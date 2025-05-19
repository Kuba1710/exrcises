import requests
import json
import os
import sys
from dotenv import load_dotenv
import openai

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment variables
API_KEY = os.getenv("API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

if not API_KEY:
    print("Error: API_KEY not found in .env file.")
    print("Please add your API_KEY to the .env file.")
    sys.exit(1)

if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY not found in .env file.")
    print("Please add your OPENAI_API_KEY to the .env file.")
    sys.exit(1)

# Configure OpenAI client
openai.api_key = OPENAI_API_KEY

def fetch_data():
    url = f"https://c3ntrala.ag3nts.org/data/{API_KEY}/cenzura.txt"
    response = requests.get(url)
    response.raise_for_status()
    
    # Get the text content and trim any whitespace
    data = response.text.strip()
    return data

def censor_data(text):
    # Print original text for debugging
    print(f"Original text: {text}")
    
    # Create a system prompt that explains the censoring rules
    system_prompt = """
    You are a text censoring system. Your task is to censor personal information in the provided text by replacing specific information with the word "CENZURA". 
    
    Replace the following information with "CENZURA":
    1. Full names (e.g., "Jan Nowak" -> "CENZURA")
    2. Age (e.g., "32" -> "CENZURA" when it refers to a person's age)
    3. City names (e.g., "Wrocław" -> "CENZURA")
    4. Street addresses (e.g., "ul. Szeroka 18" -> "ul. CENZURA")
    
    Important:
    - Only replace the exact information specified above
    - Maintain the original format (punctuation, spaces, etc.)
    - DO NOT modify any other parts of the text
    - When censoring streets, keep "ul." or similar prefixes, only censor the actual street name and number
    
    Your output must contain ONLY the censored text, without any additional commentary or explanation.
    """
    
    user_prompt = f"Original text: {text}\n\nCensored text:"
    
    # Call the OpenAI API with the system and user prompts
    response = openai.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0  # Use low temperature for consistent output
    )
    
    # Extract the censored text from the response
    censored = response.choices[0].message.content.strip()
    
    # Print censored text for debugging
    print(f"Censored text: {censored}")
    
    return censored

def report_data(censored_text):
    url = "https://c3ntrala.ag3nts.org/report"
    payload = {
        "task": "CENZURA",
        "apikey": API_KEY,
        "answer": censored_text
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"Sending payload:")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    
    response = requests.post(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
    response.raise_for_status()
    return response.json()

def main():
    try:
        # Fetch the data
        print("Fetching data...")
        data = fetch_data()
        
        # Censor the data
        print("Censoring data...")
        censored_data = censor_data(data)
        
        # Report the data
        print("Reporting data...")
        result = report_data(censored_data)
        print("Result:", result)
        
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        if "404" in str(e):
            print("\nTIP: The API key may be incorrect. Please check your .env file.")
        elif "400" in str(e):
            print("\nTIP: The server rejected our request. Check the payload format and censoring.")
            print("Make sure you're censoring exactly as required in the instructions.")
            
            # Get response content for more details
            if hasattr(e, 'response') and e.response is not None:
                print("Error details:", e.response.text)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main() 