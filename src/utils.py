"""
Utility functions for time granularity, date formatting, and calculations.
"""

from datetime import datetime, timedelta
from config.settings import SEISMIC_ENERGY_CONSTANT_A, SEISMIC_ENERGY_CONSTANT_B, MAGNITUDE_CATEGORIES


def determine_time_granularity(start_date: datetime, end_date: datetime) -> tuple[str, str]:
    """
    Determine the appropriate time granularity for aggregation based on date range.

    Args:
        start_date: Start datetime
        end_date: End datetime

    Returns:
        tuple[str, str]: (pandas frequency code, human-readable label)
    """
    delta = end_date - start_date
    days = delta.days

    if days < 1:
        return ('h', 'Hourly')
    elif days <= 7:
        return ('6h', 'Every 6 Hours')
    elif days <= 31:
        return ('D', 'Daily')
    elif days <= 93:  # ~3 months
        return ('W', 'Weekly')
    elif days <= 365:  # 1 year
        return ('W', 'Weekly')
    elif days <= 1825:  # 5 years
        return ('M', 'Monthly')
    else:
        return ('Y', 'Yearly')


def format_date_for_api(date: datetime) -> str:
    """
    Format a datetime object to ISO8601 format for USGS API.

    Args:
        date: datetime object

    Returns:
        str: ISO8601 formatted date string
    """
    return date.strftime('%Y-%m-%dT%H:%M:%S')


def calculate_energy_joules(magnitude: float) -> float:
    """
    Calculate seismic energy released in joules using the standard formula.
    E = 10^(1.5*M + 4.8)

    Args:
        magnitude: Earthquake magnitude

    Returns:
        float: Energy in joules
    """
    return 10 ** (SEISMIC_ENERGY_CONSTANT_A * magnitude + SEISMIC_ENERGY_CONSTANT_B)


def energy_to_tnt_tons(energy_joules: float) -> float:
    """
    Convert energy in joules to TNT equivalent in tons.
    1 ton of TNT = 4.184 × 10^9 joules

    Args:
        energy_joules: Energy in joules

    Returns:
        float: Energy in tons of TNT
    """
    return energy_joules / 4.184e9


def magnitude_category(magnitude: float) -> str:
    """
    Categorize earthquake magnitude.

    Args:
        magnitude: Earthquake magnitude

    Returns:
        str: Category name (Micro, Minor, Light, Moderate, Strong, Major, Great)
    """
    for category, (min_mag, max_mag) in MAGNITUDE_CATEGORIES.items():
        if min_mag <= magnitude < max_mag:
            return category
    return "Great"  # For anything >= 8


def format_energy_display(energy_joules: float) -> str:
    """
    Format energy for human-readable display.

    Args:
        energy_joules: Energy in joules

    Returns:
        str: Formatted energy string
    """
    tnt_tons = energy_to_tnt_tons(energy_joules)

    if tnt_tons < 1:
        return f"{tnt_tons * 1000:.1f} kg TNT"
    elif tnt_tons < 1000:
        return f"{tnt_tons:.1f} tons TNT"
    else:
        return f"{tnt_tons / 1000:.2f} kilotons TNT"


def format_distance(distance_km: float) -> str:
    """
    Format distance for display.

    Args:
        distance_km: Distance in kilometers

    Returns:
        str: Formatted distance string
    """
    if distance_km < 1:
        return f"{distance_km * 1000:.0f} m"
    else:
        return f"{distance_km:.1f} km"
