"""
Google Analytics integration for Streamlit app
"""

import streamlit as st
import streamlit.components.v1 as components


def inject_ga_tracking(measurement_id: str = None):
    """
    Inject Google Analytics tracking code into the Streamlit app.

    Args:
        measurement_id: Your Google Analytics Measurement ID (e.g., 'G-XXXXXXXXXX')
                       If None, will look for GA_MEASUREMENT_ID in st.secrets
    """
    # Try to get measurement ID from secrets if not provided
    if measurement_id is None:
        try:
            measurement_id = st.secrets.get("GA_MEASUREMENT_ID")
        except (FileNotFoundError, KeyError):
            # No GA configured, skip tracking
            return

    if not measurement_id:
        return

    # Google Analytics 4 tracking code
    ga_code = f"""
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={measurement_id}"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag('js', new Date());
        gtag('config', '{measurement_id}');
    </script>
    """

    # Inject the tracking code
    components.html(ga_code, height=0)


def track_event(event_name: str, event_params: dict = None):
    """
    Track a custom event in Google Analytics.

    Args:
        event_name: Name of the event (e.g., 'search_earthquakes', 'export_data')
        event_params: Dictionary of event parameters (e.g., {'location': 'San Francisco'})
    """
    # Try to get measurement ID to check if GA is configured
    try:
        measurement_id = st.secrets.get("GA_MEASUREMENT_ID")
    except (FileNotFoundError, KeyError):
        return

    if not measurement_id:
        return

    if event_params is None:
        event_params = {}

    # Convert event params to JavaScript object notation
    params_str = "{"
    for key, value in event_params.items():
        # Escape single quotes in string values
        if isinstance(value, str):
            value = value.replace("'", "\\'")
            params_str += f"'{key}': '{value}', "
        else:
            params_str += f"'{key}': {value}, "
    params_str += "}"

    # Create the gtag event tracking script
    event_code = f"""
    <script>
        if (typeof gtag !== 'undefined') {{
            gtag('event', '{event_name}', {params_str});
        }}
    </script>
    """

    # Inject the event tracking code
    components.html(event_code, height=0)
