# Google Analytics Setup Guide

This guide will help you set up Google Analytics 4 tracking for your Seismic Earthquake Analyzer app.

## Prerequisites

- A Google account
- Access to [Google Analytics](https://analytics.google.com/)

## Step 1: Create a Google Analytics 4 Property

1. Go to [Google Analytics](https://analytics.google.com/)
2. Click **Admin** (gear icon in the bottom left)
3. In the **Account** column, select or create an account
4. In the **Property** column, click **Create Property**
5. Enter a property name (e.g., "Seismic Earthquake Analyzer")
6. Select your reporting time zone and currency
7. Click **Next**
8. Fill in your business details and click **Create**
9. Accept the Terms of Service

## Step 2: Set Up a Data Stream

1. After creating the property, you'll be prompted to set up a data stream
2. Select **Web** as the platform
3. Enter your website URL (or `http://localhost:8501` for local testing)
4. Enter a stream name (e.g., "Seismic App")
5. Click **Create stream**

## Step 3: Get Your Measurement ID

1. After creating the stream, you'll see your **Measurement ID** at the top of the page
2. It will look like this: `G-XXXXXXXXXX`
3. Copy this ID - you'll need it in the next step

## Step 4: Configure Your App

1. In your project directory, create the Streamlit secrets file:
```bash
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

2. Open `.streamlit/secrets.toml` in your text editor

3. Replace the placeholder with your actual Measurement ID:
```toml
GA_MEASUREMENT_ID = "G-XXXXXXXXXX"
```

4. Save the file

## Step 5: Test Your Setup

1. Start your Streamlit app:
```bash
streamlit run app.py
```

2. Open the app in your browser

3. Perform some actions (searches, exports, etc.)

4. Go back to Google Analytics and navigate to:
   - **Reports** → **Realtime** to see live activity
   - Wait a few hours, then check **Reports** → **Engagement** → **Events** to see tracked events

## Tracked Events

The app automatically tracks the following events:

### Page Views
- Automatically tracked when users visit the app

### Custom Events

| Event Name | Description | Parameters |
|------------|-------------|------------|
| `search_earthquakes` | When user clicks "Analyze Earthquakes" | `location_type`, `time_range`, `min_magnitude`, `radius_km` |
| `search_results` | When search completes successfully | `earthquakes_found`, `location`, `has_dyfi_data` |
| `export_data` | When user downloads CSV data | `format`, `location`, `num_earthquakes` |

## Viewing Your Data

### Realtime Reports
See active users and their activities in real-time:
- Go to **Reports** → **Realtime** in Google Analytics

### Event Reports
View all tracked events and their parameters:
- Go to **Reports** → **Engagement** → **Events**
- Click on any event name to see detailed parameters

### Custom Reports
Create custom reports and explorations:
- Go to **Explore** to create custom analysis
- Use dimensions like `location`, `time_range`, etc. to segment your data

## Troubleshooting

### No data appearing in Google Analytics

1. **Check your Measurement ID**: Make sure it's correctly formatted (`G-XXXXXXXXXX`)
2. **Check the secrets file**: Ensure `.streamlit/secrets.toml` exists and contains your ID
3. **Restart the app**: Stop and restart `streamlit run app.py`
4. **Wait for data**: Real-time reports update quickly, but other reports may take 24-48 hours
5. **Check browser console**: Open browser developer tools and check for any JavaScript errors

### Events not tracking

1. Make sure you're performing actions that trigger events (clicking buttons, exporting data)
2. Check that your Measurement ID is valid in Google Analytics
3. Verify the tracking code is loaded by checking the browser's Network tab for requests to `google-analytics.com`

## Privacy Considerations

- Google Analytics collects user data including IP addresses and browser information
- Make sure to add a privacy policy to your app if deploying publicly
- Consider adding a cookie consent banner for GDPR compliance
- You can anonymize IP addresses in GA4 settings if needed

## Security Notes

- **Never commit** your `.streamlit/secrets.toml` file to version control
- The file is already in `.gitignore` to prevent accidental commits
- For production deployments, use environment variables or secure secret management
- If using Streamlit Cloud, add your secrets through the Streamlit Cloud dashboard

## Advanced Configuration

### Adding More Events

To track additional events, use the `track_event()` function in your code:

```python
from src.analytics import track_event

# Track a custom event
track_event('custom_event_name', {
    'parameter1': 'value1',
    'parameter2': value2
})
```

### Disabling Analytics

To disable analytics:
1. Remove or rename `.streamlit/secrets.toml`
2. Or remove the `GA_MEASUREMENT_ID` from the file

The app will work normally without analytics if no Measurement ID is configured.

## Additional Resources

- [Google Analytics 4 Documentation](https://support.google.com/analytics/answer/10089681)
- [GA4 Event Tracking Guide](https://support.google.com/analytics/answer/9322688)
- [Streamlit Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
