"""
Data Storytelling - Transform earthquake data into compelling narratives.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta


def generate_insight_narrative(stats: Dict) -> List[str]:
    """
    Generate natural language insights from earthquake statistics.

    Args:
        stats: Dictionary with earthquake statistics

    Returns:
        List of insight strings
    """
    insights = []

    # Temporal insights
    temporal = stats.get('temporal', {})
    avg_per_day = temporal.get('avg_per_day', 0)

    if avg_per_day > 10:
        insights.append(f"⚡ **Intense Activity:** {avg_per_day:.1f} earthquakes per day—exceptionally active region.")
    elif avg_per_day > 5:
        insights.append(f"📊 **Active Period:** {avg_per_day:.1f} earthquakes daily—above average activity.")
    elif avg_per_day < 1:
        insights.append(f"🌊 **Calm Period:** Only {avg_per_day:.2f} earthquakes per day—relatively quiet.")

    # Magnitude insights
    magnitude = stats.get('magnitude', {})
    max_mag = magnitude.get('max', 0)
    avg_mag = magnitude.get('mean', 0)

    if max_mag >= 7.0:
        insights.append(f"🚨 **Major Event:** M{max_mag:.1f} detected—could cause significant damage in populated areas.")
    elif max_mag >= 6.0:
        insights.append(f"⚠️ **Strong Event:** M{max_mag:.1f}—potentially damaging to structures.")
    elif max_mag >= 5.0:
        insights.append(f"💫 **Notable Event:** M{max_mag:.1f}—widely felt but typically minor damage.")

    if avg_mag < 3.0:
        insights.append(f"🔬 **Micro-seismicity:** Average M{avg_mag:.1f}—mostly imperceptible to humans.")
    elif avg_mag > 4.0:
        insights.append(f"📈 **Elevated Magnitude:** Average M{avg_mag:.1f}—higher than typical background levels.")

    # Depth insights
    depth = stats.get('depth', {})
    avg_depth = depth.get('mean', 0)

    if avg_depth < 70:
        insights.append(f"🌋 **Shallow Focus:** Average depth {avg_depth:.1f} km—more likely to cause damage at surface.")
    elif avg_depth > 300:
        insights.append(f"🌍 **Deep Focus:** Average depth {avg_depth:.1f} km—energy dissipates before reaching surface.")

    # Temporal clustering
    if 'swarms' in stats and stats['swarms'] > 0:
        insights.append(f"🔄 **Swarm Activity:** {stats['swarms']} earthquake swarms detected—possible volcanic or tectonic stress.")

    # Energy insights
    if 'energy' in stats:
        total_energy = stats['energy'].get('total_joules', 0)
        if total_energy > 1e15:  # Large energy release
            tnt_equiv = total_energy / 4.184e9  # Convert to tons of TNT
            insights.append(f"💥 **Energy Release:** {tnt_equiv:.1f} tons of TNT equivalent—substantial seismic energy.")

    return insights


def create_narrative_timeline(df: pd.DataFrame, time_range_days: int) -> str:
    """
    Create a narrative description of the earthquake timeline.

    Args:
        df: Earthquake DataFrame
        time_range_days: Number of days in the analysis

    Returns:
        Narrative text
    """
    if df.empty:
        return "No earthquakes recorded in this period."

    total_count = len(df)
    start_date = df['time'].min().strftime('%B %d, %Y')
    end_date = df['time'].max().strftime('%B %d, %Y')

    # Opening narrative
    narrative = f"**Over {time_range_days} days** ({start_date} to {end_date}), "

    if total_count == 1:
        narrative += "a single earthquake was recorded."
    elif total_count < 10:
        narrative += f"the earth spoke {total_count} times, each tremor telling a story of tectonic movement beneath."
    elif total_count < 50:
        narrative += f"{total_count} earthquakes rattled the region, painting a picture of active geological processes."
    else:
        narrative += f"an intense swarm of {total_count} earthquakes shook the area, signaling vigorous tectonic activity."

    return narrative


def create_community_impact_section(df: pd.DataFrame) -> str:
    """
    Generate narrative about community impact based on magnitude distribution.

    Args:
        df: Earthquake DataFrame

    Returns:
        Impact narrative
    """
    if df.empty:
        return ""

    # Count felt earthquakes (M3.0+)
    felt_count = len(df[df['magnitude'] >= 3.0])
    damaging_count = len(df[df['magnitude'] >= 5.0])
    major_count = len(df[df['magnitude'] >= 7.0])

    narratives = []

    if major_count > 0:
        narratives.append(
            f"🚨 **{major_count} major earthquake(s)** likely caused significant disruption, "
            f"with potential building damage and emergency response activated."
        )

    if damaging_count > 0:
        narratives.append(
            f"⚠️ **{damaging_count} potentially damaging event(s)** may have affected infrastructure, "
            f"especially in older or poorly constructed buildings."
        )

    if felt_count > 0:
        narratives.append(
            f"👥 **{felt_count} earthquake(s) felt by residents**, contributing to the collective experience "
            f"of living in a seismically active region."
        )
    else:
        narratives.append(
            "🔬 **All earthquakes were below human perception threshold**, detected only by sensitive instruments."
        )

    return "\n\n".join(narratives)


def create_global_context(max_mag: float, total_count: int) -> str:
    """
    Provide global context for the earthquake data.

    Args:
        max_mag: Maximum magnitude in the dataset
        total_count: Total number of earthquakes

    Returns:
        Context narrative
    """
    context_parts = []

    # Magnitude context
    if max_mag >= 8.0:
        context_parts.append(
            "🌍 **Globally Significant:** M8.0+ earthquakes occur only ~1 time per year worldwide. "
            "This is a rare and catastrophic event."
        )
    elif max_mag >= 7.0:
        context_parts.append(
            "🌍 **Major Global Event:** M7.0+ earthquakes occur ~15 times per year globally. "
            "These events make international news."
        )
    elif max_mag >= 6.0:
        context_parts.append(
            "🌎 **Regionally Notable:** M6.0+ earthquakes occur ~130 times per year worldwide. "
            "Significant at a regional scale."
        )
    elif max_mag >= 5.0:
        context_parts.append(
            "📊 **Moderate Activity:** M5.0+ earthquakes occur ~1,300 times per year globally. "
            "Part of Earth's normal seismic activity."
        )
    else:
        context_parts.append(
            "📉 **Minor Activity:** Small earthquakes like these occur millions of times per year. "
            "Most go unnoticed without instruments."
        )

    # Frequency context
    if total_count > 1000:
        context_parts.append(
            f"⚡ **Exceptional Frequency:** {total_count:,} events is extremely high, "
            "possibly indicating a swarm or volcanic activity."
        )
    elif total_count > 100:
        context_parts.append(
            f"📈 **High Activity:** {total_count} events indicates an active seismic zone "
            "or aftershock sequence."
        )

    return "\n\n".join(context_parts)


def render_storytelling_sections(df: pd.DataFrame, stats: Dict, time_range_days: int):
    """
    Render all storytelling sections with progressive disclosure.

    Args:
        df: Earthquake DataFrame
        stats: Statistics dictionary
        time_range_days: Analysis time range
    """
    if df.empty:
        st.info("No earthquake data available for storytelling analysis.")
        return

    # Section 1: Overview (auto-show)
    st.markdown("## 📍 Your Earthquake Story")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Events", stats.get('total_count', 0))
    with col2:
        max_mag = stats.get('magnitude', {}).get('max', 0)
        st.metric("Strongest", f"M{max_mag:.1f}")
    with col3:
        avg_per_day = stats.get('temporal', {}).get('avg_per_day', 0)
        st.metric("Daily Average", f"{avg_per_day:.1f}")

    # Section 2: Timeline (auto-show)
    st.markdown("### ⏰ The Timeline")
    timeline_narrative = create_narrative_timeline(df, time_range_days)
    st.markdown(timeline_narrative)

    # Section 3: AI-style insights carousel
    st.markdown("### 💡 Key Insights")
    insights = generate_insight_narrative(stats)

    for insight in insights:
        st.markdown(
            f'<div class="glass-card" style="padding: 1rem; margin: 0.75rem 0;">{insight}</div>',
            unsafe_allow_html=True
        )

    # Section 4: Patterns (expandable)
    with st.expander("🔍 **Hidden Patterns** - Click to reveal", expanded=False):
        st.markdown("#### Spatial Distribution")
        if 'depth' in stats:
            depth_mean = stats['depth'].get('mean', 0)
            depth_std = stats['depth'].get('std', 0)

            if depth_std < 10:
                st.markdown(
                    f"🎯 **Concentrated Depth:** Earthquakes clustered around {depth_mean:.1f} km depth—"
                    f"suggests a specific fault or magma chamber."
                )
            else:
                st.markdown(
                    f"📊 **Varied Depth:** Wide depth range ({depth_std:.1f} km std dev)—"
                    f"multiple seismic sources active."
                )

        st.markdown("#### Temporal Patterns")
        if 'temporal' in stats:
            # Group by hour to find peak activity times
            df_copy = df.copy()
            df_copy['hour'] = df_copy['time'].dt.hour
            hourly_counts = df_copy.groupby('hour').size()

            if not hourly_counts.empty:
                peak_hour = hourly_counts.idxmax()
                peak_count = hourly_counts.max()

                st.markdown(
                    f"⏰ **Peak Activity:** {peak_count} earthquakes occurred around {peak_hour}:00 UTC—"
                    f"though this may be coincidental."
                )

    # Section 5: Community Impact (expandable)
    with st.expander("👥 **Community Impact** - Click to reveal", expanded=False):
        impact_narrative = create_community_impact_section(df)
        st.markdown(impact_narrative)

        # Show strongest earthquake details
        if not df.empty:
            strongest = df.nlargest(1, 'magnitude').iloc[0]
            st.markdown("#### Strongest Event Details")
            st.markdown(
                f"**M{strongest['magnitude']:.1f}** - {strongest['place']}\n\n"
                f"📅 {strongest['time'].strftime('%B %d, %Y at %H:%M UTC')}\n\n"
                f"📏 Depth: {strongest['depth']:.1f} km"
            )

    # Section 6: Global Context (expandable)
    with st.expander("📊 **Global Context** - Click to reveal", expanded=False):
        max_mag = stats.get('magnitude', {}).get('max', 0)
        total_count = stats.get('total_count', 0)

        global_context = create_global_context(max_mag, total_count)
        st.markdown(global_context)

        st.markdown("#### How This Compares")
        st.markdown(
            "- **Globally**: ~50 earthquakes M5.0+ occur each week\n"
            "- **Daily**: ~8,000 earthquakes M2.0+ happen worldwide\n"
            "- **Yearly**: ~1 earthquake M8.0+ shakes the planet"
        )
