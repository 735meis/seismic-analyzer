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

    # Initialize Google Analytics tracking
    inject_ga_tracking()

    # Header
    st.title("🌍 Seismic Earthquake Analyzer")
    st.markdown("""
    Analyze earthquake data from the USGS (United States Geological Survey) database.
    Search by location and time range to visualize patterns and statistics.
    """)

    # Sidebar - Input Controls
    with st.sidebar:
        st.header("Search Parameters")

        # Location input
        st.subheader("📍 Location")
        location_type = st.radio(
            "Select location type:",
            ["City Name", "Zip Code"],
            help="Choose whether to search by city name or US zip code"
        )

        is_zipcode = location_type == "Zip Code"
        location = st.text_input(
            "Enter location:",
            value="San Ramon" if not is_zipcode else "",
            placeholder="San Francisco" if not is_zipcode else "94102",
            help="Enter a city name (e.g., San Francisco) or US zip code (e.g., 94102)"
        )

        # Date range
        st.subheader("📅 Date Range")

        # Time range selection
        time_range_option = st.selectbox(
            "Select time range:",
            options=[
                "Today",
                "Last 15 minutes",
                "Last 30 minutes",
                "Last 1 hour",
                "Last 12 hours",
                "Custom date range"
            ],
            index=0,  # Default to "Today"
            help="Choose a preset time range or select custom dates"
        )

        # Calculate datetime based on selection
        if time_range_option == "Custom date range":
            # Show date pickers for custom range
            col1, col2 = st.columns(2)

            with col1:
                # Default to 30 days ago
                default_start = datetime.now() - timedelta(days=30)
                start_date = st.date_input(
                    "Start Date",
                    value=default_start,
                    max_value=datetime.now().date(),
                    help="Starting date for earthquake search"
                )

            with col2:
                end_date = st.date_input(
                    "End Date",
                    value=datetime.now() - timedelta(days=1),
                    max_value=datetime.now().date(),
                    help="Ending date for earthquake search"
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

        # Optional filters
        st.subheader("⚙️ Optional Filters")

        min_magnitude = st.number_input(
            "Minimum Magnitude",
            min_value=0.0,
            max_value=10.0,
            value=1.0,
            step=0.1,
            help="Filter earthquakes by minimum magnitude (0 = no filter)"
        )

        radius_km = st.number_input(
            "Search Radius (km)",
            min_value=10,
            max_value=5000,
            value=DEFAULT_SEARCH_RADIUS_KM,
            step=50,
            help="Radius around the location to search for earthquakes"
        )

        # Submit button
        analyze_button = st.button("🔍 Analyze Earthquakes", type="primary", use_container_width=True)

    # Main area - Results
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

            # Display results
            st.success(f"✅ Analysis complete! Found {len(df)} earthquakes.")

            # Track successful search with results
            track_event('search_results', {
                'earthquakes_found': len(df),
                'location': location,
                'has_dyfi_data': not df[(df['cdi'].notna()) | (df['felt'].notna())].empty
            })

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

            # Map View
            st.subheader("🗺️ Earthquake Map View")
            st.info(f"Interactive map showing earthquake locations. Purple dots indicate magnitude < 2.0, red dots indicate magnitude ≥ 2.0. Larger markers indicate higher magnitudes. Click on markers for details.")
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
                    st.metric("👋 Total 'Felt It' Reports", f"{total_felt_reports:,}")
                with col2:
                    st.metric("📊 Earthquakes Reported", earthquakes_with_reports)
                with col3:
                    if avg_cdi:
                        st.metric("🎯 Avg Community Intensity", f"{avg_cdi:.1f} CDI")
                    else:
                        st.metric("🎯 Avg Community Intensity", "N/A")

                st.markdown("""
                <div style='background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin: 10px 0;'>
                    <b>📱 About DYFI (Did You Feel It?)</b><br>
                    Community members report earthquake experiences through USGS's "Did You Feel It?" system.
                    CDI (Community Decimal Intensity) measures how strongly people felt the earthquake, on a scale of 1-10.
                </div>
                """, unsafe_allow_html=True)

                # Visualization
                dyfi_fig = create_dyfi_visualization(df)
                st.plotly_chart(dyfi_fig, use_container_width=True)

                # Show top felt earthquakes details
                if len(dyfi_data) > 0:
                    with st.expander("📋 Top Community-Reported Earthquakes Details"):
                        top_dyfi = dyfi_data.nlargest(5, 'felt', keep='all')

                        for idx, row in top_dyfi.iterrows():
                            cdi_desc = get_intensity_description(row['cdi']) if pd.notna(row['cdi']) else "Not reported"
                            felt_count = int(row['felt']) if pd.notna(row['felt']) else 0
                            cdi_value = f"{row['cdi']:.1f}" if pd.notna(row['cdi']) else "N/A"

                            st.markdown(f"""
                            **{row['place']}**
                            - 🎯 Magnitude: M {row['magnitude']:.1f}
                            - 👥 Felt by: {felt_count:,} people
                            - 📊 Community Intensity: {cdi_value} CDI - {cdi_desc}
                            - 🕐 Time: {row['time'].strftime('%Y-%m-%d %H:%M:%S')}
                            """)
                            st.markdown("---")
            else:
                st.info("💡 No community-reported data available for these earthquakes. DYFI reports are typically available for larger or more widely-felt earthquakes.")

            st.markdown("---")

            # Timeline Chart
            st.subheader("📈 Earthquake Timeline")
            st.info(f"Showing magnitude over time. Each point represents one earthquake.")
            timeline_fig = create_timeline_chart(df)
            st.plotly_chart(timeline_fig, use_container_width=True)

            st.markdown("---")

            # Occurrence Bar Chart
            st.subheader("📊 Earthquake Occurrences")
            st.info(f"Time granularity: {interval_label}")
            occurrence_fig = create_occurrence_bar_chart(aggregated_df, interval, interval_label)
            st.plotly_chart(occurrence_fig, use_container_width=True)

            st.markdown("---")

            # Distribution Charts
            st.subheader("📊 Distributions")
            col1, col2 = st.columns(2)

            with col1:
                mag_dist_fig = create_magnitude_distribution_chart(df)
                st.plotly_chart(mag_dist_fig, use_container_width=True)

            with col2:
                depth_dist_fig = create_depth_distribution_chart(df)
                st.plotly_chart(depth_dist_fig, use_container_width=True)

            # Magnitude vs Depth scatter
            st.subheader("🔍 Magnitude vs Depth Analysis")
            mag_depth_fig = create_magnitude_vs_depth_scatter(df)
            st.plotly_chart(mag_depth_fig, use_container_width=True)

            st.markdown("---")

            # Statistics Section
            st.subheader("📊 Detailed Statistics")
            format_statistics_display(stats, location)

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

        except Exception as e:
            st.error(f"❌ An unexpected error occurred: {str(e)}")
            st.info("Please try again or contact support if the problem persists.")

    else:
        # Show instructions when no search has been performed
        st.info("👈 Enter search parameters in the sidebar and click 'Analyze Earthquakes' to begin.")

        st.markdown("""
        ### How to Use

        1. **Choose Location Type:** Select whether you want to search by city name or zip code
        2. **Enter Location:** Type in your city name (e.g., "Los Angeles") or US zip code (e.g., "90001")
        3. **Select Date Range:** Choose start and end dates for your search
        4. **Optional Filters:**
           - Set a minimum magnitude to focus on larger earthquakes
           - Adjust the search radius around your location
        5. **Click Analyze:** Press the button to fetch and analyze earthquake data

        ### About the Data

        - Data source: [USGS Earthquake Catalog](https://earthquake.usgs.gov/)
        - Real-time earthquake information from around the world
        - Includes magnitude, location, depth, and timing for each event
        - Updated continuously by the USGS

        ### Features

        - **Interactive Timeline:** See when earthquakes occurred and their magnitudes
        - **Occurrence Analysis:** Understand patterns over time with auto-adjusted granularity
        - **Statistical Insights:** Get detailed statistics about magnitude, depth, and energy
        - **Earthquake Swarms:** Detect clusters of seismic activity
        - **Export Data:** Download your results as CSV for further analysis
        """)

        # Footer
        st.markdown("---")
        st.markdown(
            """
            <div style='text-align: center'>
                <p>Built with Streamlit | Data from USGS | Geocoding by Nominatim</p>
            </div>
            """,
            unsafe_allow_html=True
        )


if __name__ == "__main__":
    main()
