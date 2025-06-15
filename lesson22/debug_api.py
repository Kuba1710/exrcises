import requests
import json


def test_places_api():
    places_api_url = "https://c3ntrala.ag3nts.org/places"
    
    # Test different variations of Lubawa
    test_queries = ["LUBAWA", "Lubawa", "lubawa"]
    
    for query in test_queries:
        print(f"\n=== Testing query: '{query}' ===")
        data = {
            "apikey": API_KEY,
            "query": query
        }
        
        response = requests.post(places_api_url, json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        try:
            result = response.json()
            print(f"JSON: {json.dumps(result, indent=2, ensure_ascii=False)}")
        except:
            print("Not valid JSON")

def test_user_coordinates():
    places_api_url = "https://c3ntrala.ag3nts.org/places"
    
    # Test coordinates for users
    test_users = ["RAFAL", "AZAZEL", "SAMUEL"]
    
    for user in test_users:
        print(f"\n=== Testing user coordinates: '{user}' ===")
        data = {
            "apikey": API_KEY,
            "query": user
        }
        
        response = requests.post(places_api_url, json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        try:
            result = response.json()
            print(f"JSON: {json.dumps(result, indent=2, ensure_ascii=False)}")
        except:
            print("Not valid JSON")

def test_database_users():
    db_api_url = "https://c3ntrala.ag3nts.org/apidb"
    
    # Check database structure
    queries = [
        "SHOW TABLES",  # Check what tables exist
        "SELECT * FROM users LIMIT 5",  # Check user structure
        "DESCRIBE users"  # Check user table structure
    ]
    
    for query in queries:
        print(f"\n=== Testing DB query: '{query}' ===")
        data = {
            "task": "database",
            "apikey": API_KEY,
            "query": query
        }
        
        response = requests.post(db_api_url, json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        try:
            result = response.json()
            print(f"JSON: {json.dumps(result, indent=2, ensure_ascii=False)}")
        except:
            print("Not valid JSON")

def test_all_tables():
    db_api_url = "https://c3ntrala.ag3nts.org/apidb"
    
    # Check all tables
    tables = ["users", "datacenters", "connections", "correct_order"]
    
    for table in tables:
        print(f"\n=== Testing table: '{table}' ===")
        query = f"SELECT * FROM {table} LIMIT 3"
        data = {
            "task": "database",
            "apikey": API_KEY,
            "query": query
        }
        
        response = requests.post(db_api_url, json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        try:
            result = response.json()
            print(f"JSON: {json.dumps(result, indent=2, ensure_ascii=False)}")
        except:
            print("Not valid JSON")

def test_gps_endpoints():
    # Test different GPS endpoints
    gps_endpoints = [
        "https://c3ntrala.ag3nts.org/gps",
        "https://c3ntrala.ag3nts.org/apidb/gps",
        "https://c3ntrala.ag3nts.org/places/gps"
    ]
    
    user_ids = [28, 3, 98]  # IDs for RAFAL, AZAZEL, SAMUEL
    
    for endpoint in gps_endpoints:
        for user_id in user_ids:
            print(f"\n=== Testing GPS endpoint: '{endpoint}' with userID={user_id} ===")
            data = {
                "apikey": API_KEY,
                "userID": user_id
            }
            
            response = requests.post(endpoint, json=data)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
            try:
                result = response.json()
                print(f"JSON: {json.dumps(result, indent=2, ensure_ascii=False)}")
            except:
                print("Not valid JSON")

def test_places_with_userid():
    # Test places API with userID instead of username
    places_api_url = "https://c3ntrala.ag3nts.org/places"
    
    user_ids = [28, 3, 98]  # IDs for RAFAL, AZAZEL, SAMUEL
    
    for user_id in user_ids:
        print(f"\n=== Testing places API with userID={user_id} ===")
        data = {
            "apikey": API_KEY,
            "query": str(user_id)
        }
        
        response = requests.post(places_api_url, json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        try:
            result = response.json()
            print(f"JSON: {json.dumps(result, indent=2, ensure_ascii=False)}")
        except:
            print("Not valid JSON")

def test_places_different_formats():
    places_api_url = "https://c3ntrala.ag3nts.org/places"
    
    # Test different formats for user names  
    user_formats = [
        "RAFAL",
        "USER:RAFAL",
        "GPS:RAFAL", 
        "COORDINATES:RAFAL",
        "LOCATION:RAFAL"
    ]
    
    for user_format in user_formats:
        print(f"\n=== Testing places API with format: '{user_format}' ===")
        data = {
            "apikey": API_KEY,
            "query": user_format
        }
        
        response = requests.post(places_api_url, json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        try:
            result = response.json()
            print(f"JSON: {json.dumps(result, indent=2, ensure_ascii=False)}")
        except:
            print("Not valid JSON")

if __name__ == "__main__":
    # test_places_api()
    # test_user_coordinates()
    # test_database_users()
    # test_all_tables()
    test_gps_endpoints()
    test_places_with_userid()
    test_places_different_formats() 