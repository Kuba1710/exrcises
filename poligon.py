import requests
import json

# URL for data and verification
DATA_URL = "https://poligon.aidevs.pl/dane.txt"
VERIFY_URL = "https://poligon.aidevs.pl/verify"

# Your API key and task identifier
API_KEY = "94097678-8e03-41d2-9656-a54c7f1371c1"  # Replace with your actual API key
TASK_ID = "POLIGON"  # Replace with your actual task ID

def main():
    # Download data from the URL
    response = requests.get(DATA_URL)
    if response.status_code != 200:
        print(f"Error downloading data: {response.status_code}")
        return

    # Get the content and split it into two strings
    content = response.text.strip()
    strings = content.split()

    if len(strings) != 2:
        print("Error: Expected exactly two strings in the response")
        return

    # Prepare the data for verification
    verify_data = {
        "task": TASK_ID,
        "apikey": API_KEY,
        "answer": strings
    }

    # Send the data to verification endpoint
    verify_response = requests.post(VERIFY_URL, json=verify_data)
    
    # Print the response
    print(f"Verification response: {verify_response.text}")

if __name__ == "__main__":
    main()
