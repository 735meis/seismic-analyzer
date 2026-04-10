"""
Gamification System - Points, Badges, and Achievements using browser LocalStorage.
"""

import streamlit as st
import streamlit.components.v1 as components
from typing import Dict, List, Tuple
from datetime import datetime


# Points structure
POINTS_CONFIG = {
    'search': 10,
    'discover_major': 50,  # M7.0+
    'export': 5,
    'share': 15,
    'daily_login': 25,
    'trivia_correct': 20,
    'trivia_attempt': 5
}

# Badge definitions
BADGES = {
    'seismologist': {
        'name': '🔬 Seismologist',
        'description': 'Complete 50+ searches',
        'requirement': lambda stats: stats.get('searches', 0) >= 50
    },
    'early_detector': {
        'name': '⚡ Early Detector',
        'description': 'Found quake within 1 hour',
        'requirement': lambda stats: stats.get('early_detections', 0) >= 1
    },
    'data_enthusiast': {
        'name': '📊 Data Enthusiast',
        'description': 'Export data 10+ times',
        'requirement': lambda stats: stats.get('exports', 0) >= 10
    },
    'globe_trotter': {
        'name': '🌍 Globe Trotter',
        'description': 'Search 5 continents',
        'requirement': lambda stats: stats.get('continents', 0) >= 5
    },
    'major_hunter': {
        'name': '🎯 Major Hunter',
        'description': 'Discover 5 major earthquakes (M7.0+)',
        'requirement': lambda stats: stats.get('major_quakes', 0) >= 5
    },
    'knowledge_seeker': {
        'name': '🧠 Knowledge Seeker',
        'description': 'Answer 10 trivia questions correctly',
        'requirement': lambda stats: stats.get('trivia_correct', 0) >= 10
    }
}

# Milestones
MILESTONES = [100, 250, 500, 1000, 2500, 5000]


def initialize_gamification():
    """
    Initialize gamification system with LocalStorage integration.
    Call this at the start of the app.
    """
    # HTML/JS to initialize and load stats from LocalStorage
    init_html = """
    <script>
    // Initialize or load user stats
    function initializeStats() {
        let stats = localStorage.getItem('seismic_user_stats');
        if (!stats) {
            stats = {
                points: 0,
                searches: 0,
                exports: 0,
                shares: 0,
                major_quakes: 0,
                early_detections: 0,
                continents: 0,
                trivia_correct: 0,
                trivia_attempts: 0,
                badges: [],
                last_login: new Date().toISOString().split('T')[0]
            };
            localStorage.setItem('seismic_user_stats', JSON.stringify(stats));
        } else {
            stats = JSON.parse(stats);

            // Check for daily login bonus
            const today = new Date().toISOString().split('T')[0];
            if (stats.last_login !== today) {
                stats.points += 25;
                stats.last_login = today;
                localStorage.setItem('seismic_user_stats', JSON.stringify(stats));

                // Show toast notification
                window.parent.postMessage({
                    type: 'daily_login',
                    points: 25
                }, '*');
            }
        }

        // Send stats to Streamlit
        window.parent.postMessage({
            type: 'load_stats',
            data: stats
        }, '*');
    }

    // Function to update stats
    function updateStats(action, value) {
        let stats = JSON.parse(localStorage.getItem('seismic_user_stats'));

        if (action === 'add_points') {
            stats.points += value;
        } else if (action === 'increment') {
            stats[value] = (stats[value] || 0) + 1;
        } else if (action === 'add_badge') {
            if (!stats.badges.includes(value)) {
                stats.badges.push(value);
            }
        }

        localStorage.setItem('seismic_user_stats', JSON.stringify(stats));

        // Send updated stats back
        window.parent.postMessage({
            type: 'update_stats',
            data: stats
        }, '*');
    }

    // Listen for commands from Streamlit
    window.addEventListener('message', function(event) {
        if (event.data.type === 'update_gamification') {
            updateStats(event.data.action, event.data.value);
        } else if (event.data.type === 'get_stats') {
            initializeStats();
        }
    });

    // Initialize on load
    initializeStats();
    </script>
    """

    components.html(init_html, height=0)

    # Initialize session state for stats if not present
    if 'user_stats' not in st.session_state:
        st.session_state.user_stats = {
            'points': 0,
            'searches': 0,
            'exports': 0,
            'shares': 0,
            'major_quakes': 0,
            'early_detections': 0,
            'continents': 0,
            'trivia_correct': 0,
            'trivia_attempts': 0,
            'badges': []
        }


def award_points(action: str, custom_amount: int = None):
    """
    Award points for an action.

    Args:
        action: Action type (e.g., 'search', 'export', 'share')
        custom_amount: Custom point amount (overrides config)
    """
    amount = custom_amount if custom_amount else POINTS_CONFIG.get(action, 0)

    if amount > 0:
        # Update session state
        st.session_state.user_stats['points'] = st.session_state.user_stats.get('points', 0) + amount

        # Show toast notification
        st.toast(f"⭐ +{amount} points!", icon="⭐")

        # Update LocalStorage via JS
        update_html = f"""
        <script>
        window.parent.postMessage({{
            type: 'update_gamification',
            action: 'add_points',
            value: {amount}
        }}, '*');
        </script>
        """
        components.html(update_html, height=0)


def increment_stat(stat_name: str):
    """
    Increment a statistic (searches, exports, etc.).

    Args:
        stat_name: Name of the stat to increment
    """
    st.session_state.user_stats[stat_name] = st.session_state.user_stats.get(stat_name, 0) + 1

    # Update LocalStorage
    update_html = f"""
    <script>
    window.parent.postMessage({{
        type: 'update_gamification',
        action: 'increment',
        value: '{stat_name}'
    }}, '*');
    </script>
    """
    components.html(update_html, height=0)


def check_badges() -> List[str]:
    """
    Check which badges have been unlocked.

    Returns:
        List of newly unlocked badge IDs
    """
    stats = st.session_state.user_stats
    current_badges = set(stats.get('badges', []))
    new_badges = []

    for badge_id, badge_info in BADGES.items():
        if badge_id not in current_badges and badge_info['requirement'](stats):
            new_badges.append(badge_id)
            stats['badges'].append(badge_id)

            # Show celebration
            st.balloons()
            st.toast(f"🎉 Badge Unlocked: {badge_info['name']}", icon="🎉")

            # Update LocalStorage
            update_html = f"""
            <script>
            window.parent.postMessage({{
                type: 'update_gamification',
                action: 'add_badge',
                value: '{badge_id}'
            }}, '*');
            </script>
            """
            components.html(update_html, height=0)

    return new_badges


def render_gamification_sidebar():
    """
    Render gamification UI in the sidebar.
    """
    stats = st.session_state.user_stats
    points = stats.get('points', 0)
    badges = stats.get('badges', [])

    # Points display with gradient
    st.sidebar.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 1rem;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        ">
            <div style="font-size: 1.5rem; font-weight: 700;">⭐ {points}</div>
            <div style="font-size: 0.875rem; opacity: 0.9;">Points</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Progress to next milestone
    next_milestone = None
    for milestone in MILESTONES:
        if points < milestone:
            next_milestone = milestone
            break

    if next_milestone:
        progress = (points / next_milestone) * 100
        remaining = next_milestone - points

        st.sidebar.markdown("**Next Milestone**")
        st.sidebar.progress(progress / 100)
        st.sidebar.markdown(
            f'<div style="text-align: center; font-size: 0.875rem; color: #a3a3a3; margin-bottom: 1rem;">'
            f'{remaining} points to {next_milestone}'
            f'</div>',
            unsafe_allow_html=True
        )

    # Badges section (expandable)
    with st.sidebar.expander("🏆 Badges", expanded=False):
        if badges:
            for badge_id in badges:
                badge = BADGES[badge_id]
                st.markdown(
                    f"""
                    <div class="glass-card" style="padding: 0.75rem; margin: 0.5rem 0;">
                        <div style="font-size: 1.125rem; font-weight: 600;">{badge['name']}</div>
                        <div style="font-size: 0.8125rem; color: #a3a3a3;">{badge['description']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.markdown("*Complete challenges to earn badges!*")

        # Show locked badges
        st.markdown("**Available Badges**")
        for badge_id, badge in BADGES.items():
            if badge_id not in badges:
                st.markdown(
                    f"""
                    <div style="padding: 0.5rem; margin: 0.25rem 0; opacity: 0.5;">
                        <div style="font-size: 0.9375rem;">🔒 {badge['name']}</div>
                        <div style="font-size: 0.75rem; color: #a3a3a3;">{badge['description']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )


def record_search(has_major_quake: bool = False):
    """
    Record a search action and award points.

    Args:
        has_major_quake: Whether search found a major (M7.0+) quake
    """
    increment_stat('searches')
    award_points('search')

    if has_major_quake:
        increment_stat('major_quakes')
        award_points('discover_major')

    check_badges()


def record_export():
    """Record an export action."""
    increment_stat('exports')
    award_points('export')
    check_badges()


def record_share():
    """Record a share action."""
    increment_stat('shares')
    award_points('share')
    check_badges()
