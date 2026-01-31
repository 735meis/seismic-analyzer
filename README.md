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

## Project Structure

```
seismic-analyzer/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── config/
│   └── settings.py          # Configuration constants
├── src/
│   ├── geocoding.py         # Location to coordinates conversion
│   ├── usgs_api.py          # USGS API client
│   ├── data_processor.py    # Data processing and statistics
│   ├── visualizations.py    # Plotly chart generation
│   └── utils.py             # Utility functions
└── tests/
    └── __init__.py
```

## Configuration

Key settings can be modified in `config/settings.py`:

- `DEFAULT_SEARCH_RADIUS_KM`: Default search radius (500 km)
- `API_REQUEST_TIMEOUT`: API timeout in seconds (30s)
- `MAGNITUDE_CATEGORIES`: Earthquake magnitude classifications
- `DEPTH_CATEGORIES`: Depth classifications (shallow/intermediate/deep)

## Data Sources

- **Earthquake Data**: [USGS Earthquake Catalog](https://earthquake.usgs.gov/)
- **Geocoding**: Nominatim (OpenStreetMap)

## Examples

### Search by City
- Location: "San Francisco"
- Date Range: Last 30 days
- Results: All earthquakes within 500km of San Francisco

### Search by Zip Code
- Location: "94102"
- Date Range: Last year
- Min Magnitude: 4.0
- Results: Significant earthquakes near the zip code

## Features Explained

### Auto-Adjusting Time Granularity

The application automatically selects the best time interval for visualizations based on your date range:

- < 1 day → Hourly
- 1-7 days → Every 6 hours
- 1 week - 1 month → Daily
- 1-3 months → Weekly
- 3 months - 1 year → Weekly
- 1-5 years → Monthly
- \> 5 years → Yearly

### Earthquake Swarm Detection

The analyzer detects earthquake swarms - clusters of 5 or more events occurring within 10km and 24 hours of each other.

### Energy Calculations

Seismic energy is calculated using the standard formula:
```
E = 10^(1.5 × M + 4.8) joules
```

Results are displayed in TNT equivalent for easier understanding.

## Limitations

- **Rate Limits**: Nominatim geocoding is limited to 1 request/second
- **Result Limit**: USGS API returns maximum 20,000 earthquakes per query
- **Coverage**: Best coverage for seismically active regions

## Tips for Better Results

1. **No Results?**
   - Expand your date range
   - Increase search radius
   - Lower minimum magnitude
   - Try a different location

2. **Too Many Results?**
   - Narrow date range
   - Increase minimum magnitude
   - Decrease search radius

3. **Best Practices:**
   - Use specific city names (e.g., "San Francisco, CA")
   - For recent events, search within last 30-90 days
   - For historical analysis, focus on higher magnitude events

## Troubleshooting

### Geocoding Errors
- Check spelling of city name
- Try adding state/country (e.g., "Paris, France")
- Verify zip code is valid US zip

### API Timeouts
- Check internet connection
- Try again later (service may be busy)
- Reduce search parameters

### Empty Results
- Verify location is correct
- Expand date range or search radius
- Lower magnitude filter

## Development

### Running Tests
```bash
source venv/bin/activate
python test_modules.py
```

### Adding Features
The modular structure makes it easy to extend:
- Add new visualizations in `src/visualizations.py`
- Add new statistics in `src/data_processor.py`
- Modify UI in `app.py`

## License

This project uses public APIs and data sources:
- USGS data is in the public domain
- OpenStreetMap data (via Nominatim) is under ODbL license

## Acknowledgments

- USGS for providing comprehensive earthquake data
- OpenStreetMap and Nominatim for geocoding services
- Streamlit, Plotly, and Pandas communities

## Support

For issues or questions:
1. Check the troubleshooting section
2. Verify your internet connection and API access
3. Review error messages for specific guidance

## Version

1.0.0 - Initial release

---

Built with ❤️ using Streamlit and Python
