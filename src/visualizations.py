"""
Visualization functions using Plotly for interactive charts.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import timezone
import math
from config.settings import (
    CHART_HEIGHT,
    MAGNITUDE_COLOR_SCALE,
    OCCURRENCE_COLOR_SCALE,
    MAGNITUDE_CATEGORIES,
    DEPTH_CATEGORIES
)


def create_timeline_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create an interactive scatter plot showing earthquake timeline.

    Args:
        df: DataFrame with earthquake data

    Returns:
        go.Figure: Plotly figure object
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig

    # Create hover text
    hover_text = df.apply(
        lambda row: f"<b>{row['place']}</b><br>" +
                   f"Time: {row['time'].strftime('%Y-%m-%d %H:%M:%S')}<br>" +
                   f"Magnitude: {row['magnitude']:.1f}<br>" +
                   f"Depth: {row['depth']:.1f} km",
        axis=1
    )

    # Create scatter plot
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['time'],
        y=df['magnitude'],
        mode='markers',
        marker=dict(
            size=(df['magnitude'] + 2) * 3,  # Scale size by magnitude, offset to ensure positive values
            color=df['magnitude'],
            colorscale=MAGNITUDE_COLOR_SCALE,
            showscale=True,
            colorbar=dict(title="Magnitude"),
            line=dict(width=0.5, color='white')
        ),
        text=hover_text,
        hovertemplate='%{text}<extra></extra>',
        name='Earthquakes'
    ))

    # Add reference lines
    fig.add_hline(y=3.0, line_dash="dash", line_color="gray",
                  annotation_text="M 3.0 (Feelable)", annotation_position="right")
    fig.add_hline(y=5.0, line_dash="dash", line_color="orange",
                  annotation_text="M 5.0 (Damaging)", annotation_position="right")
    fig.add_hline(y=7.0, line_dash="dash", line_color="red",
                  annotation_text="M 7.0 (Major)", annotation_position="right")

    # Update layout
    fig.update_layout(
        title="Earthquake Timeline",
        xaxis_title="Time",
        yaxis_title="Magnitude",
        height=CHART_HEIGHT,
        hovermode='closest',
        showlegend=False,
        template='plotly_white'
    )

    return fig


def create_occurrence_bar_chart(df: pd.DataFrame, interval: str, interval_label: str) -> go.Figure:
    """
    Create a bar chart showing earthquake occurrences over time.

    Args:
        df: Aggregated DataFrame with time bins and counts
        interval: Pandas frequency string
        interval_label: Human-readable interval label

    Returns:
        go.Figure: Plotly figure object
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig

    # Create hover text with date range
    if interval in ['H', '6H']:
        hover_text = df['time'].dt.strftime('%Y-%m-%d %H:%M')
    elif interval == 'D':
        hover_text = df['time'].dt.strftime('%Y-%m-%d')
    elif interval == 'W':
        hover_text = df['time'].dt.strftime('Week of %Y-%m-%d')
    elif interval == 'M':
        hover_text = df['time'].dt.strftime('%B %Y')
    else:  # Y
        hover_text = df['time'].dt.strftime('%Y')

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df['time'],
        y=df['count'],
        marker=dict(
            color=df['count'],
            colorscale=OCCURRENCE_COLOR_SCALE,
            showscale=True,
            colorbar=dict(title="Count")
        ),
        hovertemplate='<b>%{text}</b><br>Count: %{y}<extra></extra>',
        text=hover_text,
        name='Earthquakes'
    ))

    # Update layout
    fig.update_layout(
        title=f"Earthquake Occurrences Over Time ({interval_label})",
        xaxis_title="Time",
        yaxis_title="Number of Earthquakes",
        height=CHART_HEIGHT,
        showlegend=False,
        template='plotly_white'
    )

    return fig


def create_magnitude_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create a bar chart showing magnitude distribution.

    Args:
        df: DataFrame with earthquake data

    Returns:
        go.Figure: Plotly figure object
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig

    # Count by category
    mag_counts = df['magnitude_category'].value_counts()

    # Order by magnitude categories
    category_order = list(MAGNITUDE_CATEGORIES.keys())
    mag_counts = mag_counts.reindex([cat for cat in category_order if cat in mag_counts.index])

    # Create color scale
    colors = px.colors.sequential.Reds[2:]
    if len(colors) < len(mag_counts):
        colors = colors * (len(mag_counts) // len(colors) + 1)
    colors = colors[:len(mag_counts)]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=mag_counts.index,
        y=mag_counts.values,
        marker=dict(
            color=colors,
            line=dict(width=1, color='white')
        ),
        text=mag_counts.values,
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>'
    ))

    # Update layout
    fig.update_layout(
        title="Magnitude Distribution",
        xaxis_title="Magnitude Category",
        yaxis_title="Count",
        height=400,
        showlegend=False,
        template='plotly_white'
    )

    return fig


def create_depth_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create a bar chart showing depth distribution.

    Args:
        df: DataFrame with earthquake data

    Returns:
        go.Figure: Plotly figure object
    """
    if df.empty or df['depth'].isna().all():
        fig = go.Figure()
        fig.add_annotation(
            text="No depth data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig

    # Categorize depths
    def categorize_depth(depth):
        if pd.isna(depth):
            return None
        for category, (min_d, max_d) in DEPTH_CATEGORIES.items():
            if min_d <= depth < max_d:
                return category
        return "Deep"

    depth_cats = df['depth'].apply(categorize_depth)
    depth_counts = depth_cats.value_counts()

    # Order by depth categories
    category_order = list(DEPTH_CATEGORIES.keys())
    depth_counts = depth_counts.reindex([cat for cat in category_order if cat in depth_counts.index])

    # Create colors
    colors = ['#4575b4', '#fdae61', '#d73027'][:len(depth_counts)]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=depth_counts.index,
        y=depth_counts.values,
        marker=dict(
            color=colors,
            line=dict(width=1, color='white')
        ),
        text=depth_counts.values,
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>'
    ))

    # Update layout
    fig.update_layout(
        title="Depth Distribution",
        xaxis_title="Depth Category",
        yaxis_title="Count",
        height=400,
        showlegend=False,
        template='plotly_white'
    )

    return fig


def create_magnitude_vs_depth_scatter(df: pd.DataFrame) -> go.Figure:
    """
    Create a scatter plot showing magnitude vs depth relationship.

    Args:
        df: DataFrame with earthquake data

    Returns:
        go.Figure: Plotly figure object
    """
    if df.empty or df['depth'].isna().all():
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig

    # Filter out rows with missing data
    plot_df = df.dropna(subset=['magnitude', 'depth'])

    if plot_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No complete data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=plot_df['depth'],
        y=plot_df['magnitude'],
        mode='markers',
        marker=dict(
            size=8,
            color=plot_df['magnitude'],
            colorscale=MAGNITUDE_COLOR_SCALE,
            showscale=True,
            colorbar=dict(title="Magnitude"),
            opacity=0.6,
            line=dict(width=0.5, color='white')
        ),
        hovertemplate='<b>Depth:</b> %{x:.1f} km<br>' +
                     '<b>Magnitude:</b> %{y:.1f}<extra></extra>',
        name='Earthquakes'
    ))

    # Update layout
    fig.update_layout(
        title="Magnitude vs Depth",
        xaxis_title="Depth (km)",
        yaxis_title="Magnitude",
        height=400,
        showlegend=False,
        template='plotly_white'
    )

    # Reverse x-axis to show shallow earthquakes on left
    fig.update_xaxes(autorange="reversed")

    return fig


def calculate_zoom_level(radius_km: float) -> float:
    """
    Calculate appropriate map zoom level based on search radius.

    Args:
        radius_km: Search radius in kilometers

    Returns:
        float: Zoom level for the map (higher = more zoomed in)
    """
    # Formula to approximate zoom level based on radius
    # This is calibrated for Mapbox zoom levels (0-22)
    if radius_km <= 10:
        return 11
    elif radius_km <= 25:
        return 10
    elif radius_km <= 50:
        return 9
    elif radius_km <= 100:
        return 8
    elif radius_km <= 250:
        return 7
    elif radius_km <= 500:
        return 6
    elif radius_km <= 1000:
        return 5
    elif radius_km <= 2000:
        return 4
    else:
        return 3


def create_earthquake_map(
    df: pd.DataFrame,
    center_lat: float,
    center_lon: float,
    radius_km: float
) -> go.Figure:
    """
    Create an interactive map showing earthquake locations.

    Args:
        df: DataFrame with earthquake data
        center_lat: Latitude of search center
        center_lon: Longitude of search center
        radius_km: Search radius in kilometers

    Returns:
        go.Figure: Plotly figure object with map
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No earthquake data to display",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig

    # Create hover text with detailed information
    hover_text = []
    for _, row in df.iterrows():
        # Format time in GMT
        time_gmt = row['time'].strftime('%Y-%m-%d %H:%M:%S GMT')

        # Try to get local time (using UTC offset if available, otherwise just show GMT)
        # Note: For simplicity, we'll show GMT time. Full timezone conversion would require
        # additional libraries or API calls for timezone lookup by coordinates
        time_local = time_gmt  # Could be enhanced with timezone conversion

        text = (
            f"<b>{row['place']}</b><br>"
            f"<b>Magnitude:</b> M {row['magnitude']:.1f}<br>"
            f"<b>Time (GMT):</b> {time_gmt}<br>"
            f"<b>Coordinates:</b> {row['latitude']:.4f}, {row['longitude']:.4f}<br>"
            f"<b>Depth:</b> {row['depth']:.1f} km"
        )
        hover_text.append(text)

    # Calculate zoom level
    zoom = calculate_zoom_level(radius_km)

    # Create the map
    fig = go.Figure()

    # Add earthquake markers
    # Scale marker size proportionally to magnitude: larger earthquakes = larger markers
    # Using exponential scaling for better visual distinction
    marker_sizes = df['magnitude'].apply(lambda m: 8 + (m ** 1.5) * 2)

    # Create custom colors: purple for magnitude < 2, red scale for >= 2
    # This provides better contrast for small earthquakes
    marker_colors = []
    for mag in df['magnitude']:
        if mag < 2.0:
            # Purple color for low magnitude earthquakes (better visibility)
            marker_colors.append('#8B00FF')  # Dark purple
        else:
            # Red scale for higher magnitudes
            # Map magnitude 2-8 to red intensity
            normalized = min((mag - 2.0) / 6.0, 1.0)  # Normalize 2-8 to 0-1
            # Interpolate from light red to dark red
            red_intensity = int(139 + normalized * (220 - 139))  # 139 to 220
            marker_colors.append(f'rgb({red_intensity}, 0, 0)')

    fig.add_trace(go.Scattermapbox(
        lat=df['latitude'],
        lon=df['longitude'],
        mode='markers',
        marker=dict(
            size=marker_sizes,
            color=marker_colors,
            showscale=False,  # Disable automatic colorscale since we're using custom colors
            opacity=1.0,
            sizemode='diameter'
        ),
        text=hover_text,
        hovertemplate='%{text}<extra></extra>',
        name='Earthquakes'
    ))

    # Add legend entries for color scheme
    # Purple for magnitude < 2
    fig.add_trace(go.Scattermapbox(
        lat=[None],
        lon=[None],
        mode='markers',
        marker=dict(size=10, color='#8B00FF'),
        name='M < 2.0',
        showlegend=True
    ))

    # Red for magnitude >= 2
    fig.add_trace(go.Scattermapbox(
        lat=[None],
        lon=[None],
        mode='markers',
        marker=dict(size=10, color='rgb(180, 0, 0)'),
        name='M ≥ 2.0',
        showlegend=True
    ))

    # Add center point marker
    fig.add_trace(go.Scattermapbox(
        lat=[center_lat],
        lon=[center_lon],
        mode='markers',
        marker=dict(
            size=15,
            color='blue',
            symbol='circle',
            opacity=0.7
        ),
        text=[f"<b>Search Center</b><br>Lat: {center_lat:.4f}<br>Lon: {center_lon:.4f}<br>Radius: {radius_km} km"],
        hovertemplate='%{text}<extra></extra>',
        name='Search Center',
        showlegend=True
    ))

    # Update map layout
    fig.update_layout(
        title="Earthquake Map View",
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=zoom
        ),
        height=600,
        showlegend=True,
        hovermode='closest',
        margin=dict(l=0, r=0, t=40, b=0)
    )

    return fig


def create_dyfi_visualization(df: pd.DataFrame) -> go.Figure:
    """
    Create an engaging visualization for DYFI (Did You Feel It?) community data.

    Args:
        df: DataFrame with earthquake data including CDI and felt columns

    Returns:
        go.Figure: Plotly figure object
    """
    # Filter for earthquakes with DYFI data
    dyfi_df = df[(df['cdi'].notna()) | (df['felt'].notna())].copy()

    if dyfi_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No community-reported data available for these earthquakes",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            height=300,
            template='plotly_white'
        )
        return fig

    # Sort by felt reports (descending)
    dyfi_df = dyfi_df.sort_values('felt', ascending=False).head(15)  # Top 15

    # Create hover text
    hover_text = dyfi_df.apply(
        lambda row: (
            f"<b>{row['place']}</b><br>"
            f"Magnitude: M {row['magnitude']:.1f}<br>"
            f"Felt Reports: {int(row['felt']) if pd.notna(row['felt']) else 0}<br>"
            f"Community Intensity: {row['cdi']:.1f} CDI" if pd.notna(row['cdi']) else ""
        ),
        axis=1
    )

    fig = go.Figure()

    # Add bar chart for felt reports
    fig.add_trace(go.Bar(
        x=dyfi_df['felt'],
        y=dyfi_df['place'].str[:50],  # Truncate long place names
        orientation='h',
        marker=dict(
            color=dyfi_df['cdi'] if 'cdi' in dyfi_df.columns else dyfi_df['magnitude'],
            colorscale='YlOrRd',
            showscale=True,
            colorbar=dict(
                title="CDI",
                x=1.15
            ),
            line=dict(width=1, color='white')
        ),
        text=hover_text,
        hovertemplate='%{text}<extra></extra>',
        name='Felt Reports'
    ))

    # Update layout
    fig.update_layout(
        title="Top Community-Reported Earthquakes",
        xaxis_title="Number of 'Felt It' Reports",
        yaxis_title="",
        height=max(400, len(dyfi_df) * 30),
        showlegend=False,
        template='plotly_white',
        yaxis=dict(autorange="reversed")
    )

    return fig


def get_intensity_description(cdi: float) -> str:
    """
    Get the Modified Mercalli Intensity description for a given CDI value.

    Args:
        cdi: Community Decimal Intensity value

    Returns:
        str: Description of the intensity level
    """
    if pd.isna(cdi):
        return "Not reported"

    if cdi < 1:
        return "Not felt"
    elif cdi < 2:
        return "Weak - Not felt except by very few"
    elif cdi < 3:
        return "Weak - Felt by few people at rest"
    elif cdi < 4:
        return "Weak - Felt indoors by many"
    elif cdi < 5:
        return "Light - Felt by most, some awakened"
    elif cdi < 6:
        return "Moderate - Felt by all, many frightened"
    elif cdi < 7:
        return "Strong - Everyone runs outdoors"
    elif cdi < 8:
        return "Severe - Damage to buildings"
    elif cdi < 9:
        return "Violent - General panic"
    elif cdi < 10:
        return "Extreme - Most buildings destroyed"
    else:
        return "Catastrophic - Total destruction"
