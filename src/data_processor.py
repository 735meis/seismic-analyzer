"""
Data processing and statistical analysis for earthquake data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
from math import radians, cos, sin, asin, sqrt
from config.settings import (
    MAGNITUDE_CATEGORIES,
    DEPTH_CATEGORIES,
    FEELABLE_MAGNITUDE_THRESHOLD,
    DAMAGING_MAGNITUDE_THRESHOLD,
    SWARM_MIN_EVENTS,
    SWARM_DISTANCE_KM,
    SWARM_TIME_HOURS
)
from src.utils import (
    magnitude_category,
    calculate_energy_joules,
    format_energy_display,
    format_distance
)


def process_earthquake_data(geojson_data: dict) -> pd.DataFrame:
    """
    Convert GeoJSON earthquake data to a pandas DataFrame.

    Args:
        geojson_data: GeoJSON response from USGS API

    Returns:
        pd.DataFrame: Processed earthquake data
    """
    features = geojson_data.get('features', [])

    if not features:
        return pd.DataFrame()

    records = []
    for feature in features:
        props = feature['properties']
        coords = feature['geometry']['coordinates']

        record = {
            'time': pd.to_datetime(props['time'], unit='ms'),
            'magnitude': props.get('mag'),
            'depth': coords[2] if len(coords) > 2 else None,
            'place': props.get('place', 'Unknown'),
            'latitude': coords[1],
            'longitude': coords[0],
            'type': props.get('type', 'earthquake')
        }
        records.append(record)

    df = pd.DataFrame(records)

    # Sort by time
    df = df.sort_values('time').reset_index(drop=True)

    # Add derived columns
    if not df.empty and 'magnitude' in df.columns:
        df['magnitude_category'] = df['magnitude'].apply(
            lambda x: magnitude_category(x) if pd.notna(x) else 'Unknown'
        )

    return df


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth in kilometers.

    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates

    Returns:
        float: Distance in kilometers
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of Earth in kilometers
    return c * r


def detect_earthquake_swarms(df: pd.DataFrame) -> list[dict]:
    """
    Detect earthquake swarms (clusters of events in space and time).

    Args:
        df: DataFrame with earthquake data

    Returns:
        list[dict]: List of detected swarms with details
    """
    if df.empty or len(df) < SWARM_MIN_EVENTS:
        return []

    swarms = []

    # Use a sliding window approach
    for i in range(len(df)):
        # Define time window
        start_time = df.iloc[i]['time']
        end_time = start_time + timedelta(hours=SWARM_TIME_HOURS)

        # Get events within time window
        time_mask = (df['time'] >= start_time) & (df['time'] <= end_time)
        window_df = df[time_mask]

        if len(window_df) < SWARM_MIN_EVENTS:
            continue

        # Check spatial clustering
        ref_lat = df.iloc[i]['latitude']
        ref_lon = df.iloc[i]['longitude']

        # Calculate distances from reference point
        distances = window_df.apply(
            lambda row: haversine_distance(ref_lat, ref_lon, row['latitude'], row['longitude']),
            axis=1
        )

        # Count events within distance threshold
        close_events = (distances <= SWARM_DISTANCE_KM).sum()

        if close_events >= SWARM_MIN_EVENTS:
            # Check if this is a new swarm (not overlapping with existing ones)
            is_new = True
            for swarm in swarms:
                if abs((start_time - swarm['start_time']).total_seconds()) < SWARM_TIME_HOURS * 3600:
                    is_new = False
                    break

            if is_new:
                swarms.append({
                    'start_time': start_time,
                    'end_time': end_time,
                    'count': close_events,
                    'latitude': ref_lat,
                    'longitude': ref_lon,
                    'location': df.iloc[i]['place']
                })

    return swarms


def calculate_statistics(df: pd.DataFrame, search_lat: float, search_lon: float) -> dict:
    """
    Calculate comprehensive statistics from earthquake data.

    Args:
        df: DataFrame with earthquake data
        search_lat: Search center latitude
        search_lon: Search center longitude

    Returns:
        dict: Dictionary containing various statistics
    """
    if df.empty:
        return {
            'total_count': 0,
            'message': 'No earthquakes found in the specified region and time period.'
        }

    stats = {}

    # Basic statistics
    stats['total_count'] = len(df)
    stats['date_range'] = {
        'start': df['time'].min(),
        'end': df['time'].max()
    }

    # Magnitude statistics
    mag_series = df['magnitude'].dropna()
    if not mag_series.empty:
        stats['magnitude'] = {
            'average': mag_series.mean(),
            'max': mag_series.max(),
            'min': mag_series.min(),
            'median': mag_series.median()
        }

        # Find strongest earthquake
        strongest_idx = df['magnitude'].idxmax()
        strongest = df.loc[strongest_idx]
        stats['strongest_earthquake'] = {
            'magnitude': strongest['magnitude'],
            'time': strongest['time'],
            'place': strongest['place'],
            'depth': strongest['depth'],
            'latitude': strongest['latitude'],
            'longitude': strongest['longitude']
        }

        # Magnitude distribution
        mag_dist = df['magnitude_category'].value_counts().to_dict()
        stats['magnitude_distribution'] = mag_dist

        # Calculate percentages
        total = len(df)
        stats['magnitude_distribution_pct'] = {
            cat: (count / total * 100) for cat, count in mag_dist.items()
        }

    # Temporal patterns
    days = (df['time'].max() - df['time'].min()).days + 1
    stats['temporal'] = {
        'duration_days': days,
        'avg_per_day': len(df) / max(days, 1)
    }

    # Most active day
    df['date'] = df['time'].dt.date
    daily_counts = df['date'].value_counts()
    if not daily_counts.empty:
        most_active_date = daily_counts.idxmax()
        stats['temporal']['most_active_date'] = most_active_date
        stats['temporal']['most_active_count'] = daily_counts.max()

        # Quietest day (find longest gap)
        dates = sorted(df['date'].unique())
        if len(dates) > 1:
            max_gap = 0
            gap_start = None
            for i in range(len(dates) - 1):
                gap = (dates[i + 1] - dates[i]).days
                if gap > max_gap:
                    max_gap = gap
                    gap_start = dates[i]
            if max_gap > 1:
                stats['temporal']['longest_quiet_period_days'] = max_gap
                stats['temporal']['quiet_period_start'] = gap_start

    # Depth statistics
    depth_series = df['depth'].dropna()
    if not depth_series.empty:
        stats['depth'] = {
            'average': depth_series.mean(),
            'max': depth_series.max(),
            'min': depth_series.min(),
            'median': depth_series.median()
        }

        # Depth distribution
        def categorize_depth(depth):
            for category, (min_d, max_d) in DEPTH_CATEGORIES.items():
                if min_d <= depth < max_d:
                    return category
            return "Deep"

        depth_dist = depth_series.apply(categorize_depth).value_counts().to_dict()
        stats['depth_distribution'] = depth_dist

    # Energy statistics
    if not mag_series.empty:
        energies = mag_series.apply(calculate_energy_joules)
        total_energy = energies.sum()
        max_energy = energies.max()

        stats['energy'] = {
            'total_joules': total_energy,
            'total_formatted': format_energy_display(total_energy),
            'max_joules': max_energy,
            'max_formatted': format_energy_display(max_energy)
        }

    # Interesting facts
    stats['interesting_facts'] = {}

    # Feelable earthquakes
    feelable = df[df['magnitude'] >= FEELABLE_MAGNITUDE_THRESHOLD]
    stats['interesting_facts']['feelable_count'] = len(feelable)

    # Potentially damaging
    damaging = df[df['magnitude'] >= DAMAGING_MAGNITUDE_THRESHOLD]
    stats['interesting_facts']['damaging_count'] = len(damaging)

    # Earthquake swarms
    swarms = detect_earthquake_swarms(df)
    stats['interesting_facts']['swarm_count'] = len(swarms)
    stats['interesting_facts']['swarms'] = swarms

    # Geographic spread
    distances = df.apply(
        lambda row: haversine_distance(search_lat, search_lon, row['latitude'], row['longitude']),
        axis=1
    )
    stats['interesting_facts']['nearest_km'] = distances.min()
    stats['interesting_facts']['farthest_km'] = distances.max()
    stats['interesting_facts']['nearest_formatted'] = format_distance(distances.min())
    stats['interesting_facts']['farthest_formatted'] = format_distance(distances.max())

    return stats


def aggregate_by_time_interval(df: pd.DataFrame, interval: str) -> pd.DataFrame:
    """
    Aggregate earthquake counts by time intervals.

    Args:
        df: DataFrame with earthquake data
        interval: Pandas frequency string (e.g., 'D', 'W', 'M')

    Returns:
        pd.DataFrame: Aggregated data with time bins and counts
    """
    if df.empty:
        return pd.DataFrame(columns=['time', 'count'])

    # Set time as index for resampling
    df_copy = df.copy()
    df_copy = df_copy.set_index('time')

    # Resample and count
    aggregated = df_copy.resample(interval).size().reset_index()
    aggregated.columns = ['time', 'count']

    return aggregated
