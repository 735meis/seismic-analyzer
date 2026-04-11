"""
Social Media Sharing - Generate shareable content and platform-specific share buttons.
"""

import streamlit as st
import urllib.parse
from typing import Dict


def generate_share_text(location: str, total_quakes: int, max_mag: float) -> str:
    """
    Generate shareable text for social media.

    Args:
        location: Search location
        total_quakes: Total number of earthquakes found
        max_mag: Maximum magnitude

    Returns:
        Formatted share text
    """
    text = f"🌍 Just analyzed {total_quakes} earthquakes near {location}! "

    if max_mag >= 7.0:
        text += f"Strongest: M{max_mag:.1f} 😱 "
    elif max_mag >= 5.0:
        text += f"Strongest: M{max_mag:.1f} ⚡ "
    else:
        text += f"Max magnitude: M{max_mag:.1f} "

    text += "#Seismology #Earthquakes #DataScience"

    return text


def create_share_buttons(location: str, stats: Dict):
    """
    Create social media share buttons.

    Args:
        location: Search location
        stats: Dictionary with earthquake statistics (total_quakes, max_mag, etc.)
    """
    total_quakes = stats.get('total_count', 0)
    max_mag = stats.get('magnitude', {}).get('max', 0)

    # Generate share text
    share_text = generate_share_text(location, total_quakes, max_mag)
    app_url = "https://seismic-analyzer.streamlit.app"  # Update with actual URL

    # URL encode the text
    encoded_text = urllib.parse.quote(share_text)
    encoded_url = urllib.parse.quote(app_url)

    # Platform-specific share URLs
    twitter_url = f"https://twitter.com/intent/tweet?text={encoded_text}&url={encoded_url}"
    facebook_url = f"https://www.facebook.com/sharer/sharer.php?u={encoded_url}"
    linkedin_url = f"https://www.linkedin.com/sharing/share-offsite/?url={encoded_url}"
    whatsapp_url = f"https://wa.me/?text={encoded_text}%20{encoded_url}"

    # Instagram doesn't have direct web share, so we'll provide a copy link option
    instagram_text = share_text.replace('#Seismology #Earthquakes #DataScience', '#Seismology #Earthquakes #DataScience #EarthquakeAnalysis')

    # Compact, elegant share section
    st.markdown("""
    <style>
    .share-section {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 12px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
    }
    .share-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
        margin-bottom: 0.5rem;
        display: inline-block;
    }
    .share-button {
        padding: 0.5rem 0.75rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease;
        border-radius: 8px;
        margin-bottom: 0.25rem;
    }
    .share-button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    .share-button .icon {
        font-size: 1.25rem;
        margin-bottom: 0.15rem;
    }
    .share-button .label {
        font-size: 0.65rem;
        font-weight: 600;
        margin-top: 0.15rem;
        opacity: 0.9;
    }
    @media (max-width: 768px) {
        .share-button {
            padding: 0.4rem 0.6rem;
        }
        .share-button .icon {
            font-size: 1.1rem;
        }
        .share-button .label {
            font-size: 0.6rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="share-section"><span class="share-title">📤 Share</span></div>', unsafe_allow_html=True)

    # Compact layout: all buttons in one row
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(
            f"""
            <a href="{twitter_url}" target="_blank" style="text-decoration: none;">
                <div class="glass-card share-button" style="border: 1px solid rgba(29, 161, 242, 0.3);">
                    <div class="icon">𝕏</div>
                    <div class="label">Twitter</div>
                </div>
            </a>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <a href="{facebook_url}" target="_blank" style="text-decoration: none;">
                <div class="glass-card share-button" style="border: 1px solid rgba(24, 119, 242, 0.3);">
                    <div class="icon">📘</div>
                    <div class="label">Facebook</div>
                </div>
            </a>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <a href="{linkedin_url}" target="_blank" style="text-decoration: none;">
                <div class="glass-card share-button" style="border: 1px solid rgba(0, 119, 181, 0.3);">
                    <div class="icon">💼</div>
                    <div class="label">LinkedIn</div>
                </div>
            </a>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            f"""
            <a href="{whatsapp_url}" target="_blank" style="text-decoration: none;">
                <div class="glass-card share-button" style="border: 1px solid rgba(37, 211, 102, 0.3);">
                    <div class="icon">💬</div>
                    <div class="label">WhatsApp</div>
                </div>
            </a>
            """,
            unsafe_allow_html=True
        )

    with col5:
        st.markdown(
            f"""
            <div onclick="copyInstagramLink()" style="cursor: pointer; text-decoration: none;">
                <div class="glass-card share-button" style="border: 1px solid rgba(193, 53, 132, 0.3);">
                    <div class="icon">📷</div>
                    <div class="label">Instagram</div>
                </div>
            </div>
            <script>
            function copyInstagramLink() {{
                const text = '{instagram_text} {app_url}';
                navigator.clipboard.writeText(text).then(function() {{
                    alert('📋 Link copied! Paste in Instagram story, bio, or post caption.');
                }}).catch(function(err) {{
                    alert('Please copy this text: ' + text);
                }});
            }}
            </script>
            """,
            unsafe_allow_html=True
        )


def create_share_metadata(location: str, stats: Dict) -> Dict[str, str]:
    """
    Generate Open Graph metadata for better social sharing.

    Args:
        location: Search location
        stats: Earthquake statistics

    Returns:
        Dictionary with OG tags
    """
    total_quakes = stats.get('total_count', 0)
    max_mag = stats.get('magnitude', {}).get('max', 0)

    metadata = {
        'og:title': f'Earthquake Analysis: {location}',
        'og:description': f'Found {total_quakes} earthquakes. Strongest: M{max_mag:.1f}',
        'og:type': 'website',
        'og:image': 'https://seismic-analyzer.streamlit.app/og-image.png',  # Update with actual image
        'twitter:card': 'summary_large_image',
        'twitter:title': f'Earthquake Analysis: {location}',
        'twitter:description': f'Found {total_quakes} earthquakes near {location}'
    }

    return metadata
