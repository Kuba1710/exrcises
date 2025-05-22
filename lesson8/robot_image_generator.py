import os
import requests
import json
import argparse
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up argument parser
parser = argparse.ArgumentParser(description='Generate a robot image based on a description and send it to a central server.')
parser.add_argument('--api-key', help='AIDevs API key')
parser.add_argument('--openai-key', help='OpenAI API key')
args = parser.parse_args()

# Get API keys from environment variables or command line arguments
API_KEY = args.api_key or os.getenv("API_KEY")
OPENAI_API_KEY = args.openai_key or os.getenv("OPENAI_API_KEY")

# Check if API keys are available
if not API_KEY:
    API_KEY = input("Please enter your AIDevs API key: ")

if not OPENAI_API_KEY:
    OPENAI_API_KEY = input("Please enter your OpenAI API key: ")

# Try to initialize OpenAI client based on the version
try:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    print("Using new OpenAI client")
except (ImportError, TypeError):
    try:
        # Fall back to old client if new one fails
        import openai
        openai.api_key = OPENAI_API_KEY
        print("Using legacy OpenAI client")
    except ImportError:
        print("Error: OpenAI package not installed. Please run 'pip install openai'")
        sys.exit(1)

def get_robot_description(api_key):
    """Fetch the robot description from the server"""
    url = f"https://c3ntrala.ag3nts.org/data/{api_key}/robotid.json"
    print(f"Fetching from URL: {url}")
    try:
        response = requests.get(url)
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Raw response: {response.text}")
        
        response.raise_for_status()  # Raise exception for HTTP errors
        
        # Try to parse as JSON
        try:
            data = response.json()
            print(f"Full API response (JSON): {data}")
            
            # Check if the response contains a description
            # The key might not be 'robot_description', so let's look for any key that might
            # contain the description
            description = None
            if isinstance(data, dict):
                for key in data:
                    if 'description' in key.lower() or 'robot' in key.lower():
                        description = data[key]
                        print(f"Found description under key: {key}")
                        break
                
                # If we couldn't find a likely key, take the first value
                if not description and len(data) > 0:
                    first_key = next(iter(data))
                    description = data[first_key]
                    print(f"Using first key in response: {first_key}")
            
            # If data is a string or we couldn't find a description in the dict
            if not description:
                if isinstance(data, str):
                    description = data
                else:
                    # If we still can't find a description, use the entire response as is
                    description = str(data)
            
            print(f"Extracted description: {description}")
            return description
            
        except json.JSONDecodeError:
            print("Response is not valid JSON, using text content directly")
            return response.text
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching robot description: {e}")
        sys.exit(1)

def generate_robot_image(description):
    """Generate an image of the robot using DALL-E 3"""
    try:
        # Craft a more detailed prompt based on the description
        prompt = f"""Generate a detailed, realistic image of a robot with the following description: 
{description}

The image should be:
- Clear and well-lit
- Show the robot in its entirety
- Have a neutral background
- Include all details mentioned in the description
- Be highly detailed and photorealistic
"""
        print(f"Sending prompt to DALL-E: {prompt}")
        
        # Generate image based on which client we're using
        if 'client' in globals():
            # New client
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024",
                quality="standard",
                response_format="url"
            )
            image_url = response.data[0].url
        else:
            # Legacy client
            response = openai.Image.create(
                prompt=prompt,
                n=1,
                size="1024x1024",
                model="dall-e-3",
                response_format="url"
            )
            image_url = response['data'][0]['url']
            
        return image_url
    except Exception as e:
        print(f"Error generating image: {e}")
        sys.exit(1)

def send_to_central(api_key, image_url):
    """Send the image URL to the central server"""
    url = "https://c3ntrala.ag3nts.org/report"
    payload = {
        "task": "robotid",
        "apikey": api_key,
        "answer": image_url
    }
    
    print(f"Sending payload to {url}: {payload}")
    
    try:
        response = requests.post(url, json=payload)
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending data to central server: {e}")
        print(f"Response content: {response.content if 'response' in locals() else 'No response'}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing server response: {e}")
        print(f"Response content: {response.content if 'response' in locals() else 'No response'}")
        sys.exit(1)

def main():
    print("Robot Image Generator")
    print(f"AIDevs API Key: {API_KEY[:5]}...{API_KEY[-5:] if API_KEY else 'None'}")
    print(f"OpenAI API Key: {OPENAI_API_KEY[:5]}...{OPENAI_API_KEY[-5:] if OPENAI_API_KEY else 'None'}")
    
    print("1. Fetching robot description...")
    description = get_robot_description(API_KEY)
    print(f"Description: {description}")
    
    print("\n2. Generating robot image...")
    image_url = generate_robot_image(description)
    print(f"Image URL: {image_url}")
    
    print("\n3. Sending image URL to central server...")
    result = send_to_central(API_KEY, image_url)
    print(f"Server response: {result}")

if __name__ == "__main__":
    main() 