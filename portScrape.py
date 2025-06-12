# try to use the process as is, perhaps will some lazy load type logic on the monkey C side to use most recent pulled data?
# To make this process run faster do the below, then ask copilot to update the code:

# To make EasyOCR faster by utilizing a GPU, you need to ensure that you have the necessary GPU drivers and libraries installed. Specifically, you need to have CUDA and cuDNN installed, and you need to install the GPU version of PyTorch, which EasyOCR relies on.

# Here are the steps to set up your environment to use a GPU with EasyOCR:

# 1. **Install CUDA and cuDNN**:
#    - Download and install the appropriate version of CUDA from the [NVIDIA CUDA Toolkit website](https://developer.nvidia.com/cuda-toolkit).
#    - Download and install the appropriate version of cuDNN from the [NVIDIA cuDNN website](https://developer.nvidia.com/cudnn).

# 2. **Install the GPU version of PyTorch**:
#    - Visit the [PyTorch website](https://pytorch.org/get-started/locally/) and follow the instructions to install the GPU version of PyTorch. For example, you can use the following command to install PyTorch with CUDA support:
#      ```sh
#      pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu113
#      ```
#      Replace `cu113` with the appropriate CUDA version you have installed.

# 3. **Verify GPU Availability**:
#    - You can verify that PyTorch can access the GPU by running the following Python code:
#      ```python
#      import torch
#      print(torch.cuda.is_available())
#      ```
#      This should print `True` if the GPU is available.

# 4. **Run EasyOCR with GPU**:
#    - EasyOCR will automatically use the GPU if it is available. Ensure that you have the GPU version of PyTorch installed and that your GPU is properly configured.

# ERROR? CHECK MONKEY C INSTALLED CORRECTLY:
# https://developer.garmin.com/connect-iq/connect-iq-basics/getting-started/



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

# Set default encoding to utf-8
sys.stdout.reconfigure(encoding='utf-8')

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
        # Open the image using PIL
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
        date_time = "24/10/2024 09.32 DT"
        formatted_output = f"{title},\n{location},\n{time},\n{formatted_output}"

        # Print the formatted output
        print("Formatted Output:")
        print(formatted_output)

           # Save the formatted output to a file (keep existing functionality)
        with open('portDataScrape.txt', 'w', encoding='utf-8') as output_file:
            output_file.write(formatted_output)
            print("Extracted text saved to 'portDataScrape.txt'")
        
        # NEW: Save as JSON for Garmin widget
        import json
        from datetime import datetime
        
        # Parse the data into structured format
        lines = formatted_output.split('\n')
        wave_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "location": "Mauao Wave Buoy",
            "last_updated": datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC"),
            "raw_data": formatted_output,
            "parsed_data": {
                "title": lines[0] if len(lines) > 0 else "",
                "location": lines[1] if len(lines) > 1 else "",
                "time_label": lines[2] if len(lines) > 2 else "",
                "conditions": lines[3:] if len(lines) > 3 else []
            }
        }
        
        with open('wave_data.json', 'w', encoding='utf-8') as json_file:
            json.dump(wave_data, json_file, indent=2)
            print("Data saved to wave_data.json")
            
        # Also create a simple status file
        with open('index.html', 'w', encoding='utf-8') as html_file:
            html_file.write(f"""
<!DOCTYPE html>
<html>
<head>
    <title>Mauao Wave Data</title>
    <meta http-equiv="refresh" content="300">
</head>
<body>
    <h1>Mauao Wave Buoy Data</h1>
    <p>Last updated: {datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")}</p>
    <pre>{formatted_output}</pre>
    <p><a href="wave_data.json">JSON Data</a></p>
</body>
</html>
""")
            
    else:
        print("The URL does not point to an image.")
else:
    print("No image found with id 'harbour'")
