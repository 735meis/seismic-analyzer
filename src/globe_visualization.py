"""
3D Globe Visualization using PyDeck for earthquake data.
"""

import pydeck as pdk
import pandas as pd
from typing import Optional


def create_3d_globe_view(df: pd.DataFrame, center_lat: float, center_lon: float) -> pdk.Deck:
    """
    Create a 3D globe visualization of earthquakes using PyDeck.

    Args:
        df: DataFrame with earthquake data (must have 'latitude', 'longitude', 'mag', 'depth')
        center_lat: Center latitude for view
        center_lon: Center longitude for view

    Returns:
        PyDeck Deck object ready for rendering
    """
    if df.empty:
        # Return empty deck if no data
        return pdk.Deck(
            map_style="mapbox://styles/mapbox/dark-v10",
            initial_view_state=pdk.ViewState(
                latitude=center_lat,
                longitude=center_lon,
                zoom=2,
                pitch=45,
            ),
            layers=[],
        )

    # Prepare data for visualization
    df = df.copy()

    # Normalize magnitude for size (multiply by 100,000 for visibility)
    df['size'] = df['magnitude'] * 100000

    # Color by depth: shallow (red) to deep (blue)
    def depth_to_color(depth):
        """Convert depth to RGB color."""
        if depth < 70:  # Shallow - Red
            return [255, 87, 51, 200]
        elif depth < 300:  # Intermediate - Orange
            return [255, 167, 38, 200]
        else:  # Deep - Blue
            return [0, 149, 255, 200]

    df['color'] = df['depth'].apply(depth_to_color)

    # Create scatterplot layer for earthquakes
    scatterplot_layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position=["longitude", "latitude"],
        get_radius="size",
        get_fill_color="color",
        pickable=True,
        opacity=0.8,
        stroked=True,
        filled=True,
        radius_scale=1,
        radius_min_pixels=3,
        radius_max_pixels=50,
        line_width_min_pixels=1,
        get_line_color=[255, 255, 255, 100],
    )

    # Create arc layer for major earthquakes (M5.0+)
    major_quakes = df[df['magnitude'] >= 5.0].copy()

    arc_layers = []
    if not major_quakes.empty:
        # Create arcs from search center to major quakes
        arc_data = []
        for _, quake in major_quakes.iterrows():
            arc_data.append({
                'start': [center_lon, center_lat],
                'end': [quake['longitude'], quake['latitude']],
                'magnitude': quake['magnitude']
            })

        arc_df = pd.DataFrame(arc_data)

        arc_layer = pdk.Layer(
            "ArcLayer",
            data=arc_df,
            get_source_position="start",
            get_target_position="end",
            get_source_color=[102, 126, 234, 100],
            get_target_color=[240, 147, 251, 150],
            get_width="magnitude",
            width_scale=0.5,
            width_min_pixels=2,
            pickable=True,
        )
        arc_layers.append(arc_layer)

    # Tooltip configuration
    tooltip = {
        "html": "<b>Magnitude:</b> {magnitude}<br/>"
                "<b>Location:</b> {place}<br/>"
                "<b>Depth:</b> {depth} km<br/>"
                "<b>Time:</b> {time}",
        "style": {
            "backgroundColor": "rgba(26, 26, 26, 0.9)",
            "color": "white",
            "fontSize": "12px",
            "padding": "10px",
            "borderRadius": "8px",
            "fontFamily": "Inter, sans-serif"
        }
    }

    # Determine if mobile device (adjust pitch)
    # Note: This is handled by the rendering context, but we'll use standard desktop view
    pitch = 45

    # Create the deck
    deck = pdk.Deck(
        map_style="mapbox://styles/mapbox/dark-v10",
        initial_view_state=pdk.ViewState(
            latitude=center_lat,
            longitude=center_lon,
            zoom=4,
            pitch=pitch,
            bearing=0,
        ),
        layers=[scatterplot_layer] + arc_layers,
        tooltip=tooltip,
    )

    return deck


def create_3d_globe_mobile(df: pd.DataFrame, center_lat: float, center_lon: float) -> pdk.Deck:
    """
    Create a mobile-optimized 3D globe visualization.

    Args:
        df: DataFrame with earthquake data
        center_lat: Center latitude for view
        center_lon: Center longitude for view

    Returns:
        PyDeck Deck object optimized for mobile
    """
    deck = create_3d_globe_view(df, center_lat, center_lon)

    # Adjust view state for mobile (lower pitch, larger touch targets)
    deck.initial_view_state.pitch = 30
    deck.initial_view_state.zoom = 3

    return deck
