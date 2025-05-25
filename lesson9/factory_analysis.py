import os
import json
import requests
import zipfile
from pathlib import Path
import shutil
from openai import OpenAI
from PIL import Image
import pytesseract
import whisper
import logging
from dotenv import load_dotenv
import torch
import subprocess
import base64

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
API_KEY = os.getenv("API_KEY")  # Replace with your actual API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Replace with your OpenAI API key
ZIP_URL = "https://c3ntrala.ag3nts.org/dane/pliki_z_fabryki.zip"
REPORT_URL = "https://c3ntrala.ag3nts.org/report"

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def check_dependencies():
    """Check if required dependencies are installed."""
    # Check FFmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        logging.error("FFmpeg is not installed. Audio processing will be skipped.")
        return False
    return True

# Initialize Whisper model globally
try:
    whisper_model = whisper.load_model("base", device="cpu" if not torch.cuda.is_available() else "cuda")
except Exception as e:
    logging.error(f"Failed to load Whisper model: {e}")
    whisper_model = None

def download_and_extract_zip():
    """Download and extract the ZIP file."""
    try:
        # Download the ZIP file
        response = requests.get(ZIP_URL)
        response.raise_for_status()
        
        # Save the ZIP file
        zip_path = "pliki_z_fabryki.zip"
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        
        # Extract the ZIP file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall("extracted_files")
        
        # Clean up the ZIP file
        os.remove(zip_path)
        logging.info("Successfully downloaded and extracted the ZIP file")
        
    except Exception as e:
        logging.error(f"Error downloading or extracting ZIP file: {e}")
        raise

def analyze_with_gpt(content, file_type):
    """Analyze content using GPT to determine its category."""
    try:
        prompt = f"""You are a factory report analyzer. Your task is to categorize the following {file_type} content into EXACTLY ONE of these categories:

1. "people" - ONLY if the content explicitly shows:
   - Direct evidence of CAPTURED or DETAINED people
   - Clear, recent physical evidence of human presence (fresh footprints, fingerprints)
   - Direct visual confirmation of intruders being caught
   - Clear evidence of recent unauthorized human activity (recently moved objects, recently opened doors)
   - Direct security alerts about confirmed human presence and capture
   - Direct surveillance footage showing people being detained
   - Direct reports of human contact or interaction with security
   - Direct evidence of security breaches by people who were caught
   DO NOT categorize as "people" if:
   - There are only indirect or unclear signs
   - The evidence is old or historical
   - There are only suspicions without clear evidence
   - The content only mentions general security measures
   - The content only describes normal factory operations
   - The content only mentions security systems or cameras
   - The content only describes maintenance or technical issues

2. "hardware" - ONLY if the content mentions:
   - Equipment or machinery REPAIRS
   - Technical diagrams related to REPAIRS
   - Maintenance records of FIXED issues
   - System status reports showing RESOLVED hardware problems
   - Technical diagnostics of REPAIRED equipment
   - Physical damage to equipment that was FIXED
   - Hardware components that were REPLACED or REPAIRED
   - Technical measurements or readings showing RESOLVED issues
   - Security system hardware REPAIRS
   DO NOT categorize as "hardware" if:
   - The content is about software issues or updates
   - The content describes ongoing problems without repairs
   - The content is about software maintenance
   - The content describes software configurations
   - The content is about software security
   - The content describes software diagnostics
   - The content is about software updates or patches

3. "none" - if the content doesn't clearly fit either category above.

Content to analyze:
{content}

IMPORTANT:
- For "people" category, require clear, direct, and recent evidence of CAPTURED people or their traces
- Do not categorize as "people" if there's any doubt
- For "hardware" category, focus ONLY on REPAIRED or FIXED hardware issues
- When in doubt, categorize as "none"
- Pay special attention to the timing and clarity of evidence
- Only categorize as "people" if there is undeniable evidence of human presence or capture
- Please justify your decision
- Respond with ONLY one word: "people", "hardware", or "none"."""

        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a factory report analyzer. You must be extremely strict about categorizing content as 'people'. Only categorize as 'people' if there is clear, direct, and recent evidence of human presence or capture. For 'hardware', only include content about REPAIRED or FIXED hardware issues. When in doubt, prefer 'none'."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        category = response.choices[0].message.content.strip().lower()
        logging.info(f"File type: {file_type}, Category: {category}")
        logging.info(f"Content preview: {content[:500]}...")
        
        if category in ["people", "hardware"]:
            return category
        return None
        
    except Exception as e:
        logging.error(f"Error analyzing with GPT: {e}")
        return None

def analyze_text_file(file_path):
    """Analyze a text file and determine its category."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return analyze_with_gpt(content, "text")
        
    except Exception as e:
        logging.error(f"Error analyzing text file {file_path}: {e}")
        return None

def analyze_image(file_path):
    """Analyze an image file using OCR and GPT."""
    try:
        # Extract text from image using OCR
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image, lang='pol')
        
        if not text.strip():
            # If OCR fails, try to analyze the image directly with GPT-4 Vision
            with open(file_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                
                response = client.chat.completions.create(
                    model="gpt-4-vision-preview",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": """You are a factory report analyzer. Your task is to categorize this image into EXACTLY ONE of these categories:

1. "people" - ONLY if the image shows:
   - Actual people or human figures
   - Clear, recent human footprints or handprints
   - Recent signs of human activity (like recently moved objects)
   - Clear evidence of unauthorized access
   - Recent security breaches
   - Recent surveillance footage showing people
   DO NOT categorize as "people" if:
   - The image only shows equipment or machinery
   - The image shows old or historical evidence
   - The image shows only indirect signs
   - The image shows only security systems or cameras
   - The image shows only maintenance records or logs

2. "hardware" - if the image shows:
   - Equipment or machinery
   - Technical diagrams
   - Maintenance records
   - System status displays
   - Technical documentation
   - Physical damage to equipment
   - Hardware components
   - Technical measurements or readings

3. "none" - if the image doesn't clearly fit either category above.

IMPORTANT:
- For "people" category, require clear, direct evidence of human presence
- Do not categorize as "people" if there's any doubt
- When in doubt, categorize as "hardware" or "none"
- Respond with ONLY one word: "people", "hardware", or "none"."""
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=10
                )
                
                category = response.choices[0].message.content.strip().lower()
                if category in ["people", "hardware"]:
                    return category
                return None
        
        # If OCR succeeded, analyze the extracted text
        return analyze_with_gpt(text, "image text")
        
    except Exception as e:
        logging.error(f"Error analyzing image file {file_path}: {e}")
        return None

def analyze_audio(file_path):
    """Analyze an audio file using Whisper and GPT."""
    try:
        if whisper_model is None:
            logging.error("Whisper model not loaded. Skipping audio analysis.")
            return None
            
        # Transcribe audio
        result = whisper_model.transcribe(file_path, language="en")
        text = result["text"]
        
        return analyze_with_gpt(text, "audio transcript")
        
    except Exception as e:
        logging.error(f"Error analyzing audio file {file_path}: {e}")
        return None

def process_files():
    """Process all files in the extracted directory."""
    categories = {
        "people": [],
        "hardware": []
    }
    
    # Walk through the extracted directory
    for root, dirs, files in os.walk("extracted_files"):
        # Skip the "facts" directory
        if "facts" in root:
            continue
            
        for file in files:
            # Skip files without extension, weapons_tests.zip, and specific problematic file
            if not os.path.splitext(file)[1] or file == "weapons_tests.zip":
                continue
                
            file_path = os.path.join(root, file)
            file_ext = os.path.splitext(file)[1].lower()
            
            # Determine file category based on extension
            category = None
            if file_ext == '.txt':
                category = analyze_text_file(file_path)
            elif file_ext == '.png':
                category = analyze_image(file_path)
            elif file_ext == '.mp3':
                category = analyze_audio(file_path)
                
            # Add file to appropriate category if categorized
            if category:
                categories[category].append(file)
    
    # Sort file lists alphabetically
    for category in categories:
        categories[category].sort()
        
    return categories

def send_report(categories):
    """Send the categorized data to the central server."""
    try:
        # Ensure both categories have at least one file
        if not categories["people"] or not categories["hardware"]:
            logging.error("Both categories must contain at least one file")
            raise ValueError("Both categories must contain at least one file")
            
        payload = {
            "task": "kategorie",
            "apikey": API_KEY,
            "answer": categories
        }
        
        response = requests.post(
            REPORT_URL,
            json=payload,
            headers={'Content-Type': 'application/json; charset=utf-8'}
        )
        
        if response.status_code != 200:
            logging.error(f"Server response: {response.text}")
            response.raise_for_status()
            
        logging.info("Successfully sent report to central server")
        return response.json()
        
    except Exception as e:
        logging.error(f"Error sending report: {e}")
        raise

def main():
    try:
        # Check dependencies
        has_ffmpeg = check_dependencies()
        
        # Download and extract files
        download_and_extract_zip()
        
        # Process files and categorize them
        categories = process_files()
        
        # Print categories for debugging
        print("\nCategorized files:")
        print(json.dumps(categories, indent=2, ensure_ascii=False))
        
        # Send report to central server
        result = send_report(categories)
        print("\nReport sent successfully!")
        print("Response:", result)
        
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        # Clean up extracted files
        if os.path.exists("extracted_files"):
            shutil.rmtree("extracted_files")

if __name__ == "__main__":
    main() 