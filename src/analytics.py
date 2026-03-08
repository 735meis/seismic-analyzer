"""
Google Analytics integration for Streamlit app
"""

import streamlit as st


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

    # Store measurement ID in session state for event tracking
    st.session_state['ga_measurement_id'] = measurement_id

    # Google Analytics 4 tracking code - inject into page, not iframe
    ga_code = f"""
    <script async src="https://www.googletagmanager.com/gtag/js?id={measurement_id}"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag('js', new Date());
        gtag('config', '{measurement_id}');
    </script>
    """

    # Use markdown with unsafe HTML to inject directly into page
    st.markdown(ga_code, unsafe_allow_html=True)


def track_event(event_name: str, event_params: dict = None):
    """
    Track a custom event in Google Analytics.

    Args:
        event_name: Name of the event (e.g., 'search_earthquakes', 'export_data')
        event_params: Dictionary of event parameters (e.g., {'location': 'San Francisco'})
    """
    # Check if GA is configured via session state or secrets
    measurement_id = st.session_state.get('ga_measurement_id')
    if not measurement_id:
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
        // Wait a bit for gtag to be available, then track event
        (function() {{
            var attempts = 0;
            var maxAttempts = 20;
            var checkGtag = setInterval(function() {{
                attempts++;
                if (typeof gtag !== 'undefined') {{
                    gtag('event', '{event_name}', {params_str});
                    clearInterval(checkGtag);
                }} else if (attempts >= maxAttempts) {{
                    clearInterval(checkGtag);
                    console.warn('GA gtag not available after ' + maxAttempts + ' attempts');
                }}
            }}, 100);
        }})();
    </script>
    """

    # Inject the event tracking code into the page
    st.markdown(event_code, unsafe_allow_html=True)
