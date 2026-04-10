"""
Social Activity Feed - Real-time earthquake activity and simulated user searches.
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import random
from typing import List, Dict


# Sample locations for simulated user searches
SAMPLE_LOCATIONS = [
    "Tokyo, Japan", "Los Angeles, USA", "Mexico City, Mexico",
    "Santiago, Chile", "Istanbul, Turkey", "San Francisco, USA",
    "Jakarta, Indonesia", "Manila, Philippines", "Lima, Peru",
    "Athens, Greece", "Tehran, Iran", "Kathmandu, Nepal"
]


@st.cache_data(ttl=30)  # Cache for 30 seconds
def fetch_global_activity() -> List[Dict]:
    """
    Fetch recent global earthquake activity and combine with simulated user searches.

    Returns:
        List of activity items with type, message, timestamp
    """
    activities = []

    try:
        # Fetch recent significant earthquakes from USGS (M4.5+ in last hour)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)

        params = {
            'format': 'geojson',
            'starttime': start_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'endtime': end_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'minmagnitude': 4.5,
            'orderby': 'time'
        }

        response = requests.get(
            'https://earthquake.usgs.gov/fdsnws/event/1/query',
            params=params,
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            for feature in data.get('features', [])[:5]:  # Limit to 5 most recent
                props = feature['properties']
                mag = props.get('mag', 0)
                place = props.get('place', 'Unknown location')
                time_ms = props.get('time', 0)

                # Calculate time ago
                event_time = datetime.fromtimestamp(time_ms / 1000)
                time_diff = datetime.utcnow() - event_time
                minutes_ago = int(time_diff.total_seconds() / 60)

                if minutes_ago < 1:
                    time_ago = "Just now"
                elif minutes_ago < 60:
                    time_ago = f"{minutes_ago} min ago"
                else:
                    hours_ago = int(minutes_ago / 60)
                    time_ago = f"{hours_ago} hr ago"

                activities.append({
                    'type': 'earthquake',
                    'icon': '🌍' if mag < 5.0 else '⚡',
                    'message': f"M {mag:.1f} - {place}",
                    'time_ago': time_ago,
                    'timestamp': event_time
                })

    except Exception as e:
        # Fallback: If API fails, show cached or placeholder data
        pass

    # Add simulated user searches (for engagement)
    num_searches = random.randint(2, 4)
    for _ in range(num_searches):
        location = random.choice(SAMPLE_LOCATIONS)
        minutes_ago = random.randint(1, 30)

        activities.append({
            'type': 'search',
            'icon': '🔍',
            'message': f"User searched {location}",
            'time_ago': f"{minutes_ago} min ago",
            'timestamp': datetime.utcnow() - timedelta(minutes=minutes_ago)
        })

    # Sort by timestamp (most recent first)
    activities.sort(key=lambda x: x['timestamp'], reverse=True)

    # Return top 10 activities
    return activities[:10]


def render_activity_feed():
    """
    Render the live activity feed in the sidebar.
    """
    st.sidebar.markdown("### 🌐 Live Activity")

    activities = fetch_global_activity()

    if not activities:
        st.sidebar.markdown(
            '<div class="activity-item glass-card" style="text-align: center; color: #a3a3a3;">'
            'No recent activity'
            '</div>',
            unsafe_allow_html=True
        )
        return

    for activity in activities:
        icon = activity['icon']
        message = activity['message']
        time_ago = activity['time_ago']

        # Different styling for earthquakes vs searches
        if activity['type'] == 'earthquake':
            bg_color = "rgba(255, 87, 51, 0.1)"
            border_color = "rgba(255, 87, 51, 0.3)"
        else:
            bg_color = "rgba(102, 126, 234, 0.1)"
            border_color = "rgba(102, 126, 234, 0.3)"

        activity_html = f"""
        <div class="activity-item glass-card" style="
            background: {bg_color};
            border-left: 3px solid {border_color};
            padding: 0.75rem;
            margin: 0.5rem 0;
            border-radius: 8px;
            font-size: 0.875rem;
        ">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="font-size: 1.25rem;">{icon}</span>
                <div style="flex: 1;">
                    <div style="font-weight: 500;">{message}</div>
                    <div style="font-size: 0.75rem; color: #a3a3a3; margin-top: 0.25rem;">
                        {time_ago}
                    </div>
                </div>
            </div>
        </div>
        """

        st.sidebar.markdown(activity_html, unsafe_allow_html=True)

    # Auto-refresh hint
    st.sidebar.markdown(
        '<div style="text-align: center; font-size: 0.75rem; color: #a3a3a3; margin-top: 0.5rem;">'
        '⟳ Updates every 30 seconds'
        '</div>',
        unsafe_allow_html=True
    )
