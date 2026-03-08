"""
Geocoding module to convert city names and zip codes to coordinates.
"""

import time
from functools import lru_cache
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError, GeocoderUnavailable
from config.settings import GEOCODING_USER_AGENT, GEOCODING_TIMEOUT, GEOCODING_RATE_LIMIT


# Initialize the geocoder with more conservative settings
geolocator = Nominatim(user_agent=GEOCODING_USER_AGENT, timeout=GEOCODING_TIMEOUT)

# Use a class to maintain state that survives module reloads
class RateLimiter:
    """Rate limiter that maintains state across module imports."""
    def __init__(self):
        self.last_request_time = 0

    def wait(self, min_interval=GEOCODING_RATE_LIMIT):
        """Wait if necessary to respect rate limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)

        self.last_request_time = time.time()

# Create a singleton instance
_rate_limiter = RateLimiter()


def _rate_limit():
    """Ensure we don't exceed rate limits (1 request per second for Nominatim)."""
    _rate_limiter.wait()


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
    retry_delay = 2  # Start with 2 seconds for more conservative rate limiting

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
            error_str = str(e)
            # Check if this is a rate limit error (429)
            if "429" in error_str or "Too Many Requests" in error_str:
                # For rate limit errors, wait longer before retrying
                rate_limit_delay = 5 * (attempt + 1)  # 5, 10, 15 seconds
                if attempt < max_retries - 1:
                    time.sleep(rate_limit_delay)
                else:
                    raise GeocoderServiceError(
                        "Rate limit exceeded. The geocoding service limits requests to 1 per second. "
                        "Please wait a few seconds and try again."
                    )
            else:
                # For other service errors, use regular exponential backoff
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
