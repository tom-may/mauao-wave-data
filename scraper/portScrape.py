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
import time

# Set default encoding to utf-8
sys.stdout.reconfigure(encoding='utf-8')

# Define output directory
OUTPUT_DIR = 'wave-scrape-app/data'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_image_with_retry(url, headers, max_retries=3, timeout=30):
    """Download image with retry logic and chunked reading"""
    for attempt in range(max_retries):
        try:
            print(f"Downloading image (attempt {attempt + 1}/{max_retries})...")
            
            # Use stream=True for large files and set timeout
            response = requests.get(url, headers=headers, stream=True, timeout=timeout)
            response.raise_for_status()
            
            # Read content in chunks to handle incomplete reads
            content = BytesIO()
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # Filter out keep-alive chunks
                    content.write(chunk)
            
            content.seek(0)  # Reset pointer to beginning
            print(f"Successfully downloaded image ({len(content.getvalue())} bytes)")
            return content
            
        except requests.exceptions.ChunkedEncodingError as e:
            print(f"Attempt {attempt + 1}: ChunkedEncodingError - {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print("Max retries reached for ChunkedEncodingError")
                raise
                
        except requests.exceptions.Timeout as e:
            print(f"Attempt {attempt + 1}: Timeout - {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print("Max retries reached for Timeout")
                raise
                
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1}: RequestException - {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print("Max retries reached for RequestException")
                raise
    
    raise Exception("Failed to download after all retry attempts")

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
        json_path = os.path.join(OUTPUT_DIR, 'wave_data.json')
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return None

def create_error_json(error_message):
    """Create standardized error JSON"""
    error_data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "location": "Mauao Wave Buoy",
        "last_updated": datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC"),
        "status": "error",
        "data_quality": "error",
        "scrape_attempt": datetime.utcnow().isoformat() + "Z",
        "error_message": error_message,
        "raw_data": None,
        "parsed_data": {
            "title": None,
            "location": "Mauao Wave Buoy",
            "time_label": None,
            "conditions": {
                "max_wave_height": None,
                "sig_wave_height": None,
                "wave_period": None,
                "tide": None,
                "wind_speed": None,
                "wind_gust": None,
                "wind_direction": None,
                "water_temp": None,
                "air_temp": None
            },
            "raw_conditions": []
        }
    }
    
    json_path = os.path.join(OUTPUT_DIR, 'wave_data.json')
    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(error_data, json_file, indent=2)
    
    return error_data

# Main execution starts here
try:
    # Step 1: Send a GET request to fetch the webpage content
    url = 'https://www.port-tauranga.co.nz/operations/harbour-conditions/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    
    print("Fetching webpage...")
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    # Step 2: Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Step 3: Find the <img> tag with id="harbour"
    img_tag = soup.find('img', id='harbour')

    if img_tag:
        img_url = img_tag['src']
        full_img_url = requests.compat.urljoin(url, img_url)  # Handle relative URL
        print(f"Found image URL: {full_img_url}")
        
        # Download image with retry logic
        try:
            img_content = download_image_with_retry(full_img_url, headers)
            
            # Check content type if possible
            try:
                # Make a quick HEAD request to check content type
                head_response = requests.head(full_img_url, headers=headers, timeout=10)
                content_type = head_response.headers.get('Content-Type', '')
            except:
                content_type = 'image/'  # Assume it's an image if HEAD fails

            if 'image' in content_type:
                try:
                    # Open the image using PIL
                    img = Image.open(img_content)
                    
                    # Verify the image is not corrupted
                    img.verify()
                    
                    # Reopen the image for processing (verify() closes it)
                    img_content.seek(0)  # Reset pointer
                    img = Image.open(img_content)

                    # Convert to OpenCV format (initial conversion to BGR)
                    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

                    # Optional Preprocessing: Resize, enhance contrast, etc.
                    img_cv_resized = cv2.resize(img_cv, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)

                    # Step 4: Use EasyOCR for text extraction
                    print("Performing OCR...")
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
                    
                    # Always create JSON - determine data quality
                    data_quality = "complete" if is_data_complete(structured_conditions) else "incomplete"
                    status = "success" if is_data_complete(structured_conditions) else "partial_data"
                    
                    # Create new JSON with current data (complete or incomplete)
                    wave_data = {
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "location": "Mauao Wave Buoy",
                        "last_updated": datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC"),
                        "status": status,
                        "data_quality": data_quality,
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
                    
                    # Always save the JSON
                    json_path = os.path.join(OUTPUT_DIR, 'wave_data.json')
                    with open(json_path, 'w', encoding='utf-8') as json_file:
                        json.dump(wave_data, json_file, indent=2)
                        
                    if is_data_complete(structured_conditions):
                        print("✅ Complete data found - JSON updated successfully")
                        print(f"Wave height: {structured_conditions['max_wave_height']}m")
                        print(f"Wind: {structured_conditions['wind_speed']} knots {structured_conditions['wind_direction']}")
                    else:
                        print("⚠️ Incomplete data - JSON created with null values for missing fields")
                        missing_fields = [k for k, v in structured_conditions.items() if v is None]
                        print(f"Missing fields: {', '.join(missing_fields)}")
                    
                    # Always save the raw text file for debugging
                    txt_path = os.path.join(OUTPUT_DIR, 'portDataScrape.txt')
                    with open(txt_path, 'w', encoding='utf-8') as output_file:
                        output_file.write(formatted_output)
                        print(f"Extracted text saved to '{txt_path}'")
                        
                    # Always create HTML file
                    html_path = os.path.join(OUTPUT_DIR, 'index.html')
                    with open(html_path, 'w', encoding='utf-8') as html_file:
                        status_display = "✅ Data Complete" if is_data_complete(structured_conditions) else "⚠️ Data Incomplete (with nulls)"
                        html_file.write(f"""
<!DOCTYPE html>
<html>
<head>
    <title>Mauao Wave Data</title>
    <meta http-equiv="refresh" content="300">
</head>
<body>
    <h1>Mauao Wave Buoy Data</h1>
    <p><strong>Status:</strong> {status_display}</p>
    <p><strong>Last scrape attempt:</strong> {datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")}</p>
    <h2>Raw Extracted Data:</h2>
    <pre>{formatted_output}</pre>
    <p><a href="wave_data.json">JSON Data</a></p>
</body>
</html>
""")

                except (OSError, IOError) as e:
                    print(f"Error processing image: {e}")
                    print("Image may be corrupted or incomplete. Creating error JSON.")
                    create_error_json(f"Image processing error: {str(e)}")
                    print("💥 Error JSON created with null values")
                    sys.exit(0)

            else:
                print("The URL does not point to an image.")
                create_error_json("Non-image response received")
                
        except Exception as e:
            print(f"Failed to download image: {e}")
            create_error_json(f"Image download failed: {str(e)}")
            print("💥 Error JSON created due to download failure")
            sys.exit(0)
            
    else:
        print("No image found with id 'harbour'")
        create_error_json("Image tag not found")

except requests.exceptions.RequestException as e:
    print(f"Failed to fetch webpage: {e}")
    create_error_json(f"Webpage fetch failed: {str(e)}")
    print("💥 Error JSON created due to webpage fetch failure")
    sys.exit(0)

except Exception as e:
    print(f"Unexpected error: {e}")
    create_error_json(f"Unexpected error: {str(e)}")
    print("💥 Error JSON created due to unexpected error")
    sys.exit(0)
