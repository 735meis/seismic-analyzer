"""
Configuration settings for the Seismic Earthquake Analyzer application.
"""

# USGS API Configuration
USGS_API_BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
DEFAULT_SEARCH_RADIUS_KM = 500
API_REQUEST_TIMEOUT = 30
API_MAX_RETRIES = 3
API_RESULT_LIMIT = 20000

# Geocoding Configuration
GEOCODING_USER_AGENT = "seismic-earthquake-analyzer/1.0"
GEOCODING_TIMEOUT = 10
GEOCODING_RATE_LIMIT = 1.0  # seconds between requests

# Visualization Settings
CHART_HEIGHT = 500
CHART_WIDTH = 800
MAGNITUDE_COLOR_SCALE = "Reds"
OCCURRENCE_COLOR_SCALE = "Purples"

# Magnitude Categories
MAGNITUDE_CATEGORIES = {
    "Micro": (0, 3),
    "Minor": (3, 4),
    "Light": (4, 5),
    "Moderate": (5, 6),
    "Strong": (6, 7),
    "Major": (7, 8),
    "Great": (8, 10)
}

# Depth Categories (in km)
DEPTH_CATEGORIES = {
    "Shallow": (0, 70),
    "Intermediate": (70, 300),
    "Deep": (300, 1000)
}

# Energy Calculation Constants
SEISMIC_ENERGY_CONSTANT_A = 1.5
SEISMIC_ENERGY_CONSTANT_B = 4.8

# Thresholds
FEELABLE_MAGNITUDE_THRESHOLD = 3.0
DAMAGING_MAGNITUDE_THRESHOLD = 5.0
SWARM_MIN_EVENTS = 5
SWARM_DISTANCE_KM = 10
SWARM_TIME_HOURS = 24
