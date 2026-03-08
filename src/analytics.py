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

    # Store measurement ID in session state for event tracking
    st.session_state['ga_measurement_id'] = measurement_id

    # Only inject once per session to avoid multiple instances
    if 'ga_injected' in st.session_state:
        return
    st.session_state['ga_injected'] = True

    # Google Analytics 4 tracking code - inject using components.html for proper script execution
    ga_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script async src="https://www.googletagmanager.com/gtag/js?id={measurement_id}"></script>
        <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){{dataLayer.push(arguments);}}
            gtag('js', new Date());
            gtag('config', '{measurement_id}');

            // Make gtag globally accessible
            window.gtag = gtag;

            // Try to make it available to parent window
            try {{
                if (window.parent && window.parent !== window) {{
                    window.parent.dataLayer = window.dataLayer;
                    window.parent.gtag = gtag;
                }}
            }} catch(e) {{
                console.log('Could not access parent window:', e);
            }}

            // Send a test event to verify GA is working
            gtag('event', 'ga_initialized', {{
                'event_category': 'system',
                'event_label': 'GA Tracking Active'
            }});
        </script>
    </head>
    <body style="margin:0;padding:0;"></body>
    </html>
    """

    # Use components.html with a minimal height to ensure it renders and executes
    components.html(ga_code, height=1)


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
    import json
    params_str = "{"
    for key, value in event_params.items():
        # Escape single quotes in string values
        if isinstance(value, str):
            value = value.replace("'", "\\'")
            params_str += f"'{key}': '{value}', "
        elif isinstance(value, bool):
            # Convert Python True/False to JavaScript true/false
            params_str += f"'{key}': {str(value).lower()}, "
        elif value is None:
            params_str += f"'{key}': null, "
        else:
            # Numbers and other types
            params_str += f"'{key}': {value}, "
    params_str += "}"

    # Create the gtag event tracking script with proper HTML structure
    event_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script>
            // Wait a bit for gtag to be available, then track event
            (function() {{
                var attempts = 0;
                var maxAttempts = 30;
                var checkGtag = setInterval(function() {{
                    attempts++;
                    // Check in current window and parent window
                    var gtagFunc = window.gtag || (window.parent && window.parent !== window && window.parent.gtag);
                    if (typeof gtagFunc !== 'undefined') {{
                        gtagFunc('event', '{event_name}', {params_str});
                        clearInterval(checkGtag);
                        console.log('GA event tracked: {event_name}');
                    }} else if (attempts >= maxAttempts) {{
                        clearInterval(checkGtag);
                        console.warn('GA gtag not available after ' + maxAttempts + ' attempts');
                    }}
                }}, 100);
            }})();
        </script>
    </head>
    <body style="margin:0;padding:0;"></body>
    </html>
    """

    # Use components.html with minimal height to ensure it renders and executes
    components.html(event_code, height=1)
