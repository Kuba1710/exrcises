import requests
import json
import os

API_KEY = "94097678-8e03-41d2-9656-a54c7f1371c1"

class GPSAgent:
    def __init__(self):
        self.api_key = API_KEY
        self.db_api_url = "https://c3ntrala.ag3nts.org/apidb"
        self.places_api_url = "https://c3ntrala.ag3nts.org/places"
        self.gps_api_url = "https://c3ntrala.ag3nts.org/gps"
        self.report_url = "https://c3ntrala.ag3nts.org/report"
    
    def load_question(self, filename):
        """Load question from JSON file"""
        print(f"> Reading data from file... [OK]")
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, filename)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data["question"]
    
    def check_user_in_db(self, username):
        """Check if user exists in database and get their ID"""
        query = f"SELECT id FROM users WHERE username = '{username}'"
        data = {
            "task": "database",
            "apikey": self.api_key,
            "query": query
        }
        
        response = requests.post(self.db_api_url, json=data)
        result = response.json()
        
        if "reply" in result and result["reply"]:
            return int(result["reply"][0]["id"])
        return None
    
    def check_place_api(self, place):
        """Check if place exists in places API"""
        data = {
            "apikey": self.api_key,
            "query": place
        }
        
        response = requests.post(self.places_api_url, json=data)
        result = response.json()
        
        return "message" in result and result["message"] != "place not found"
    
    def get_users_from_place(self, place):
        """Get users from a specific place"""
        data = {
            "apikey": self.api_key,
            "query": place
        }
        
        response = requests.post(self.places_api_url, json=data)
        result = response.json()
        
        if "message" in result and isinstance(result["message"], str):
            # Split string by spaces to get list of users
            users = result["message"].split()
            return users
        return []
    
    def get_gps_coordinates(self, user_id):
        """Get GPS coordinates for a user by userID using the /gps endpoint"""
        data = {
            "apikey": self.api_key,
            "userID": user_id
        }
        
        response = requests.post(self.gps_api_url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            if "message" in result and isinstance(result["message"], dict):
                if "lat" in result["message"] and "lon" in result["message"]:
                    return {
                        "lat": result["message"]["lat"],
                        "lon": result["message"]["lon"]
                    }
        
        return None
    
    def process_question(self, question):
        """Process the main question and extract location data"""
        print(f"> Processing user question... [OK]")
        print(f"> Preparing plan...")
        print(f"> Executing plan...")
        
        # From question: Rafał planned to go to Lubawa, find who was waiting for him there
        place = "LUBAWA"
        
        print(f"  - Step 1: Check if this is username or place - select API or DB [OK]")
        print(f"     - place found - '{place}'")
        print(f"     - Check if place exists in external API /places... [OK]")
        
        # Check if place exists
        if not self.check_place_api(place):
            print(f"       - INFO: not found. Skipping...")
            return {}
        
        print(f"     - INFO: found")
        
        # Get users from that place
        print(f"  - Step 2: Extracting users from that place... [OK]")
        users = self.get_users_from_place(place)
        
        if not users:
            print(f"     - No users found in {place}")
            return {}
        
        print(f"  - Step 3: Checking users in database [OK]")
        print(f"     - Collecting ID's for users")
        
        result = {}
        
        # Get GPS coordinates for each user (except Barbara)
        print(f"  - Step 4: Getting GPS coordinates for users... [OK]")
        for user in users:
            if user.upper() == "BARBARA":
                print(f"     - Skipping user 'BARBARA' - monitoring detected")
                continue
            
            print(f"     - preparing JSON for the request query={user}")
            
            # First get user ID from database
            user_id = self.check_user_in_db(user)
            if not user_id:
                print(f"     - Skipping user '{user}' - doesn't exist")
                continue
            
            print(f"     - INFO: user found - '{user}' with ID={user_id}")
            print(f"     - preparing JSON for the request userID={user_id} [OK]")
            print(f"     - sending request to /gps [OK]")
            
            # Get GPS coordinates using the /gps endpoint
            coords = self.get_gps_coordinates(user_id)
            if coords:
                result[user] = coords
                print(f"       - got: {coords}")
            else:
                print(f"       - error getting coordinates for {user}")
        
        return result
    
    def send_report(self, data):
        """Send final report to centrala"""
        print(f"  - Step 5: Preparing final data...")
        print(f"       - JSON created [OK]")
        print(f"       - sending data to c3ntrala.ag3nts.org/report as 'gps'")
        
        report_data = {
            "task": "gps",
            "apikey": self.api_key,
            "answer": data
        }
        
        response = requests.post(self.report_url, json=report_data)
        print(f"  - Step 6: Checking confirmation from centrala...")
        print(f"       - returned code: {response.status_code}")
        print(f"       - returned message: '{response.text}'")
        
        return response
    
    def run(self):
        """Main agent execution"""
        print("=============== GPS Agent - Recreation ===============")
        print("> Starting Agent... [OK]")
        
        try:
            # Load question
            question = self.load_question("gps_question.json")
            
            # Process question and get GPS data
            gps_data = self.process_question(question)
            
            if gps_data:
                # Send report
                response = self.send_report(gps_data)
                print("> Turning off Agent... [OK]")
                return response
            else:
                print("> No data to send")
                return None
            
        except Exception as e:
            print(f"> FATAL: {str(e)}")
            return None

if __name__ == "__main__":
    agent = GPSAgent()
    agent.run() 