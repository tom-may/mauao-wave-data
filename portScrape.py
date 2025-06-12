# ########################################################################
# TO RUN THIS FILE:
# 1. Open GIT BASH. Navigate to the folder containing this file.
# 2. Run the following command: python portScrape.py

import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import os
import cv2
import numpy as np
import easyocr
import sys
import json
import re
from datetime import datetime

# Set default encoding to utf-8
sys.stdout.reconfigure(encoding='utf-8')

def parse_wave_conditions(conditions_list):
    """Parse conditions list into structured data with validation"""
    
    parsed = {
        "max_wave_height": None,
        "sig_wave_height": None, 
        "wave_period": None,
        "tide": None,
        "wind_speed": None,
        "wind_gust": None,
        "wind_direction": None,
        "water_temp": None,
        "air_temp": None
    }
    
    for condition in conditions_list:
        condition = condition.strip()
        
        # Max wave height
        if "max wave height" in condition.lower():
            match = re.search(r'([\d.]+)\s*m', condition, re.IGNORECASE)
            if match:
                parsed["max_wave_height"] = float(match.group(1))
                
        # Significant wave height  
        elif "sig" in condition.lower() and "wave height" in condition.lower():
            match = re.search(r'([\d.]+)\s*m', condition, re.IGNORECASE)
            if match:
                parsed["sig_wave_height"] = float(match.group(1))
                
        # Wave period
        elif "period" in condition.lower():
            match = re.search(r'([\d.]+)\s*s', condition, re.IGNORECASE)
            if match:
                parsed["wave_period"] = float(match.group(1))
                
        # Wind speed (exclude gust lines)
        elif "wind" in condition.lower() and "gust" not in condition.lower():
            match = re.search(r'([\d.]+)\s*knots?', condition, re.IGNORECASE)
            if match:
                parsed["wind_speed"] = float(match.group(1))
                
        # Wind gust
        elif "gust" in condition.lower():
            match = re.search(r'([\d.]+)\s*knots?', condition, re.IGNORECASE)
            if match:
                parsed["wind_gust"] = float(match.group(1))
                
        # Wind direction
        elif "direction" in condition.lower():
            match = re.search(r'([NSEW]{1,3})', condition, re.IGNORECASE)
            if match:
                parsed["wind_direction"] = match.group(1).upper()
                
        # Water temperature
        elif "water temp" in condition.lower():
            match = re.search(r'([\d.]+)\s*°?c', condition, re.IGNORECASE)
            if match:
                parsed["water_temp"] = float(match.group(1))
                
        # Air temperature
        elif "air temp" in condition.lower():
            match = re.search(r'([\d.]+)\s*°?c', condition, re.IGNORECASE)
            if match:
                parsed["air_temp"] = float(match.group(1))
    
    return parsed

def is_data_complete(parsed_conditions):
    """Check if we have the critical data points"""
    critical_fields = [
        "max_wave_height", 
        "sig_wave_height", 
        "wind_speed", 
        "wind_direction"
    ]
    
    # Check if at least 3 out of 4 critical fields are present
    present_fields = sum(1 for field in critical_fields if parsed_conditions[field] is not None)
    
    # Must have both wave height fields OR wind data
    has_wave_data = (parsed_conditions["max_wave_height"] is not None or 
                    parsed_conditions["sig_wave_height"] is not None)
    has_wind_data = (parsed_conditions["wind_speed"] is not None)
    
    return present_fields >= 3 and has_wave_data and has_wind_data

def load_existing_data():
    """Load existing JSON data if it exists"""
    try:
        if os.path.exists('wave_data.json'):
            with open('wave_data.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return None

# Step 1: Send a GET request to fetch the webpage content
url = 'https://www.port-tauranga.co.nz/operations/harbour-conditions/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}
response = requests.get(url, headers=headers)

# Step 2: Parse the HTML using BeautifulSoup
soup = BeautifulSoup(response.content, 'html.parser')

# Step 3: Find the <img> tag with id="harbour"
img_tag = soup.find('img', id='harbour')

if img_tag:
    img_url = img_tag['src']
    full_img_url = requests.compat.urljoin(url, img_url)  # Handle relative URL
    img_response = requests.get(full_img_url, headers=headers)

    content_type = img_response.headers.get('Content-Type', '')

    if 'image' in content_type:
        try:
            # Open the image using PIL
            img = Image.open(BytesIO(img_response.content))
            
            # Verify the image is not corrupted
            img.verify()
            
            # Reopen the image for processing (verify() closes it)
            img = Image.open(BytesIO(img_response.content))

            # Convert to OpenCV format (initial conversion to BGR)
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

            # Optional Preprocessing: Resize, enhance contrast, etc.
            img_cv_resized = cv2.resize(img_cv, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)

            # Step 4: Use EasyOCR for text extraction
            reader = easyocr.Reader(['en'])  # Load the English model
            result = reader.readtext(img_cv_resized)

            # Extracted text
            extracted_text = "\n".join([text for (_, text, _) in result])

            # Keywords to search for
            keywords = [
                "Port Weather & Sea Conditions",
                "Max wave height:",
                "Sig: wave height:",
                "period:",
                "Tide:",
                "Wind:",
                "Gust:",
                "Direction:",
                "Water Temp:",
                "Air Temp:"
            ]

            # Find the lines containing the keywords and the line immediately below
            lines = extracted_text.split('\n')
            output_lines = []
            for keyword in keywords:
                for i, line in enumerate(lines):
                    if keyword in line:
                        output_lines.append(line)
                        if i + 1 < len(lines):
                            output_lines.append(lines[i + 1])
                        break

            # Remove the very first output line
            if output_lines:
                output_lines.pop(0)

            # Combine the output lines into the specified format
            formatted_output = "\n".join(output_lines)

            # Add "Title" on the first line and "Time" on the third line
            title = "Title"
            location = "Mauao Wave Buoy"
            time = "Time"
            formatted_output = f"{title},\n{location},\n{time},\n{formatted_output}"

            # Print the formatted output
            print("Formatted Output:")
            print(formatted_output)

            # Parse the data into structured format
            lines = formatted_output.split('\n')
            conditions_list = lines[3:] if len(lines) > 3 else []
            
            # Parse conditions with validation
            structured_conditions = parse_wave_conditions(conditions_list)
            
            # Check if data is complete enough to update
            if is_data_complete(structured_conditions):
                
                # Data is good - create new JSON
                wave_data = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "location": "Mauao Wave Buoy",
                    "last_updated": datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC"),
                    "status": "success",
                    "data_quality": "complete",
                    "scrape_attempt": datetime.utcnow().isoformat() + "Z",
                    "raw_data": formatted_output,
                    "parsed_data": {
                        "title": lines[0] if len(lines) > 0 else "",
                        "location": lines[1] if len(lines) > 1 else "",
                        "time_label": lines[2] if len(lines) > 2 else "",
                        "conditions": structured_conditions,
                        "raw_conditions": conditions_list
                    }
                }
                
                # Save the new complete data
                with open('wave_data.json', 'w', encoding='utf-8') as json_file:
                    json.dump(wave_data, json_file, indent=2)
                    
                print("✅ Complete data found - JSON updated successfully")
                print(f"Wave height: {structured_conditions['max_wave_height']}m")
                print(f"Wind: {structured_conditions['wind_speed']} knots {structured_conditions['wind_direction']}")
                
            else:
                # Data is incomplete - preserve existing JSON
                existing_data = load_existing_data()
                
                if existing_data:
                    # Update the scrape attempt timestamp but keep existing data
                    existing_data["last_scrape_attempt"] = datetime.utcnow().isoformat() + "Z"
                    existing_data["last_scrape_status"] = "incomplete_data_skipped"
                    
                    with open('wave_data.json', 'w', encoding='utf-8') as json_file:
                        json.dump(existing_data, json_file, indent=2)
                        
                    print("⚠️  Incomplete data detected - keeping previous good data")
                    print(f"Missing critical fields - skipping this update")
                    print(f"Last good data from: {existing_data.get('last_updated', 'unknown')}")
                else:
                    # No existing data and current data is incomplete
                    print("❌ No existing data and current scrape incomplete - no JSON created")
            
            # Always save the raw text file for debugging
            with open('portDataScrape.txt', 'w', encoding='utf-8') as output_file:
                output_file.write(formatted_output)
                print("Extracted text saved to 'portDataScrape.txt'")
                
            # Always create HTML file
            with open('index.html', 'w', encoding='utf-8') as html_file:
                status = "✅ Data Complete" if is_data_complete(structured_conditions) else "⚠️ Data Incomplete - Using Previous"
                html_file.write(f"""
<!DOCTYPE html>
<html>
<head>
    <title>Mauao Wave Data</title>
    <meta http-equiv="refresh" content="300">
</head>
<body>
    <h1>Mauao Wave Buoy Data</h1>
    <p><strong>Status:</strong> {status}</p>
    <p><strong>Last scrape attempt:</strong> {datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")}</p>
    <h2>Raw Extracted Data:</h2>
    <pre>{formatted_output}</pre>
    <p><a href="wave_data.json">JSON Data</a></p>
</body>
</html>
""")

        except (OSError, IOError) as e:
            print(f"Error processing image: {e}")
            print("Image may be corrupted or incomplete. Skipping this run.")
            
            # Load existing data and mark the failure
            existing_data = load_existing_data()
            if existing_data:
                existing_data["last_scrape_attempt"] = datetime.utcnow().isoformat() + "Z"
                existing_data["last_scrape_status"] = f"image_error: {str(e)}"
                
                with open('wave_data.json', 'w', encoding='utf-8') as json_file:
                    json.dump(existing_data, json_file, indent=2)
                    
                print("🔄 Image processing failed - preserving last good data")
            else:
                print("💥 No fallback data available")
                
            # Exit gracefully without failing the workflow
            sys.exit(0)

    else:
        print("The URL does not point to an image.")
        
        # Handle non-image response
        existing_data = load_existing_data()
        if existing_data:
            existing_data["last_scrape_attempt"] = datetime.utcnow().isoformat() + "Z"
            existing_data["last_scrape_status"] = "non_image_response"
            
            with open('wave_data.json', 'w', encoding='utf-8') as json_file:
                json.dump(existing_data, json_file, indent=2)
else:
    print("No image found with id 'harbour'")
    
    # Handle missing image tag
    existing_data = load_existing_data()
    if existing_data:
        existing_data["last_scrape_attempt"] = datetime.utcnow().isoformat() + "Z"
        existing_data["last_scrape_status"] = "image_tag_not_found"
        
        with open('wave_data.json', 'w', encoding='utf-8') as json_file:
            json.dump(existing_data, json_file, indent=2)
