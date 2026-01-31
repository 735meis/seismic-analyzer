"""
Geocoding module to convert city names and zip codes to coordinates.
"""

import time
from functools import lru_cache
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError, GeocoderUnavailable
from config.settings import GEOCODING_USER_AGENT, GEOCODING_TIMEOUT, GEOCODING_RATE_LIMIT


# Initialize the geocoder
geolocator = Nominatim(user_agent=GEOCODING_USER_AGENT, timeout=GEOCODING_TIMEOUT)

# Track last request time for rate limiting
_last_request_time = 0


def _rate_limit():
    """Ensure we don't exceed rate limits (1 request per second for Nominatim)."""
    global _last_request_time
    current_time = time.time()
    time_since_last = current_time - _last_request_time

    if time_since_last < GEOCODING_RATE_LIMIT:
        time.sleep(GEOCODING_RATE_LIMIT - time_since_last)

    _last_request_time = time.time()


@lru_cache(maxsize=128)
def geocode_location(location: str, is_zipcode: bool = False) -> tuple[float, float]:
    """
    Convert a city name or zip code to latitude and longitude coordinates.

    Args:
        location: City name or zip code
        is_zipcode: Whether the location is a zip code

    Returns:
        tuple[float, float]: (latitude, longitude)

    Raises:
        ValueError: If location cannot be geocoded
        GeocoderTimedOut: If the geocoding request times out
        GeocoderServiceError: If there's a service error
    """
    if not location or not location.strip():
        raise ValueError("Location cannot be empty")

    # Prepare the query
    query = location.strip()
    if is_zipcode:
        query = f"{query}, USA"

    max_retries = 3
    retry_delay = 1  # Start with 1 second

    for attempt in range(max_retries):
        try:
            _rate_limit()

            result = geolocator.geocode(query)

            if result is None:
                raise ValueError(
                    f"Could not find coordinates for '{location}'. "
                    "Please check the spelling or try a different location."
                )

            return (result.latitude, result.longitude)

        except GeocoderTimedOut:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                raise GeocoderTimedOut(
                    f"Geocoding timed out after {max_retries} attempts. "
                    "Please try again later."
                )

        except (GeocoderServiceError, GeocoderUnavailable) as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise GeocoderServiceError(
                    f"Geocoding service error: {str(e)}. "
                    "The service may be temporarily unavailable. Please try again later."
                )

        except Exception as e:
            raise ValueError(f"Unexpected error during geocoding: {str(e)}")


def get_location_name(latitude: float, longitude: float) -> str:
    """
    Reverse geocode coordinates to get a location name.

    Args:
        latitude: Latitude
        longitude: Longitude

    Returns:
        str: Location name or formatted coordinates if reverse geocoding fails
    """
    try:
        _rate_limit()
        location = geolocator.reverse((latitude, longitude), exactly_one=True)
        if location:
            return location.address
    except Exception:
        pass

    return f"{latitude:.4f}, {longitude:.4f}"
