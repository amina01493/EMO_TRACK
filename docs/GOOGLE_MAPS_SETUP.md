# Google Maps Integration Setup Guide

## What's Been Added

Your app now has full Google Maps integration for location tracking and safe zone management:

### Features:
- **Interactive Map**: Display child's current location and safe zones
- **Safe Zone Visualization**: Circles showing safe zone boundaries with customizable radius
- **Click-to-Set Location**: Click anywhere on the map to set safe zone coordinates
- **Geolocation**: Auto-detect user's current location
- **Safe Zone List**: View all configured safe zones with coordinates

## Setup Steps

### Step 1: Get a Google Maps API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing one)
3. Enable these APIs:
   - Maps JavaScript API
   - Geolocation API
4. Create an API key (in Credentials section)
5. (Optional) Restrict the key to your domain for security

### Step 2: Add API Key to Your App

**Option A: Environment Variable (Recommended)**
```powershell
$env:GOOGLE_MAPS_API_KEY="YOUR_API_KEY_HERE"
```

Then restart your Flask app.

**Option B: Direct Edit**
Edit `app.py` and replace the default key:
```python
app.config['GOOGLE_MAPS_API_KEY'] = 'YOUR_API_KEY_HERE'
```

### Step 3: Restart Your App

```powershell
cd "c:\Users\hp\Downloads\New folder"
& "C:\Users\hp\Downloads\New folder\.venv\Scripts\python.exe" app.py
```

## How to Use

### Adding a Safe Zone:
1. Go to child's profile → "Safe Zones & Location Tracking"
2. **Method 1**: Click 📍 button to auto-detect your location
3. **Method 2**: Click anywhere on the map to set coordinates
4. Enter zone name and adjust radius if needed
5. Click "Add Zone" button

### Map Features:
- **Blue Markers**: Show safe zone locations
- **Blue Circles**: Show safe zone radius/boundaries
- **Click to Select**: Click map to set latitude/longitude
- **Zoom/Pan**: Use mouse to navigate the map

## Sample Safe Zones (Egypt)

If you want to test with sample locations:
- **Home**: 30.0444, 31.2357 (Cairo Downtown)
- **School**: 30.0500, 31.2400 (Nasr City)
- **Club**: 30.0600, 31.2500 (Heliopolis)

## Troubleshooting

### Map not showing?
- Check that API key is correctly set
- Make sure "Maps JavaScript API" is enabled in Google Cloud Console
- Check browser console for errors (F12)

### Geolocation not working?
- HTTPS is required for geolocation (localhost works for testing)
- Browser must have permission to access location
- Requires "Geolocation API" enabled in Google Cloud Console

### API Key restrictions?
- If restricting to domain, add:
  - `http://localhost:5000`
  - `http://127.0.0.1:5000`
  - Your production domain

## Database Schema Updates

The Location model now stores:
- `name`: Zone name
- `latitude`: Decimal latitude coordinate
- `longitude`: Decimal longitude coordinate
- `radius`: Safe zone radius in meters (default: 200m)
- `created_at`: Timestamp

## Files Modified:
- `app.py`: Added Google Maps API config and updated locations route
- `templates/child_locations.html`: Complete Google Maps implementation
