"""
Quick test script to verify core functionality.
"""

from datetime import datetime, timedelta
from src.utils import (
    determine_time_granularity,
    calculate_energy_joules,
    magnitude_category,
    format_energy_display
)

print("Testing utility functions...")

# Test time granularity
start = datetime(2024, 1, 1, 0, 0)
end = datetime(2024, 1, 1, 12, 0)
interval, label = determine_time_granularity(start, end)
print(f"✓ 12 hour range: {interval} ({label})")
assert interval == 'H', "Expected hourly for less than 1 day"

start = datetime(2024, 1, 1)
end = datetime(2024, 1, 31)
interval, label = determine_time_granularity(start, end)
print(f"✓ 1 month range: {interval} ({label})")
assert interval == 'D', "Expected daily for 1 month"

start = datetime(2024, 1, 1)
end = datetime(2024, 12, 31)
interval, label = determine_time_granularity(start, end)
print(f"✓ 1 year range: {interval} ({label})")
assert interval == 'W', "Expected weekly for 1 year"

# Test energy calculation
energy = calculate_energy_joules(5.0)
print(f"✓ Energy for M 5.0: {format_energy_display(energy)}")
assert energy > 0, "Energy should be positive"

# Test magnitude categorization
category = magnitude_category(4.5)
print(f"✓ M 4.5 category: {category}")
assert category == "Light", "M 4.5 should be Light"

category = magnitude_category(6.5)
print(f"✓ M 6.5 category: {category}")
assert category == "Strong", "M 6.5 should be Strong"

print("\n✅ All utility function tests passed!")

# Test configuration loading
print("\nTesting configuration...")
from config.settings import USGS_API_BASE_URL, DEFAULT_SEARCH_RADIUS_KM
print(f"✓ USGS API URL: {USGS_API_BASE_URL}")
print(f"✓ Default radius: {DEFAULT_SEARCH_RADIUS_KM} km")

print("\n✅ All tests passed successfully!")
