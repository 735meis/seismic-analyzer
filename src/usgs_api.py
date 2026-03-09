"""
USGS API client for fetching earthquake data.
"""

import time
import requests
from datetime import datetime
from typing import Optional
from config.settings import (
    USGS_API_BASE_URL,
    API_REQUEST_TIMEOUT,
    API_MAX_RETRIES,
    API_RESULT_LIMIT,
    DEFAULT_SEARCH_RADIUS_KM
)
from src.utils import format_date_for_api


class USGSAPIError(Exception):
    """Custom exception for USGS API errors."""
    pass


def fetch_earthquakes(
    latitude: float,
    longitude: float,
    start_date: datetime,
    end_date: datetime,
    min_magnitude: Optional[float] = None,
    radius_km: float = DEFAULT_SEARCH_RADIUS_KM
) -> dict:
    """
    Fetch earthquake data from the USGS API.

    Args:
        latitude: Center latitude for search
        longitude: Center longitude for search
        start_date: Start datetime for search range
        end_date: End datetime for search range
        min_magnitude: Minimum magnitude filter (optional)
        radius_km: Search radius in kilometers

    Returns:
        dict: GeoJSON response from USGS API

    Raises:
        USGSAPIError: If API request fails
        ValueError: If parameters are invalid
    """
    # Validate parameters
    if not -90 <= latitude <= 90:
        raise ValueError(f"Invalid latitude: {latitude}. Must be between -90 and 90.")

    if not -180 <= longitude <= 180:
        raise ValueError(f"Invalid longitude: {longitude}. Must be between -180 and 180.")

    if start_date >= end_date:
        raise ValueError("Start date must be before end date.")

    if end_date.date() > datetime.now().date():
        raise ValueError("End date cannot be in the future.")

    if radius_km <= 0:
        raise ValueError(f"Invalid radius: {radius_km}. Must be positive.")

    if min_magnitude is not None and min_magnitude < 0:
        raise ValueError(f"Invalid minimum magnitude: {min_magnitude}. Must be non-negative.")

    # Build query parameters
    params = {
        'format': 'geojson',
        'latitude': latitude,
        'longitude': longitude,
        'maxradiuskm': radius_km,
        'starttime': format_date_for_api(start_date),
        'endtime': format_date_for_api(end_date),
        'orderby': 'time'
    }

    if min_magnitude is not None:
        params['minmagnitude'] = min_magnitude

    # Implement retry logic with exponential backoff
    retry_delay = 1
    last_exception = None

    for attempt in range(API_MAX_RETRIES):
        try:
            response = requests.get(
                USGS_API_BASE_URL,
                params=params,
                timeout=API_REQUEST_TIMEOUT
            )

            # Handle HTTP errors
            if response.status_code == 400:
                error_message = "Invalid request parameters."
                try:
                    error_detail = response.json().get('detail', '')
                    if error_detail:
                        error_message += f" Details: {error_detail}"
                except Exception:
                    pass
                raise USGSAPIError(error_message)

            elif response.status_code == 503:
                raise USGSAPIError(
                    "USGS service is temporarily unavailable. Please try again later."
                )

            elif response.status_code != 200:
                raise USGSAPIError(
                    f"USGS API returned status code {response.status_code}: {response.text}"
                )

            # Parse response
            data = response.json()

            # Check for result limit warning
            feature_count = len(data.get('features', []))
            if feature_count >= API_RESULT_LIMIT:
                raise USGSAPIError(
                    f"Result limit reached ({API_RESULT_LIMIT} earthquakes). "
                    "Please narrow your search by reducing the time range, "
                    "increasing minimum magnitude, or decreasing search radius."
                )

            return data

        except requests.exceptions.Timeout:
            last_exception = USGSAPIError(
                f"Request timed out after {API_REQUEST_TIMEOUT} seconds."
            )
            if attempt < API_MAX_RETRIES - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise last_exception

        except requests.exceptions.ConnectionError:
            last_exception = USGSAPIError(
                "Failed to connect to USGS API. Please check your internet connection."
            )
            if attempt < API_MAX_RETRIES - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise last_exception

        except requests.exceptions.RequestException as e:
            raise USGSAPIError(f"Request failed: {str(e)}")

        except USGSAPIError:
            # Don't retry on known API errors
            raise

        except Exception as e:
            raise USGSAPIError(f"Unexpected error: {str(e)}")

    # If we get here, all retries failed
    if last_exception:
        raise last_exception
    else:
        raise USGSAPIError("Failed to fetch earthquake data after multiple attempts.")


def get_earthquake_count(
    latitude: float,
    longitude: float,
    start_date: datetime,
    end_date: datetime,
    min_magnitude: Optional[float] = None,
    radius_km: float = DEFAULT_SEARCH_RADIUS_KM
) -> int:
    """
    Get the count of earthquakes without fetching full data.

    Args:
        latitude: Center latitude for search
        longitude: Center longitude for search
        start_date: Start datetime for search range
        end_date: End datetime for search range
        min_magnitude: Minimum magnitude filter (optional)
        radius_km: Search radius in kilometers

    Returns:
        int: Number of earthquakes matching criteria
    """
    data = fetch_earthquakes(
        latitude, longitude, start_date, end_date, min_magnitude, radius_km
    )
    return len(data.get('features', []))


def fetch_earthquakes_global(
    start_datetime: datetime,
    end_datetime: datetime,
    min_magnitude: float = 4.5
) -> dict:
    """
    Fetch global earthquake data from the USGS API without location constraints.

    Args:
        start_datetime: Start datetime for search range
        end_datetime: End datetime for search range
        min_magnitude: Minimum magnitude filter

    Returns:
        dict: GeoJSON response from USGS API

    Raises:
        USGSAPIError: If API request fails
    """
    # Build query parameters
    params = {
        'format': 'geojson',
        'starttime': format_date_for_api(start_datetime),
        'endtime': format_date_for_api(end_datetime),
        'minmagnitude': min_magnitude,
        'orderby': 'magnitude',
        'limit': 100
    }

    retry_delay = 1
    last_exception = None

    for attempt in range(API_MAX_RETRIES):
        try:
            response = requests.get(
                USGS_API_BASE_URL,
                params=params,
                timeout=API_REQUEST_TIMEOUT
            )

            if response.status_code == 400:
                error_message = "Invalid request parameters."
                try:
                    error_detail = response.json().get('detail', '')
                    if error_detail:
                        error_message += f" Details: {error_detail}"
                except Exception:
                    pass
                raise USGSAPIError(error_message)

            elif response.status_code == 503:
                raise USGSAPIError(
                    "USGS service is temporarily unavailable. Please try again later."
                )

            elif response.status_code != 200:
                raise USGSAPIError(
                    f"USGS API returned status code {response.status_code}: {response.text}"
                )

            return response.json()

        except requests.exceptions.Timeout:
            last_exception = USGSAPIError(
                f"Request timed out after {API_REQUEST_TIMEOUT} seconds."
            )
            if attempt < API_MAX_RETRIES - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise last_exception

        except requests.exceptions.ConnectionError:
            last_exception = USGSAPIError(
                "Failed to connect to USGS API. Please check your internet connection."
            )
            if attempt < API_MAX_RETRIES - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise last_exception

        except requests.exceptions.RequestException as e:
            raise USGSAPIError(f"Request failed: {str(e)}")

        except USGSAPIError:
            raise

        except Exception as e:
            raise USGSAPIError(f"Unexpected error: {str(e)}")

    if last_exception:
        raise last_exception
    else:
        raise USGSAPIError("Failed to fetch earthquake data after multiple attempts.")


def fetch_dyfi_data(event_id: str) -> Optional[dict]:
    """
    Fetch DYFI (Did You Feel It?) data for a specific earthquake event.

    Args:
        event_id: USGS event ID

    Returns:
        dict: DYFI data including CDI, felt reports, etc., or None if not available

    Raises:
        USGSAPIError: If API request fails
    """
    try:
        # Fetch detailed event information
        url = f"https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/{event_id}.geojson"
        response = requests.get(url, timeout=API_REQUEST_TIMEOUT)

        if response.status_code == 404:
            # Event not found or no detailed data available
            return None

        if response.status_code != 200:
            return None

        data = response.json()
        properties = data.get('properties', {})

        # Extract DYFI data
        dyfi_data = {
            'cdi': properties.get('cdi'),  # Community Decimal Intensity
            'felt': properties.get('felt'),  # Number of felt reports
            'mmi': properties.get('mmi'),  # Modified Mercalli Intensity
            'alert': properties.get('alert'),  # Alert level
            'sig': properties.get('sig'),  # Significance
            'tsunami': properties.get('tsunami'),  # Tsunami flag
        }

        # Only return if there's actual DYFI data
        if dyfi_data['cdi'] is not None or dyfi_data['felt'] is not None:
            return dyfi_data

        return None

    except Exception as e:
        # Silently fail for DYFI data - it's supplementary information
        return None
