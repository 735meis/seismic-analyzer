# 🌍 Seismic Earthquake Analyzer

A Python web application that analyzes earthquake data from the USGS API, allowing users to search by location and time range, then visualize and analyze the results with interactive charts and comprehensive statistics.

## Features

- **Location Search**: Search by city name or US zip code
- **Flexible Date Ranges**: Analyze earthquakes across any time period
- **Interactive Visualizations**:
  - Timeline scatter plot showing magnitude over time
  - Occurrence bar charts with auto-adjusted time granularity
  - Magnitude and depth distribution charts
  - Magnitude vs depth correlation analysis
- **Comprehensive Statistics**:
  - Magnitude statistics (average, max, min, distribution)
  - Temporal patterns (most active periods, quiet periods)
  - Depth analysis
  - Seismic energy calculations
  - Earthquake swarm detection
- **Data Export**: Download results as CSV

## Tech Stack

- **Streamlit**: Web application framework
- **Plotly**: Interactive data visualizations
- **Pandas**: Data processing and analysis
- **Requests**: HTTP client for USGS API
- **Geopy**: Geocoding (city/zip to coordinates)

## Installation

1. Clone or download this repository

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Streamlit application:
```bash
streamlit run app.py
```

2. Open your browser to the URL shown (typically http://localhost:8501)

3. Use the application:
   - Select location type (City Name or Zip Code)
   - Enter your location
   - Choose date range
   - Optionally set minimum magnitude and search radius
   - Click "Analyze Earthquakes"


## Acknowledgments

- USGS for providing comprehensive earthquake data
- OpenStreetMap and Nominatim for geocoding services
- Streamlit, Plotly, and Pandas communities

