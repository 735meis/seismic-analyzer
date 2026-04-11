"""
3D Globe Visualization using PyDeck for earthquake data.
"""

import pydeck as pdk
import pandas as pd
from typing import Optional


def create_3d_globe_view(df: pd.DataFrame, center_lat: float, center_lon: float) -> pdk.Deck:
    """
    Create a 3D globe visualization of earthquakes using PyDeck.

    Args:
        df: DataFrame with earthquake data (must have 'latitude', 'longitude', 'mag', 'depth')
        center_lat: Center latitude for view
        center_lon: Center longitude for view

    Returns:
        PyDeck Deck object ready for rendering
    """
    if df.empty:
        # Return empty deck if no data
        return pdk.Deck(
            map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
            initial_view_state={
                "latitude": float(center_lat),
                "longitude": float(center_lon),
                "zoom": 2,
                "pitch": 45,
                "bearing": 0,
            },
            layers=[],
        )

    # Prepare data for visualization
    df = df.copy()

    # Convert time to string for proper serialization
    if 'time' in df.columns:
        df['time'] = df['time'].astype(str)

    # Fill NaN values to avoid serialization issues
    df['magnitude'] = df['magnitude'].fillna(0)
    df['depth'] = df['depth'].fillna(0)
    df['place'] = df['place'].fillna('Unknown')

    # Normalize magnitude for size (multiply by 100,000 for visibility)
    df['size'] = df['magnitude'] * 100000

    # Color by depth: shallow (red) to deep (blue)
    def depth_to_color(depth):
        """Convert depth to RGB color."""
        if depth < 70:  # Shallow - Red
            return [255, 87, 51, 200]
        elif depth < 300:  # Intermediate - Orange
            return [255, 167, 38, 200]
        else:  # Deep - Blue
            return [0, 149, 255, 200]

    df['color'] = df['depth'].apply(depth_to_color)

    # Convert DataFrame to list of dictionaries for proper serialization
    # Ensure values are Python native types
    data_records = []
    for _, row in df.iterrows():
        record = {
            'longitude': float(row['longitude']),
            'latitude': float(row['latitude']),
            'size': float(row['size']),
            'color': row['color'],  # Already a list of ints
            'magnitude': float(row['magnitude']),
            'depth': float(row['depth']),
            'place': str(row['place']),
            'time': str(row['time'])
        }
        data_records.append(record)

    # Create scatterplot layer - use pdk.Layer with properly serialized data
    scatterplot_layer = pdk.Layer(
        "ScatterplotLayer",
        data=data_records,
        get_position=["longitude", "latitude"],
        get_radius="size",
        get_fill_color="color",
        pickable=True,
        opacity=0.8,
        stroked=True,
        filled=True,
        radius_scale=1,
        radius_min_pixels=3,
        radius_max_pixels=50,
        line_width_min_pixels=1,
        get_line_color=[255, 255, 255, 100],
    )

    # Create arc layer for major earthquakes (M5.0+)
    major_quakes = df[df['magnitude'] >= 5.0].copy()

    arc_layers = []
    if not major_quakes.empty:
        # Create arcs from search center to major quakes
        # Ensure values are Python native types
        arc_data = []
        for _, quake in major_quakes.iterrows():
            arc_data.append({
                'start': [float(center_lon), float(center_lat)],
                'end': [float(quake['longitude']), float(quake['latitude'])],
                'magnitude': float(quake['magnitude'])
            })

        # Create arc layer - use pdk.Layer with properly serialized data
        arc_layer = pdk.Layer(
            "ArcLayer",
            data=arc_data,
            get_source_position="start",
            get_target_position="end",
            get_source_color=[102, 126, 234, 100],
            get_target_color=[240, 147, 251, 150],
            get_width="magnitude",
            width_scale=0.5,
            width_min_pixels=2,
            pickable=True,
        )
        arc_layers.append(arc_layer)

    # Tooltip configuration
    tooltip = {
        "html": "<b>Magnitude:</b> {magnitude}<br/>"
                "<b>Location:</b> {place}<br/>"
                "<b>Depth:</b> {depth} km<br/>"
                "<b>Time:</b> {time}",
        "style": {
            "backgroundColor": "rgba(26, 26, 26, 0.9)",
            "color": "white",
            "fontSize": "12px",
            "padding": "10px",
            "borderRadius": "8px",
            "fontFamily": "Inter, sans-serif"
        }
    }

    # Determine if mobile device (adjust pitch)
    # Note: This is handled by the rendering context, but we'll use standard desktop view
    pitch = 45

    # Create the deck with initial_view_state as dict for better serialization
    # Ensure all values are Python native types, not numpy types
    deck = pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        initial_view_state={
            "latitude": float(center_lat),
            "longitude": float(center_lon),
            "zoom": 4,
            "pitch": int(pitch),
            "bearing": 0,
        },
        layers=[scatterplot_layer] + arc_layers,
        tooltip=tooltip,
    )

    return deck


def create_3d_globe_mobile(df: pd.DataFrame, center_lat: float, center_lon: float) -> pdk.Deck:
    """
    Create a mobile-optimized 3D globe visualization.

    Args:
        df: DataFrame with earthquake data
        center_lat: Center latitude for view
        center_lon: Center longitude for view

    Returns:
        PyDeck Deck object optimized for mobile
    """
    # Create mobile-optimized view directly instead of modifying existing deck
    if df.empty:
        return pdk.Deck(
            map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
            initial_view_state={
                "latitude": float(center_lat),
                "longitude": float(center_lon),
                "zoom": 2,
                "pitch": 30,
                "bearing": 0,
            },
            layers=[],
        )

    # Prepare data for visualization
    df = df.copy()

    # Convert time to string for proper serialization
    if 'time' in df.columns:
        df['time'] = df['time'].astype(str)

    # Fill NaN values to avoid serialization issues
    df['magnitude'] = df['magnitude'].fillna(0)
    df['depth'] = df['depth'].fillna(0)
    df['place'] = df['place'].fillna('Unknown')

    # Normalize magnitude for size (multiply by 100,000 for visibility)
    df['size'] = df['magnitude'] * 100000

    # Color by depth: shallow (red) to deep (blue)
    def depth_to_color(depth):
        """Convert depth to RGB color."""
        if depth < 70:  # Shallow - Red
            return [255, 87, 51, 200]
        elif depth < 300:  # Intermediate - Orange
            return [255, 167, 38, 200]
        else:  # Deep - Blue
            return [0, 149, 255, 200]

    df['color'] = df['depth'].apply(depth_to_color)

    # Convert DataFrame to list of dictionaries for proper serialization
    # Ensure values are Python native types
    data_records = []
    for _, row in df.iterrows():
        record = {
            'longitude': float(row['longitude']),
            'latitude': float(row['latitude']),
            'size': float(row['size']),
            'color': row['color'],  # Already a list of ints
            'magnitude': float(row['magnitude']),
            'depth': float(row['depth']),
            'place': str(row['place']),
            'time': str(row['time'])
        }
        data_records.append(record)

    # Create scatterplot layer - use pdk.Layer with properly serialized data
    scatterplot_layer = pdk.Layer(
        "ScatterplotLayer",
        data=data_records,
        get_position=["longitude", "latitude"],
        get_radius="size",
        get_fill_color="color",
        pickable=True,
        opacity=0.8,
        stroked=True,
        filled=True,
        radius_scale=1,
        radius_min_pixels=3,
        radius_max_pixels=50,
        line_width_min_pixels=1,
        get_line_color=[255, 255, 255, 100],
    )

    # Create arc layer for major earthquakes (M5.0+)
    major_quakes = df[df['magnitude'] >= 5.0].copy()

    arc_layers = []
    if not major_quakes.empty:
        # Create arcs from search center to major quakes
        # Ensure values are Python native types
        arc_data = []
        for _, quake in major_quakes.iterrows():
            arc_data.append({
                'start': [float(center_lon), float(center_lat)],
                'end': [float(quake['longitude']), float(quake['latitude'])],
                'magnitude': float(quake['magnitude'])
            })

        # Create arc layer - use pdk.Layer with properly serialized data
        arc_layer = pdk.Layer(
            "ArcLayer",
            data=arc_data,
            get_source_position="start",
            get_target_position="end",
            get_source_color=[102, 126, 234, 100],
            get_target_color=[240, 147, 251, 150],
            get_width="magnitude",
            width_scale=0.5,
            width_min_pixels=2,
            pickable=True,
        )
        arc_layers.append(arc_layer)

    # Tooltip configuration
    tooltip = {
        "html": "<b>Magnitude:</b> {magnitude}<br/>"
                "<b>Location:</b> {place}<br/>"
                "<b>Depth:</b> {depth} km<br/>"
                "<b>Time:</b> {time}",
        "style": {
            "backgroundColor": "rgba(26, 26, 26, 0.9)",
            "color": "white",
            "fontSize": "12px",
            "padding": "10px",
            "borderRadius": "8px",
            "fontFamily": "Inter, sans-serif"
        }
    }

    # Mobile-optimized view state
    # Ensure all values are Python native types, not numpy types
    deck = pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        initial_view_state={
            "latitude": float(center_lat),
            "longitude": float(center_lon),
            "zoom": 3,
            "pitch": 30,
            "bearing": 0,
        },
        layers=[scatterplot_layer] + arc_layers,
        tooltip=tooltip,
    )

    return deck
