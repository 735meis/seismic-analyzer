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

    st.markdown("### 📤 Share Your Discovery")

    # Create three columns for share buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <a href="{twitter_url}" target="_blank" style="text-decoration: none;">
                <div class="glass-card" style="
                    padding: 1rem;
                    text-align: center;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    border: 1px solid rgba(29, 161, 242, 0.3);
                ">
                    <div style="font-size: 2rem;">𝕏</div>
                    <div style="font-size: 0.875rem; font-weight: 600; margin-top: 0.5rem;">
                        Twitter
                    </div>
                </div>
            </a>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <a href="{facebook_url}" target="_blank" style="text-decoration: none;">
                <div class="glass-card" style="
                    padding: 1rem;
                    text-align: center;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    border: 1px solid rgba(24, 119, 242, 0.3);
                ">
                    <div style="font-size: 2rem;">📘</div>
                    <div style="font-size: 0.875rem; font-weight: 600; margin-top: 0.5rem;">
                        Facebook
                    </div>
                </div>
            </a>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <a href="{linkedin_url}" target="_blank" style="text-decoration: none;">
                <div class="glass-card" style="
                    padding: 1rem;
                    text-align: center;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    border: 1px solid rgba(0, 119, 181, 0.3);
                ">
                    <div style="font-size: 2rem;">💼</div>
                    <div style="font-size: 0.875rem; font-weight: 600; margin-top: 0.5rem;">
                        LinkedIn
                    </div>
                </div>
            </a>
            """,
            unsafe_allow_html=True
        )

    # Web Share API for mobile (with fallback)
    st.markdown(
        """
        <script>
        async function shareContent() {
            if (navigator.share) {
                try {
                    await navigator.share({
                        title: 'Seismic Earthquake Analysis',
                        text: '%s',
                        url: '%s'
                    });
                } catch (err) {
                    console.log('Share cancelled or failed');
                }
            } else {
                // Fallback: copy to clipboard
                navigator.clipboard.writeText('%s %s');
                alert('Share link copied to clipboard!');
            }
        }
        </script>
        """ % (share_text, app_url, share_text, app_url),
        unsafe_allow_html=True
    )

    # Mobile share button
    st.markdown(
        """
        <div style="text-align: center; margin-top: 1rem;">
            <button onclick="shareContent()" class="glass-card" style="
                padding: 0.75rem 1.5rem;
                border: 1px solid rgba(102, 126, 234, 0.3);
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 12px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
            ">
                📱 Share on Mobile
            </button>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Shareable summary box
    st.markdown("**Share Summary**")
    st.info(share_text)


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
