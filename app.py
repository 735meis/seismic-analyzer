"""
Seismic Earthquake Analyzer - Main Streamlit Application
"""

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

from src.geocoding import geocode_location
from src.usgs_api import fetch_earthquakes, USGSAPIError
from src.data_processor import (
    process_earthquake_data,
    calculate_statistics,
    aggregate_by_time_interval
)
from src.visualizations import (
    create_timeline_chart,
    create_occurrence_bar_chart,
    create_magnitude_distribution_chart,
    create_depth_distribution_chart,
    create_magnitude_vs_depth_scatter,
    create_earthquake_map,
    create_dyfi_visualization,
    get_intensity_description
)
from src.utils import determine_time_granularity
from src.analytics import inject_ga_tracking, track_event
from config.settings import DEFAULT_SEARCH_RADIUS_KM

# New UX features
from src.globe_visualization import create_3d_globe_view
from src.social_feed import render_activity_feed
from src.gamification import (
    initialize_gamification,
    render_gamification_sidebar,
    record_search,
    record_export,
    record_share
)
from src.social_sharing import create_share_buttons
from src.storytelling import render_storytelling_sections
from src.trivia import render_trivia_sidebar


# Page configuration
st.set_page_config(
    page_title="Seismic Earthquake Analyzer",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Cache geocoding results
@st.cache_data(ttl=3600)
def cached_geocode(location: str, is_zipcode: bool):
    """Cache geocoding results to avoid repeated API calls."""
    return geocode_location(location, is_zipcode)


# Cache API responses
@st.cache_data(ttl=3600)
def cached_fetch_earthquakes(lat, lon, start_date, end_date, min_mag, radius):
    """Cache earthquake data fetches."""
    return fetch_earthquakes(lat, lon, start_date, end_date, min_mag, radius)


# Cache today's significant earthquakes (global)
@st.cache_data(ttl=3600)
def fetch_todays_significant_earthquakes():
    """Fetch today's significant earthquakes globally from USGS."""
    try:
        current_time = datetime.now()
        start_time = datetime.combine(current_time.date(), datetime.min.time())

        # Fetch global earthquakes with min magnitude 4.5 for today
        from src.usgs_api import fetch_earthquakes_global
        geojson_data = fetch_earthquakes_global(
            start_datetime=start_time,
            end_datetime=current_time,
            min_magnitude=4.5
        )

        df = process_earthquake_data(geojson_data)
        # Return top 5 by magnitude
        if not df.empty:
            return df.nlargest(5, 'magnitude')
        return df
    except Exception:
        # Return empty dataframe if fetch fails
        return pd.DataFrame()


def inject_mobile_sidebar_behavior():
    """Inject JavaScript to handle mobile sidebar collapse on button click."""
    st.markdown("""
        <script>
        // Auto-collapse sidebar on mobile when Analyze button is clicked
        (function() {
            let analyzeButtonClicked = false;

            function isMobile() {
                return window.innerWidth <= 768;
            }

            function collapseSidebar() {
                if (!isMobile()) return;

                // Try multiple selectors for the sidebar toggle button
                const selectors = [
                    '[data-testid="collapsedControl"]',
                    'button[kind="header"]',
                    'button[kind="headerNoPadding"]',
                    'button[data-testid="baseButton-header"]'
                ];

                let sidebarButton = null;
                for (const selector of selectors) {
                    sidebarButton = document.querySelector(selector);
                    if (sidebarButton) break;
                }

                if (sidebarButton) {
                    // Check if sidebar is currently expanded
                    const sidebar = document.querySelector('[data-testid="stSidebar"]');
                    if (sidebar) {
                        const isExpanded = sidebar.getAttribute('aria-expanded') === 'true';
                        // Also check computed style
                        const computedStyle = window.getComputedStyle(sidebar);
                        const isVisible = computedStyle.transform !== 'none' ||
                                         computedStyle.display !== 'none';

                        if (isExpanded || isVisible) {
                            console.log('Collapsing sidebar...');
                            sidebarButton.click();
                        }
                    } else {
                        // If we can't find sidebar, just click the button
                        sidebarButton.click();
                    }
                }
            }

            // Intercept clicks on the Analyze button
            document.addEventListener('click', function(e) {
                if (!isMobile()) return;

                // Check multiple ways to identify the Analyze button
                const target = e.target;
                const button = target.closest('button');

                if (button) {
                    const buttonText = button.textContent || button.innerText || '';
                    const isAnalyzeButton = buttonText.trim() === 'Analyze' ||
                                          buttonText.includes('Analyze');
                    const isPrimaryButton = button.getAttribute('kind') === 'primary' ||
                                          button.classList.contains('stButton');

                    if (isAnalyzeButton && isPrimaryButton) {
                        console.log('Analyze button clicked!');
                        analyzeButtonClicked = true;

                        // Try multiple delays to ensure it works
                        setTimeout(function() {
                            collapseSidebar();
                            window.scrollTo({ top: 0, behavior: 'smooth' });
                        }, 300);

                        setTimeout(collapseSidebar, 600);
                        setTimeout(collapseSidebar, 1000);
                    }
                }
            }, true); // Use capture phase

            // Also watch for page updates (when results load)
            let lastChildCount = 0;
            const observer = new MutationObserver(function(mutations) {
                if (!isMobile() || !analyzeButtonClicked) return;

                const mainContent = document.querySelector('.main .block-container');
                if (mainContent) {
                    const currentChildCount = mainContent.children.length;

                    // If children increased (results added), collapse sidebar
                    if (currentChildCount > lastChildCount && currentChildCount > 3) {
                        console.log('New content detected, collapsing sidebar...');
                        collapseSidebar();
                        analyzeButtonClicked = false; // Reset flag
                    }

                    lastChildCount = currentChildCount;
                }
            });

            // Start observing after a short delay to let page load
            setTimeout(function() {
                const mainElement = document.querySelector('.main');
                if (mainElement) {
                    observer.observe(mainElement, {
                        childList: true,
                        subtree: true
                    });
                }
            }, 1000);

            // Make mobile nav hint clickable to open sidebar
            document.addEventListener('click', function(e) {
                if (!isMobile()) return;

                if (e.target.classList.contains('mobile-nav-hint')) {
                    const selectors = [
                        '[data-testid="collapsedControl"]',
                        'button[kind="header"]',
                        'button[kind="headerNoPadding"]',
                        'button[data-testid="baseButton-header"]'
                    ];

                    for (const selector of selectors) {
                        const sidebarButton = document.querySelector(selector);
                        if (sidebarButton) {
                            sidebarButton.click();
                            break;
                        }
                    }
                }
            });
        })();
        </script>
    """, unsafe_allow_html=True)


def inject_custom_css():
    """Inject custom CSS for mobile-friendly, Apple/Square-style design."""
    st.markdown("""
        <style>
        /* Import modern font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* Base typography - Apply Inter font globally */
        html, body, [class*="css"], .stApp {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', sans-serif;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        /* Main container styling */
        .main .block-container {
            padding: 2rem 3rem;
            max-width: 1200px;
        }

        /* Glassmorphism card design */
        .earthquake-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px) saturate(180%);
            -webkit-backdrop-filter: blur(20px) saturate(180%);
            border-radius: 16px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            border: 1px solid rgba(255, 255, 255, 0.18);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            animation: fadeInUp 0.6s ease-out;
        }

        .earthquake-card:hover {
            box-shadow: 0 8px 32px 0 rgba(102, 126, 234, 0.5);
            transform: translateY(-4px) scale(1.02);
        }

        /* Hero text with modern styling */
        .hero-text {
            font-size: 3.5rem;
            font-weight: 700;
            margin-bottom: 0.75rem;
            color: #0a0a0a;
            line-height: 1.1;
            letter-spacing: -0.02em;
            background: linear-gradient(135deg, #1a1a1a 0%, #4a4a4a 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .subtitle {
            font-size: 1.25rem;
            color: #6b7280;
            margin-bottom: 2.5rem;
            font-weight: 400;
            letter-spacing: -0.01em;
            line-height: 1.5;
        }

        /* Bold magnitude badge with pulse animation */
        .magnitude-badge {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 24px;
            font-weight: 700;
            font-size: 1.125rem;
            margin-right: 0.75rem;
            letter-spacing: -0.01em;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            animation: pulse-glow 2s ease-in-out infinite;
        }

        .location-text {
            font-size: 1.125rem;
            color: #1f2937;
            font-weight: 600;
            margin: 0.75rem 0 0.5rem 0;
            letter-spacing: -0.01em;
            line-height: 1.4;
        }

        .time-text {
            font-size: 0.9375rem;
            color: #9ca3af;
            font-weight: 400;
            letter-spacing: 0;
        }

        /* Enhanced metrics with glassmorphism */
        div[data-testid="metric-container"] {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px) saturate(180%);
            -webkit-backdrop-filter: blur(20px) saturate(180%);
            padding: 1.25rem;
            border-radius: 12px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.18);
            transition: all 0.3s ease;
            animation: fadeInUp 0.8s ease-out;
        }

        div[data-testid="metric-container"]:hover {
            box-shadow: 0 8px 32px 0 rgba(102, 126, 234, 0.4);
            transform: translateY(-2px);
        }

        div[data-testid="metric-container"] label {
            font-size: 0.875rem;
            font-weight: 500;
            color: #6b7280;
            letter-spacing: 0.01em;
            text-transform: uppercase;
        }

        div[data-testid="metric-container"] [data-testid="stMetricValue"] {
            font-size: 1.875rem;
            font-weight: 700;
            color: #111827;
            letter-spacing: -0.02em;
        }

        /* Bold button styling with vibrant gradient */
        .stButton button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.875rem 2rem;
            font-weight: 600;
            font-size: 1.0625rem;
            letter-spacing: -0.01em;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4);
        }

        .stButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(102, 126, 234, 0.6);
            background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
        }

        .stButton button:active {
            transform: translateY(0);
        }

        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #fafafa 0%, #f5f5f5 100%);
            border-right: 1px solid rgba(0,0,0,0.05);
        }

        section[data-testid="stSidebar"] h2 {
            font-size: 1.5rem;
            font-weight: 700;
            color: #111827;
            letter-spacing: -0.02em;
        }

        section[data-testid="stSidebar"] h3 {
            font-size: 1rem;
            font-weight: 600;
            color: #374151;
            letter-spacing: -0.01em;
            margin-bottom: 0.5rem;
        }

        section[data-testid="stSidebar"] .stRadio label {
            font-weight: 500;
            color: #4b5563;
            font-size: 0.9375rem;
        }

        section[data-testid="stSidebar"] .stTextInput input,
        section[data-testid="stSidebar"] .stSelectbox select {
            font-size: 1rem;
            font-weight: 500;
            border-radius: 8px;
            border: 1px solid #e5e7eb;
            padding: 0.625rem 0.75rem;
        }

        section[data-testid="stSidebar"] .stTextInput input:focus,
        section[data-testid="stSidebar"] .stSelectbox select:focus {
            border-color: #6366f1;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }

        /* Slider styling */
        .stSlider {
            padding: 0.5rem 0;
        }

        .stSlider label {
            font-size: 0.9375rem;
            font-weight: 500;
            color: #374151;
            letter-spacing: -0.01em;
        }

        /* Subheader styling */
        .main h2 {
            font-size: 1.875rem;
            font-weight: 700;
            color: #111827;
            letter-spacing: -0.02em;
            margin-bottom: 1rem;
        }

        .main h3 {
            font-size: 1.5rem;
            font-weight: 600;
            color: #1f2937;
            letter-spacing: -0.01em;
        }

        /* Info boxes with modern styling */
        .stInfo {
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
            border-left: 4px solid #6366f1;
            border-radius: 10px;
            padding: 1rem 1.25rem;
            font-size: 0.9375rem;
            color: #1e40af;
            box-shadow: 0 2px 8px rgba(99, 102, 241, 0.1);
        }

        .stSuccess {
            background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
            border-left: 4px solid #22c55e;
            border-radius: 10px;
            padding: 1rem 1.25rem;
            font-size: 0.9375rem;
            color: #15803d;
        }

        .stError {
            background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
            border-left: 4px solid #ef4444;
            border-radius: 10px;
            padding: 1rem 1.25rem;
            font-size: 0.9375rem;
            color: #991b1b;
        }

        /* Expander styling */
        .streamlit-expanderHeader {
            font-size: 1.125rem;
            font-weight: 600;
            color: #1f2937;
            background: #fafafa;
            border-radius: 8px;
            padding: 0.75rem 1rem;
        }

        /* Show hamburger menu on mobile - target multiple selectors */
        button[kind="header"],
        button[data-testid="baseButton-header"],
        button[kind="headerNoPadding"],
        [data-testid="collapsedControl"] {
            visibility: visible !important;
            display: block !important;
        }

        /* Make hamburger menu more prominent on mobile */
        @media (max-width: 768px) {
            button[kind="header"],
            button[data-testid="baseButton-header"],
            button[kind="headerNoPadding"],
            [data-testid="collapsedControl"] {
                background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
                color: white !important;
                border-radius: 10px !important;
                padding: 0.625rem !important;
                margin: 0.75rem !important;
                box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4) !important;
                border: none !important;
                width: 48px !important;
                height: 48px !important;
            }

            button[kind="header"]:hover,
            button[data-testid="baseButton-header"]:hover,
            button[kind="headerNoPadding"]:hover,
            [data-testid="collapsedControl"]:hover {
                box-shadow: 0 6px 16px rgba(99, 102, 241, 0.5) !important;
                transform: scale(1.05);
            }

            /* Hamburger icon styling */
            button[kind="header"] svg,
            button[data-testid="baseButton-header"] svg,
            button[kind="headerNoPadding"] svg,
            [data-testid="collapsedControl"] svg {
                color: white !important;
                fill: white !important;
                width: 24px !important;
                height: 24px !important;
            }

            /* Ensure sidebar is accessible on mobile */
            section[data-testid="stSidebar"] {
                position: fixed;
                z-index: 999;
                height: 100vh;
                top: 0;
                left: 0;
            }

            section[data-testid="stSidebar"][aria-expanded="true"] {
                width: 85vw;
                max-width: 340px;
            }

            /* Smooth sidebar animation */
            section[data-testid="stSidebar"] {
                transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }
        }

        /* Hide default Streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* Mobile navigation hint */
        .mobile-nav-hint {
            display: none;
        }

        @media (max-width: 768px) {
            .mobile-nav-hint {
                display: block;
                background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                color: white;
                padding: 0.75rem 1rem;
                border-radius: 10px;
                text-align: center;
                font-size: 0.9375rem;
                font-weight: 500;
                margin-bottom: 1rem;
                box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
                cursor: pointer;
                transition: all 0.2s ease;
            }

            .mobile-nav-hint:active {
                transform: scale(0.98);
            }

            .mobile-nav-hint::before {
                content: '☰ ';
                font-size: 1.25rem;
                margin-right: 0.5rem;
            }

            /* Hide hint when sidebar is open */
            section[data-testid="stSidebar"][aria-expanded="true"] ~ .main .mobile-nav-hint {
                display: none;
            }

            /* Ensure main content is not hidden behind sidebar on mobile */
            .main {
                position: relative;
                z-index: 1;
            }
        }

        /* Mobile responsiveness */
        @media (max-width: 768px) {
            .main .block-container {
                padding: 1rem 1rem;
                max-width: 100%;
            }

            .hero-text {
                font-size: 2.25rem;
                letter-spacing: -0.015em;
            }

            .subtitle {
                font-size: 1.0625rem;
                margin-bottom: 1.5rem;
            }

            .earthquake-card {
                padding: 1.25rem;
                margin: 0.75rem 0;
            }

            .magnitude-badge {
                font-size: 1rem;
                padding: 0.4rem 0.875rem;
            }

            .location-text {
                font-size: 1rem;
            }

            .time-text {
                font-size: 0.875rem;
            }

            .stButton button {
                width: 100%;
                padding: 0.875rem;
                font-size: 1rem;
            }

            div[data-testid="column"] {
                padding: 0.25rem;
            }

            div[data-testid="metric-container"] [data-testid="stMetricValue"] {
                font-size: 1.5rem;
            }

            .main h2 {
                font-size: 1.5rem;
            }

            .main h3 {
                font-size: 1.25rem;
            }
        }

        /* Tablet responsiveness */
        @media (min-width: 769px) and (max-width: 1024px) {
            .main .block-container {
                padding: 1.5rem 2rem;
            }

            .hero-text {
                font-size: 3rem;
            }

            .subtitle {
                font-size: 1.125rem;
            }
        }

        /* Info box styling */
        .info-box {
            background-color: #f0f8ff;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            border-left: 4px solid #6366f1;
            box-shadow: 0 2px 8px rgba(99, 102, 241, 0.1);
        }

        /* Smooth scrolling */
        html {
            scroll-behavior: smooth;
        }

        /* ============================================
           ANIMATIONS & KEYFRAMES
           ============================================ */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes pulse-glow {
            0%, 100% {
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            }
            50% {
                box-shadow: 0 4px 20px rgba(102, 126, 234, 0.8);
            }
        }

        @keyframes slideInLeft {
            from {
                opacity: 0;
                transform: translateX(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        /* Glass card utility class */
        .glass-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px) saturate(180%);
            -webkit-backdrop-filter: blur(20px) saturate(180%);
            border-radius: 12px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            border: 1px solid rgba(255, 255, 255, 0.18);
        }

        /* Activity feed item styling */
        .activity-item {
            padding: 0.75rem;
            margin: 0.5rem 0;
            border-radius: 10px;
            animation: slideInLeft 0.5s ease-out;
            transition: transform 0.2s ease;
        }

        .activity-item:hover {
            transform: translateX(5px);
        }

        /* ============================================
           DARK MODE SUPPORT
           ============================================ */
        @media (prefers-color-scheme: dark) {
            /* Base app background */
            .stApp {
                background-color: #0a0a0a;
                color: #e5e5e5;
            }

            /* Main container */
            .main .block-container {
                background-color: transparent;
            }

            /* Hero text - Light gradient for dark mode */
            .hero-text {
                color: #e5e5e5;
                background: linear-gradient(135deg, #ffffff 0%, #a3a3a3 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }

            /* Subtitle - Light gray */
            .subtitle {
                color: #a3a3a3;
            }

            /* Earthquake cards - Glassmorphism dark mode */
            .earthquake-card {
                background: rgba(26, 26, 26, 0.7);
                backdrop-filter: blur(20px) saturate(180%);
                -webkit-backdrop-filter: blur(20px) saturate(180%);
                border: 1px solid rgba(255,255,255,0.1);
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
            }

            .earthquake-card:hover {
                box-shadow: 0 8px 32px 0 rgba(102, 126, 234, 0.4);
            }

            /* Glass card for dark mode */
            .glass-card {
                background: rgba(26, 26, 26, 0.7);
                backdrop-filter: blur(20px) saturate(180%);
                -webkit-backdrop-filter: blur(20px) saturate(180%);
                border: 1px solid rgba(255,255,255,0.1);
            }

            /* Location and time text */
            .location-text {
                color: #e5e5e5;
            }

            .time-text {
                color: #a3a3a3;
            }

            /* Metrics - Glassmorphism dark mode */
            div[data-testid="metric-container"] {
                background: rgba(26, 26, 26, 0.7);
                backdrop-filter: blur(20px) saturate(180%);
                -webkit-backdrop-filter: blur(20px) saturate(180%);
                border: 1px solid rgba(255,255,255,0.1);
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
            }

            div[data-testid="metric-container"]:hover {
                box-shadow: 0 8px 32px 0 rgba(102, 126, 234, 0.4);
            }

            div[data-testid="metric-container"] label {
                color: #a3a3a3;
            }

            div[data-testid="metric-container"] [data-testid="stMetricValue"] {
                color: #e5e5e5;
            }

            /* Sidebar - Dark background */
            section[data-testid="stSidebar"] {
                background: linear-gradient(180deg, #1a1a1a 0%, #0a0a0a 100%);
                border-right: 1px solid rgba(255,255,255,0.1);
            }

            section[data-testid="stSidebar"] h2 {
                color: #e5e5e5;
            }

            section[data-testid="stSidebar"] h3 {
                color: #d4d4d4;
            }

            section[data-testid="stSidebar"] .stRadio label {
                color: #d4d4d4;
            }

            section[data-testid="stSidebar"] .stTextInput input,
            section[data-testid="stSidebar"] .stSelectbox select {
                background-color: #262626;
                color: #e5e5e5;
                border: 1px solid rgba(255,255,255,0.2);
            }

            section[data-testid="stSidebar"] .stTextInput input:focus,
            section[data-testid="stSidebar"] .stSelectbox select:focus {
                border-color: #8b5cf6;
                box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2);
            }

            /* Slider labels */
            .stSlider label {
                color: #d4d4d4;
            }

            /* Main headings */
            .main h2 {
                color: #e5e5e5;
            }

            .main h3 {
                color: #d4d4d4;
            }

            /* Info boxes - Darker versions */
            .info-box {
                background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                border-left: 4px solid #6366f1;
                color: #93c5fd;
                box-shadow: 0 2px 8px rgba(99, 102, 241, 0.2);
            }

            .stInfo {
                background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                border-left: 4px solid #6366f1;
                color: #93c5fd;
                box-shadow: 0 2px 8px rgba(99, 102, 241, 0.2);
            }

            .stSuccess {
                background: linear-gradient(135deg, #14532d 0%, #052e16 100%);
                border-left: 4px solid #22c55e;
                color: #86efac;
            }

            .stError {
                background: linear-gradient(135deg, #7f1d1d 0%, #450a0a 100%);
                border-left: 4px solid #ef4444;
                color: #fca5a5;
            }

            /* Expander headers */
            .streamlit-expanderHeader {
                color: #e5e5e5;
                background: #1a1a1a;
                border: 1px solid rgba(255,255,255,0.1);
            }

            /* Date input and other form elements */
            section[data-testid="stSidebar"] .stDateInput input {
                background-color: #262626;
                color: #e5e5e5;
                border: 1px solid rgba(255,255,255,0.2);
            }

            /* Ensure text in columns is visible */
            div[data-testid="column"] {
                color: #e5e5e5;
            }

            /* Plotly charts - adjust for dark mode */
            .js-plotly-plot {
                background-color: transparent !important;
            }

            /* Mobile navigation hint for dark mode */
            @media (max-width: 768px) {
                .mobile-nav-hint {
                    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                    color: #ffffff;
                    box-shadow: 0 2px 8px rgba(99, 102, 241, 0.4);
                }

                /* Ensure hamburger menu is visible in dark mode */
                button[kind="header"],
                button[data-testid="baseButton-header"],
                button[kind="headerNoPadding"],
                [data-testid="collapsedControl"] {
                    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
                    color: white !important;
                }

                button[kind="header"] svg,
                button[data-testid="baseButton-header"] svg,
                button[kind="headerNoPadding"] svg,
                [data-testid="collapsedControl"] svg {
                    color: white !important;
                    fill: white !important;
                }
            }

            /* Ensure all paragraph text is visible */
            p, span, div {
                color: inherit;
            }

            /* Radio button text visibility */
            .stRadio > label {
                color: #d4d4d4;
            }

            /* Selectbox dropdown options */
            option {
                background-color: #262626;
                color: #e5e5e5;
            }

            /* Streamlit native elements */
            [data-testid="stMarkdownContainer"] {
                color: #e5e5e5;
            }

            /* Ensure labels are visible */
            label {
                color: #d4d4d4 !important;
            }

            /* Text input labels */
            .stTextInput > label,
            .stSelectbox > label,
            .stDateInput > label {
                color: #d4d4d4 !important;
            }

            /* Additional mobile improvements for dark mode */
            @media (max-width: 768px) {
                /* Ensure sidebar content is scrollable and visible */
                section[data-testid="stSidebar"] > div {
                    background-color: #0a0a0a;
                }

                /* Better contrast for form elements on mobile */
                section[data-testid="stSidebar"] .stTextInput input,
                section[data-testid="stSidebar"] .stSelectbox select,
                section[data-testid="stSidebar"] .stDateInput input {
                    background-color: #1a1a1a;
                    border: 2px solid rgba(255,255,255,0.2);
                    font-size: 16px; /* Prevent zoom on iOS */
                }

                /* Enhance touch targets for mobile */
                .stButton button {
                    min-height: 48px;
                    font-size: 1rem;
                }

                /* Improve radio button visibility on mobile */
                section[data-testid="stSidebar"] .stRadio label {
                    font-size: 1rem;
                    padding: 0.5rem 0;
                }
            }
        }

        /* Light mode mobile enhancements */
        @media (max-width: 768px) {
            /* Ensure minimum touch target sizes */
            .stButton button,
            section[data-testid="stSidebar"] .stTextInput input,
            section[data-testid="stSidebar"] .stSelectbox select {
                min-height: 44px; /* iOS minimum recommended touch target */
            }

            /* Better spacing for mobile form elements */
            section[data-testid="stSidebar"] .stTextInput,
            section[data-testid="stSidebar"] .stSelectbox,
            section[data-testid="stSidebar"] .stDateInput,
            section[data-testid="stSidebar"] .stSlider {
                margin-bottom: 1.25rem;
            }

            /* Ensure labels are readable on mobile */
            section[data-testid="stSidebar"] h3 {
                font-size: 1.125rem;
                margin-top: 1rem;
                margin-bottom: 0.75rem;
            }

            /* Improve mobile card readability */
            .earthquake-card {
                font-size: 0.9375rem;
            }

            /* Better mobile metrics display */
            div[data-testid="metric-container"] {
                padding: 1rem;
            }

            div[data-testid="metric-container"] label {
                font-size: 0.8125rem;
            }

            div[data-testid="metric-container"] [data-testid="stMetricValue"] {
                font-size: 1.5rem;
            }

            /* Mobile-friendly expanders */
            .streamlit-expanderHeader {
                font-size: 1rem;
                padding: 0.875rem 1rem;
            }

            /* Prevent horizontal scroll on mobile */
            .main .block-container {
                overflow-x: hidden;
            }
        }
        </style>
    """, unsafe_allow_html=True)


def format_statistics_display(stats: dict, location: str) -> None:
    """
    Display statistics in a user-friendly format.

    Args:
        stats: Statistics dictionary
        location: Location name
    """
    if stats.get('total_count', 0) == 0:
        st.info(stats.get('message', 'No earthquakes found.'))
        return

    # Magnitude Statistics
    with st.expander("📊 Magnitude Statistics", expanded=True):
        mag_stats = stats.get('magnitude', {})
        strongest = stats.get('strongest_earthquake', {})

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Average", f"M {mag_stats.get('average', 0):.2f}")
        with col2:
            st.metric("Maximum", f"M {mag_stats.get('max', 0):.1f}")
        with col3:
            st.metric("Minimum", f"M {mag_stats.get('min', 0):.1f}")
        with col4:
            st.metric("Median", f"M {mag_stats.get('median', 0):.2f}")

        if strongest:
            st.markdown("### Strongest Earthquake")
            st.markdown(f"""
            - **Magnitude:** M {strongest['magnitude']:.1f}
            - **Time:** {strongest['time'].strftime('%Y-%m-%d %H:%M:%S')}
            - **Location:** {strongest['place']}
            - **Depth:** {strongest['depth']:.1f} km
            - **Coordinates:** {strongest['latitude']:.4f}, {strongest['longitude']:.4f}
            """)

        # Magnitude distribution percentages
        mag_dist_pct = stats.get('magnitude_distribution_pct', {})
        if mag_dist_pct:
            st.markdown("### Distribution by Category")
            for category, percentage in sorted(mag_dist_pct.items(),
                                              key=lambda x: x[1], reverse=True):
                count = stats['magnitude_distribution'].get(category, 0)
                st.markdown(f"- **{category}:** {count} earthquakes ({percentage:.1f}%)")

    # Temporal Patterns
    with st.expander("⏰ Temporal Patterns"):
        temporal = stats.get('temporal', {})

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Duration", f"{temporal.get('duration_days', 0)} days")
            st.metric("Average per Day", f"{temporal.get('avg_per_day', 0):.1f}")
        with col2:
            if 'most_active_date' in temporal:
                st.metric("Most Active Day",
                         temporal['most_active_date'].strftime('%Y-%m-%d'))
                st.metric("Earthquakes on That Day",
                         temporal.get('most_active_count', 0))

        if 'longest_quiet_period_days' in temporal:
            st.markdown(f"""
            ### Longest Quiet Period
            - **Duration:** {temporal['longest_quiet_period_days']} days
            - **Starting:** {temporal['quiet_period_start'].strftime('%Y-%m-%d')}
            """)

    # Depth Analysis
    if 'depth' in stats:
        with st.expander("📏 Depth Analysis"):
            depth_stats = stats['depth']

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Average Depth", f"{depth_stats.get('average', 0):.1f} km")
            with col2:
                st.metric("Deepest", f"{depth_stats.get('max', 0):.1f} km")
            with col3:
                st.metric("Shallowest", f"{depth_stats.get('min', 0):.1f} km")

            depth_dist = stats.get('depth_distribution', {})
            if depth_dist:
                st.markdown("### Distribution by Depth")
                for category, count in depth_dist.items():
                    percentage = (count / stats['total_count']) * 100
                    st.markdown(f"- **{category}:** {count} earthquakes ({percentage:.1f}%)")

    # Energy Released
    if 'energy' in stats:
        with st.expander("⚡ Energy Released"):
            energy = stats['energy']

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### Total Energy Released")
                st.markdown(f"**{energy['total_formatted']}**")
            with col2:
                st.markdown("### Largest Single Event")
                st.markdown(f"**{energy['max_formatted']}**")

            st.info(
                "Energy calculations use the standard seismic formula: "
                "E = 10^(1.5×M + 4.8) joules"
            )

    # Interesting Facts
    with st.expander("🔍 Interesting Facts", expanded=True):
        facts = stats.get('interesting_facts', {})

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Feelable Earthquakes (M ≥ 3.0)",
                     facts.get('feelable_count', 0))
            st.metric("Potentially Damaging (M ≥ 5.0)",
                     facts.get('damaging_count', 0))
        with col2:
            st.metric("Earthquake Swarms Detected",
                     facts.get('swarm_count', 0))

        st.markdown("### Geographic Spread")
        st.markdown(f"""
        - **Nearest to center:** {facts.get('nearest_formatted', 'N/A')}
        - **Farthest from center:** {facts.get('farthest_formatted', 'N/A')}
        """)

        # Show swarm details
        swarms = facts.get('swarms', [])
        if swarms:
            st.markdown("### Detected Earthquake Swarms")
            for i, swarm in enumerate(swarms, 1):
                st.markdown(f"""
                **Swarm {i}:**
                - **Period:** {swarm['start_time'].strftime('%Y-%m-%d %H:%M')} to
                  {swarm['end_time'].strftime('%Y-%m-%d %H:%M')}
                - **Events:** {swarm['count']}
                - **Location:** {swarm['location']}
                """)


def main():
    """Main application function."""

    # Inject custom CSS for clean, mobile-friendly design
    inject_custom_css()

    # Inject JavaScript for mobile sidebar behavior
    inject_mobile_sidebar_behavior()

    # Initialize Google Analytics tracking
    inject_ga_tracking()

    # Initialize gamification system
    initialize_gamification()

    # Header - Clean and minimal
    st.markdown('<h1 class="hero-text">Seismic Earthquake Analyzer</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Real-time earthquake data from USGS</p>', unsafe_allow_html=True)

    # Mobile navigation hint
    st.markdown('<div class="mobile-nav-hint">Tap the menu icon to search earthquakes</div>', unsafe_allow_html=True)

    # Sidebar - Input Controls
    with st.sidebar:
        st.header("Search Parameters")

        # Location input
        st.subheader("📍 Location")
        location_type = st.radio(
            "",
            ["City Name", "Zip Code"],
            label_visibility="collapsed"
        )

        is_zipcode = location_type == "Zip Code"
        location = st.text_input(
            "Location",
            value="San Ramon" if not is_zipcode else "",
            placeholder="e.g., San Francisco" if not is_zipcode else "e.g., 94102",
            label_visibility="collapsed"
        )

        # Date range
        st.subheader("📅 Time Range")

        # Time range selection
        time_range_option = st.selectbox(
            "Time Range",
            options=[
                "Today",
                "Last 15 minutes",
                "Last 30 minutes",
                "Last 1 hour",
                "Last 12 hours",
                "Custom date range"
            ],
            index=0,
            label_visibility="collapsed"
        )

        # Calculate datetime based on selection
        if time_range_option == "Custom date range":
            # Show date pickers for custom range
            col1, col2 = st.columns(2)

            with col1:
                # Default to 30 days ago
                default_start = datetime.now() - timedelta(days=30)
                start_date = st.date_input(
                    "Start",
                    value=default_start,
                    max_value=datetime.now().date()
                )

            with col2:
                end_date = st.date_input(
                    "End",
                    value=datetime.now() - timedelta(days=1),
                    max_value=datetime.now().date()
                )

            # Convert dates to datetime
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
        else:
            # Calculate datetime for preset ranges
            current_time = datetime.now()
            end_datetime = current_time

            if time_range_option == "Last 15 minutes":
                start_datetime = current_time - timedelta(minutes=15)
            elif time_range_option == "Last 30 minutes":
                start_datetime = current_time - timedelta(minutes=30)
            elif time_range_option == "Last 1 hour":
                start_datetime = current_time - timedelta(hours=1)
            elif time_range_option == "Last 12 hours":
                start_datetime = current_time - timedelta(hours=12)
            elif time_range_option == "Today":
                # Midnight today to current time
                start_datetime = datetime.combine(current_time.date(), datetime.min.time())

            # Extract date values for use in filename
            start_date = start_datetime.date()
            end_date = end_datetime.date()

            # Display selected time range for user confirmation
            st.caption(f"📅 From: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
            st.caption(f"📅 To: {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

        # Filters
        st.subheader("⚙️ Filters")

        min_magnitude = st.slider(
            "Min Magnitude",
            min_value=0.0,
            max_value=8.0,
            value=1.0,
            step=0.5
        )

        radius_km = st.slider(
            "Radius (km)",
            min_value=50,
            max_value=1000,
            value=DEFAULT_SEARCH_RADIUS_KM,
            step=50
        )

        st.markdown("")  # Add spacing

        # Submit button
        analyze_button = st.button("Analyze", type="primary", use_container_width=True)

        # Gamification UI (points, badges, progress)
        st.markdown("---")
        render_gamification_sidebar()

        # Live activity feed
        st.markdown("---")
        render_activity_feed()

        # Daily trivia challenge
        render_trivia_sidebar()

    # Main area - Results
    # Store results in session state when analyze button is clicked
    if analyze_button:
        # Track search event
        track_event('search_earthquakes', {
            'location_type': location_type,
            'time_range': time_range_option,
            'min_magnitude': min_magnitude,
            'radius_km': radius_km
        })

        # Validation
        if not location:
            st.error("Please enter a location.")
            return

        # Only validate custom date ranges (preset ranges are always valid)
        if time_range_option == "Custom date range":
            if start_datetime >= end_datetime:
                st.error("Start date must be before end date.")
                return

            if end_datetime.date() > datetime.now().date():
                st.error("End date cannot be in the future.")
                return

        try:
            # Step 1: Geocode location
            with st.spinner("🌐 Geocoding location..."):
                try:
                    latitude, longitude = cached_geocode(location, is_zipcode)
                    st.success(f"📍 Location found: {latitude:.4f}, {longitude:.4f}")
                except ValueError as e:
                    st.error(f"❌ Geocoding error: {str(e)}")
                    st.info(
                        "Suggestions:\n"
                        "- Check the spelling of the city name\n"
                        "- Try a more specific location (e.g., 'San Francisco, CA')\n"
                        "- Ensure the zip code is valid"
                    )
                    return
                except (GeocoderTimedOut, GeocoderServiceError) as e:
                    st.error(f"❌ Geocoding service error: {str(e)}")
                    st.info("The geocoding service may be temporarily unavailable. Please try again in a moment.")
                    return

            # Step 2: Fetch earthquake data
            with st.spinner("📡 Fetching earthquake data from USGS..."):
                try:
                    min_mag = min_magnitude if min_magnitude > 0 else None
                    geojson_data = cached_fetch_earthquakes(
                        latitude, longitude,
                        start_datetime, end_datetime,
                        min_mag, radius_km
                    )
                except USGSAPIError as e:
                    st.error(f"❌ USGS API error: {str(e)}")
                    if "limit reached" in str(e).lower():
                        st.info(
                            "Try narrowing your search:\n"
                            "- Reduce the time range\n"
                            "- Increase minimum magnitude\n"
                            "- Decrease search radius"
                        )
                    return
                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)}")
                    return

            # Step 3: Process data
            with st.spinner("⚙️ Processing earthquake data..."):
                df = process_earthquake_data(geojson_data)

                if df.empty:
                    st.info("No earthquakes found in the specified region and time period.")
                    st.markdown("""
                    ### Suggestions:
                    - Try expanding the date range
                    - Increase the search radius
                    - Lower the minimum magnitude filter
                    - Try a different location
                    """)
                    return

                # Calculate statistics
                stats = calculate_statistics(df, latitude, longitude)

                # Determine time granularity
                interval, interval_label = determine_time_granularity(
                    start_datetime, end_datetime
                )

                # Aggregate by time interval
                aggregated_df = aggregate_by_time_interval(df, interval)

                # Store results in session state for persistence across reruns
                st.session_state.results = {
                    'df': df,
                    'stats': stats,
                    'aggregated_df': aggregated_df,
                    'interval': interval,
                    'interval_label': interval_label,
                    'latitude': latitude,
                    'longitude': longitude,
                    'radius_km': radius_km,
                    'location': location,
                    'start_datetime': start_datetime,
                    'end_datetime': end_datetime,
                    'start_date': start_date,
                    'end_date': end_date
                }

            # Track successful search with results
            track_event('search_results', {
                'earthquakes_found': len(df),
                'location': location,
                'has_dyfi_data': not df[(df['cdi'].notna()) | (df['felt'].notna())].empty
            })

            # Record search for gamification
            has_major = stats.get('magnitude', {}).get('max', 0) >= 7.0
            record_search(has_major_quake=has_major)

        except Exception as e:
            st.error(f"❌ An unexpected error occurred: {str(e)}")
            st.info("Please try again or contact support if the problem persists.")

    # Display results if they exist in session state
    if 'results' in st.session_state:
        # Extract results from session state
        results = st.session_state.results
        df = results['df']
        stats = results['stats']
        aggregated_df = results['aggregated_df']
        interval = results['interval']
        interval_label = results['interval_label']
        latitude = results['latitude']
        longitude = results['longitude']
        radius_km = results['radius_km']
        location = results['location']
        start_datetime = results['start_datetime']
        end_datetime = results['end_datetime']
        start_date = results['start_date']
        end_date = results['end_date']

        # Show success message when results are first loaded
        if analyze_button:
            st.success(f"✅ Analysis complete! Found {len(df)} earthquakes.")

        # Summary metrics
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("📊 Total Earthquakes", len(df))
        with col2:
            if 'magnitude' in stats:
                st.metric("📈 Max Magnitude", f"M {stats['magnitude']['max']:.1f}")
        with col3:
            if 'magnitude' in stats:
                st.metric("📉 Avg Magnitude", f"M {stats['magnitude']['average']:.2f}")
        with col4:
            st.metric("🌐 Search Radius", f"{radius_km} km")

        st.markdown("---")

        # Map View with 3D globe option
        st.subheader("🗺️ Earthquake Map View")

        # Map mode toggle
        map_mode = st.radio(
            "Map Style",
            ["2D Map", "3D Globe"],
            horizontal=True,
            help="Choose between 2D interactive map or 3D globe visualization"
        )

        if map_mode == "3D Globe":
            st.info("🌍 3D globe showing earthquakes. Rotate, zoom, and explore! Color indicates depth: red (shallow), orange (intermediate), blue (deep).")
            try:
                globe_view = create_3d_globe_view(df, latitude, longitude)
                st.pydeck_chart(globe_view)
            except Exception as e:
                st.error(f"Unable to render 3D globe: {str(e)}")
                st.info("Falling back to 2D map...")
                map_fig = create_earthquake_map(df, latitude, longitude, radius_km)
                st.plotly_chart(map_fig, use_container_width=True)
        else:
            st.info("Interactive map showing earthquake locations. Purple dots indicate magnitude < 2.0, red dots indicate magnitude ≥ 2.0. Larger markers indicate higher magnitudes. Click on markers for details.")
            map_fig = create_earthquake_map(df, latitude, longitude, radius_km)
            st.plotly_chart(map_fig, use_container_width=True)

        st.markdown("---")

        # Community Confirmed Section (DYFI Data)
        st.subheader("👥 Confirmed by Community")

        # Check if we have any DYFI data
        dyfi_data = df[(df['cdi'].notna()) | (df['felt'].notna())]

        if not dyfi_data.empty:
            # Summary metrics
            total_felt_reports = int(dyfi_data['felt'].sum()) if dyfi_data['felt'].notna().any() else 0
            avg_cdi = dyfi_data['cdi'].mean() if dyfi_data['cdi'].notna().any() else None
            earthquakes_with_reports = len(dyfi_data)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📝 Community Reports", f"{total_felt_reports:,}")
            with col2:
                st.metric("🌍 Earthquakes Reported", earthquakes_with_reports)
            with col3:
                if avg_cdi:
                    st.metric("📊 Avg Intensity", f"{avg_cdi:.1f} CDI")

            st.markdown("---")

            # DYFI visualization
            dyfi_fig = create_dyfi_visualization(df)
            st.plotly_chart(dyfi_fig, use_container_width=True)
        else:
            st.info("No community-reported data available for the earthquakes in this search.")

        st.markdown("---")

        # Visualizations Section
        st.subheader("📊 Temporal Analysis")

        # Timeline chart
        timeline_fig = create_timeline_chart(df)
        st.plotly_chart(timeline_fig, use_container_width=True)

        st.markdown("---")

        # Occurrence bar chart
        occurrence_fig = create_occurrence_bar_chart(aggregated_df, interval, interval_label)
        st.plotly_chart(occurrence_fig, use_container_width=True)

        st.markdown("---")

        # Distribution Analysis Section
        st.subheader("📈 Distribution Analysis")

        col1, col2 = st.columns(2)

        with col1:
            mag_dist_fig = create_magnitude_distribution_chart(df)
            st.plotly_chart(mag_dist_fig, use_container_width=True)

        with col2:
            depth_dist_fig = create_depth_distribution_chart(df)
            st.plotly_chart(depth_dist_fig, use_container_width=True)

        # Magnitude vs Depth scatter
        mag_depth_fig = create_magnitude_vs_depth_scatter(df)
        st.plotly_chart(mag_depth_fig, use_container_width=True)

        st.markdown("---")

        # Statistics Section
        st.subheader("📊 Detailed Statistics")
        format_statistics_display(stats, location)

        st.markdown("---")

        # Data Storytelling Section
        time_range_days = (end_datetime - start_datetime).days or 1
        render_storytelling_sections(df, stats, time_range_days)

        st.markdown("---")

        # Social Sharing Section
        create_share_buttons(location, stats)

        st.markdown("---")

        # Data export option
        with st.expander("💾 Export Data"):
            st.markdown("Download the earthquake data as CSV")

            csv = df.to_csv(index=False)
            if st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"earthquakes_{location}_{start_date}_{end_date}.csv",
                mime="text/csv"
            ):
                # Track data export
                track_event('export_data', {
                    'format': 'csv',
                    'location': location,
                    'num_earthquakes': len(df)
                })
                # Record export for gamification
                record_export()

    elif not analyze_button:
        # Show today's significant earthquakes when no search has been performed
        st.markdown("---")

        # Display today's top earthquakes
        st.subheader("Today's Significant Earthquakes")

        try:
            with st.spinner("Loading today's earthquakes..."):
                todays_earthquakes = fetch_todays_significant_earthquakes()

                if not todays_earthquakes.empty:
                    # Display earthquake cards
                    for idx, quake in todays_earthquakes.iterrows():
                        magnitude = quake['magnitude']
                        place = quake['place']
                        time_str = quake['time'].strftime('%H:%M UTC')
                        depth = quake['depth']

                        st.markdown(f"""
                        <div class="earthquake-card">
                            <span class="magnitude-badge">M {magnitude:.1f}</span>
                            <div class="location-text">{place}</div>
                            <div class="time-text">{time_str} • Depth: {depth:.1f} km</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No significant earthquakes recorded today (M 4.5+)")

        except Exception:
            # Silently fail if we can't fetch today's earthquakes
            st.info("Use the sidebar to search for earthquakes in any location")

        st.markdown("---")

        # Simple feature highlights
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### 🗺️")
            st.markdown("**Interactive Maps**")
            st.markdown("Visualize earthquake locations")

        with col2:
            st.markdown("### 📊")
            st.markdown("**Deep Analytics**")
            st.markdown("Statistics and patterns")

        with col3:
            st.markdown("### 💾")
            st.markdown("**Export Data**")
            st.markdown("Download for analysis")


if __name__ == "__main__":
    main()
