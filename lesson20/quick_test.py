import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../.env')

def test_answers():
    personal_api_key = os.getenv('CENTRALA_API_KEY')
    submit_url = "https://c3ntrala.ag3nts.org/report"
    
    # From page 19 OCR: "się dostać do Laponii, która graniczy. Nie jest to daleko. 
    # Mam tylko nadzieję, że Andrzejek będzie miał wystarczająco dużo paliwa. Tankowanie nie wchodzi w grę"
    # This suggests air travel to Lapland. Maybe it's not a city but a region or specific place?
    
    test_sets = [
        {
            "name": "Test 1: Different Lapland spellings",
            "answers": {
                "01": "2019",
                "02": "Adam", 
                "03": "jaskinie skalne",
                "04": "2024-11-12",
                "05": "Lubawa"  # Polish adjective form
            }
        },
        {
            "name": "Test 2: Sami region",
            "answers": {
                "01": "2019",
                "02": "Adam", 
                "03": "jaskinie skalne",
                "04": "2024-11-12",
                "05": "Sápmi"  # Sami name for Lapland
            }
        },
        {
            "name": "Test 3: Northern airports/regions",
            "answers": {
                "01": "2019",
                "02": "Adam", 
                "03": "jaskinie skalne",
                "04": "2024-11-12",
                "05": "Finnmark"  # Northernmost region of Norway
            }
        },
        {
            "name": "Test 4: Try Nordkapp",
            "answers": {
                "01": "2019",
                "02": "Adam", 
                "03": "jaskinie skalne",
                "04": "2024-11-12",
                "05": "Nordkapp"  # North Cape
            }
        },
        {
            "name": "Test 5: Simple forms",
            "answers": {
                "01": "2019",
                "02": "Adam", 
                "03": "jaskinie skalne",
                "04": "2024-11-12",
                "05": "Północ"  # Polish for "North"
            }
        },
        {
            "name": "Test 6: Skandynawia",
            "answers": {
                "01": "2019",
                "02": "Adam", 
                "03": "jaskinie skalne",
                "04": "2024-11-12",
                "05": "Skandynawia"
            }
        }
    ]
    
    for test_set in test_sets:
        print(f"\n--- {test_set['name']} ---")
        
        report_data = {
            "task": "notes",
            "apikey": personal_api_key,
            "answer": test_set['answers']
        }
        
        try:
            response = requests.post(submit_url, json=report_data)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Result: {result}")
                
                # If successful, we're done
                if result.get('code') == 0:
                    print("SUCCESS! All answers correct!")
                    break
                    
        except Exception as e:
            print(f"Error: {e}")
            
        print("-" * 50)

if __name__ == "__main__":
    test_answers() 