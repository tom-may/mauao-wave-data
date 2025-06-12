# Mauao Wave Data System

Complete wave monitoring solution for Garmin devices with automated data scraping.

## 🌊 System Components

### 1. Data Scraper (`/scraper/`)
- **Python script** that scrapes Port Tauranga wave conditions
- **Automated** via GitHub Actions every 30 minutes (5 AM - 9 PM NZDT)
- **Hosted data** at: `https://tom-may.github.io/mauao-wave-data/wave_data.json`

### 2. Garmin Connect IQ App (`/garmin-app/`)
- **Widget/App** for Garmin watches
- **Fetches data** from the hosted JSON API
- **Displays** wave height, wind conditions, and more

### 3. Generated Data Files
- `wave_data.json` - API endpoint for Garmin app
- `index.html` - Human-readable web view
- `portDataScrape.txt` - Raw extracted text

## 🔗 Live Data
- **JSON API**: https://tom-may.github.io/mauao-wave-data/wave_data.json
- **Web View**: https://tom-may.github.io/mauao-wave-data/

## 🛠️ Development

### Scraper Development
```bash
cd scraper
python portScrape.py
```

### Garmin App Development
```bash
cd garmin-app
connectiq
# Use Connect IQ SDK tools
```

## 📱 Installation
1. Install the Garmin app from Connect IQ Store (when published)
2. Data updates automatically every 30 minutes
3. No additional setup required

## 📊 Data Format
```json
{
  "timestamp": "2024-12-12T10:30:00.000Z",
  "location": "Mauao Wave Buoy",
  "status": "success",
  "data_quality": "complete",
  "parsed_data": {
    "conditions": {
      "max_wave_height": 1.2,
      "sig_wave_height": 0.8,
      "wind_speed": 15,
      "wind_direction": "SW"
    }
  }
}
```
