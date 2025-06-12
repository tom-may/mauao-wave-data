Mauao Wave Data Scraper
Automated wave buoy data scraping system for Garmin Connect IQ widgets using GitHub Actions and Pages.

🌊 What This Does
This system automatically:

Scrapes wave condition data from Port Tauranga's harbour conditions page every 30 minutes (5 AM - 9 PM NZDT)
Extracts text from weather condition images using EasyOCR
Converts data to JSON format for easy consumption by Garmin widgets
Hosts the data on GitHub Pages for free access
📊 Data Output
The system generates three files:

1. wave_data.json - For Garmin Widget
2. index.html - Web View
Human-readable webpage showing current conditions

3. portDataScrape.txt - Raw Text Output
Plain text format of extracted data

🔗 Access Your Data
JSON API: https://tom-may.github.io/mauao-wave-data/wave_data.json
Web View: https://tom-may.github.io/mauao-wave-data/
Raw Text: https://tom-may.github.io/mauao-wave-data/portDataScrape.txt
⚙️ Current Configuration
Update Frequency: Every 30 minutes
Active Hours: 5 AM - 9 PM NZDT (17 hours/day)
Monthly Usage: ~1,020 GitHub Actions minutes (well within 2000 free limit)
Updates Per Day: 34
🚀 Next Steps for Garmin Widget
1. Set Up Connect IQ Development
Install Connect IQ SDK
Set up your development environment
Create a new widget project
2. Fetch Data in Your Widget
3. Widget Development Tips
Cache the last successful data locally
Handle network errors gracefully
Update data every 30-60 minutes (matching your scraper frequency)
Display last updated timestamp to users
🛠️ Maintenance & Monitoring
Check System Health
Monitor the Actions tab for any failed runs
Workflows automatically retry on failure
Email notifications for persistent failures
Usage Monitoring
Check GitHub Actions usage: Settings → Billing → Usage this month
Current configuration uses ~1,020 minutes/month of 2000 free limit
Troubleshooting
If scraping fails: Check if the source website has changed
If JSON is malformed: Check the latest workflow run logs
If data is stale: Verify the cron schedule is correct
📈 Optimization Options
Increase Frequency (if needed)
Extend Hours
Reduce Frequency
🔧 Files in This Repository
portScrape.py - Main scraping script
.github/workflows/scrape.yml - GitHub Actions workflow
wave_data.json - Latest JSON output (auto-generated)
index.html - Web view (auto-generated)
portDataScrape.txt - Raw text output (auto-generated)
💡 Key Benefits
✅ Completely Free - Uses GitHub's free tier
✅ Automatic - No manual intervention required
✅ Reliable - GitHub's infrastructure handles uptime
✅ Scalable - Easy to modify frequency or add features
✅ API Ready - JSON format perfect for Garmin widgets

🆘 Support
GitHub Issues: Create an issue in this repository
Workflow Logs: Check Actions tab for detailed error information
Connect IQ Documentation: Garmin Developer Portal
Your wave data is now automatically available 24/7 for your Garmin widget! 🌊⌚
