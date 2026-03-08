"""
Google Analytics integration for Streamlit app using Measurement Protocol
"""

import streamlit as st
import uuid
import time
import requests
from urllib.parse import urlencode


def get_client_id():
    """Get or create a client ID for this session."""
    if 'ga_client_id' not in st.session_state:
        st.session_state['ga_client_id'] = str(uuid.uuid4())
    return st.session_state['ga_client_id']


def get_session_id():
    """Get or create a session ID for this session."""
    if 'ga_session_id' not in st.session_state:
        # Use timestamp as session ID (GA4 standard practice)
        st.session_state['ga_session_id'] = str(int(time.time()))
        st.session_state['ga_session_start'] = time.time()
    return st.session_state['ga_session_id']


def get_engagement_time():
    """Calculate engagement time in milliseconds since session start."""
    session_start = st.session_state.get('ga_session_start', time.time())
    return int((time.time() - session_start) * 1000)


def inject_ga_tracking(measurement_id: str = None):
    """
    Initialize Google Analytics tracking.

    Args:
        measurement_id: Your Google Analytics Measurement ID (e.g., 'G-XXXXXXXXXX')
                       If None, will look for GA_MEASUREMENT_ID in st.secrets
    """
    # Try to get measurement ID from secrets if not provided
    if measurement_id is None:
        try:
            measurement_id = st.secrets.get("GA_MEASUREMENT_ID")
        except (FileNotFoundError, KeyError):
            return

    if not measurement_id:
        return

    # Store measurement ID in session state
    st.session_state['ga_measurement_id'] = measurement_id

    # Get or create client ID and session ID
    get_client_id()
    get_session_id()

    # Only send page_view once per session
    if 'ga_page_view_sent' not in st.session_state:
        st.session_state['ga_page_view_sent'] = True

        # Send page_view event with session_start marker
        track_event('page_view', {
            'page_title': 'Seismic Earthquake Analyzer',
            'page_location': 'streamlit_app',
            'session_start': 1  # Mark this as session start
        })


def track_event(event_name: str, event_params: dict = None):
    """
    Track a custom event in Google Analytics using Measurement Protocol.

    Args:
        event_name: Name of the event (e.g., 'search_earthquakes', 'export_data')
        event_params: Dictionary of event parameters (e.g., {'location': 'San Francisco'})
    """
    # Check if GA is configured
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

    # Extract the measurement ID without the G- prefix
    if measurement_id.startswith('G-'):
        measurement_stream_id = measurement_id[2:]
    else:
        measurement_stream_id = measurement_id

    # Get client ID and session ID
    client_id = get_client_id()
    session_id = get_session_id()
    engagement_time = get_engagement_time()

    # Add session parameters to event params
    event_params['session_id'] = session_id
    event_params['engagement_time_msec'] = engagement_time

    # Build the Measurement Protocol v2 (GA4) payload
    payload = {
        'client_id': client_id,
        'events': [{
            'name': event_name,
            'params': event_params
        }]
    }

    # GA4 Measurement Protocol endpoint
    api_secret = st.secrets.get("GA_API_SECRET", "")
    if not api_secret:
        # Fallback: try client-side tracking with components.html
        _track_event_client_side(measurement_id, event_name, event_params)
        return

    url = f"https://www.google-analytics.com/mp/collect?measurement_id={measurement_id}&api_secret={api_secret}"

    try:
        # Send the event asynchronously (don't block the UI)
        response = requests.post(url, json=payload, timeout=2)
        if response.status_code == 204:
            print(f"✓ GA event tracked: {event_name}")
        else:
            print(f"GA tracking failed: {response.status_code}")
    except Exception as e:
        print(f"GA tracking error: {e}")
        # Fallback to client-side tracking
        _track_event_client_side(measurement_id, event_name, event_params)


def _track_event_client_side(measurement_id, event_name, event_params):
    """
    Fallback: client-side tracking using gtag.js in iframe.
    This works for pageviews but events may not always fire due to iframe isolation.
    """
    import streamlit.components.v1 as components
    import json

    params_json = json.dumps(event_params)

    # Inline GA tracking - load gtag.js and send event immediately
    tracking_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script async src="https://www.googletagmanager.com/gtag/js?id={measurement_id}"></script>
        <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){{dataLayer.push(arguments);}}
            gtag('js', new Date());
            gtag('config', '{measurement_id}');

            // Send event after a delay to ensure gtag is loaded
            setTimeout(function() {{
                gtag('event', '{event_name}', {params_json});
                console.log('Client-side GA event: {event_name}');
            }}, 1500);
        </script>
    </head>
    <body></body>
    </html>
    """

    components.html(tracking_code, height=0)
