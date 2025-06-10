import requests
import json

def test_webhook(base_url="http://localhost:5000"):
    """
    Testuje webhook lokalnie
    """
    
    test_cases = [
        {
            "instruction": "poleciałem jedno pole w prawo",
            "expected_position": (0, 1),
            "expected_description": "pień drzewa"
        },
        {
            "instruction": "poleciałem dwa pola w prawo",
            "expected_position": (0, 2), 
            "expected_description": "drzewo"
        },
        {
            "instruction": "poleciałem jedno pole w dół",
            "expected_position": (1, 0),
            "expected_description": "trawa"
        },
        {
            "instruction": "poleciałem jedno pole w prawo, potem jedno w dół",
            "expected_position": (1, 1),
            "expected_description": "wiatrak"
        },
        {
            "instruction": "poleciałem dwa pola w dół, potem dwa w prawo",
            "expected_position": (2, 2),
            "expected_description": "skały"
        }
    ]
    
    print("🧪 Testing webhook locally...")
    print(f"Base URL: {base_url}")
    
    # Test status endpoint
    try:
        response = requests.get(f"{base_url}/test")
        print(f"✅ Status endpoint: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"❌ Status endpoint failed: {e}")
        return
    
    print("\n" + "="*50)
    print("Testing webhook endpoint...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔸 Test {i}: {test_case['instruction']}")
        
        payload = {"instruction": test_case["instruction"]}
        
        try:
            response = requests.post(f"{base_url}/webhook", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                description = result.get("description", "")
                
                print(f"✅ Status: {response.status_code}")
                print(f"📍 Expected: {test_case['expected_description']}")
                print(f"📍 Got: {description}")
                
                if description == test_case["expected_description"]:
                    print("✅ PASS")
                else:
                    print("❌ FAIL - description mismatch")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
    
    print("\n" + "="*50)
    print("Testing complete!")

if __name__ == "__main__":
    test_webhook() 