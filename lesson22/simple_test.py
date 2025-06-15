import requests
import json

API_KEY = "94097678-8e03-41d2-9656-a54c7f1371c1"

# First, let's get user IDs for our target users
db_api_url = "https://c3ntrala.ag3nts.org/apidb"
places_api_url = "https://c3ntrala.ag3nts.org/places"

# Get IDs for target users
users = ["RAFAL", "AZAZEL", "SAMUEL"]

print("Getting user IDs...")
for user in users:
    query = f"SELECT id FROM users WHERE username = '{user}'"
    data = {
        "task": "database",
        "apikey": API_KEY,
        "query": query
    }
    
    response = requests.post(db_api_url, json=data)
    result = response.json()
    
    if "reply" in result and result["reply"]:
        user_id = result["reply"][0]["id"]
        print(f"{user}: ID = {user_id}")
        
        # Now try to find GPS data by trying places API with user ID as string
        gps_data = {
            "apikey": API_KEY,
            "query": f"USER{user_id}"
        }
        
        gps_response = requests.post(places_api_url, json=gps_data)
        print(f"  GPS test: {gps_response.text}")
        
    else:
        print(f"{user}: Not found") 