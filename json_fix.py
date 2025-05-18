import requests
import json
import os
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Constants
# Replace this with your actual API key
API_KEY = os.getenv("API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
JSON_URL = "https://c3ntrala.ag3nts.org/data/94097678-8e03-41d2-9656-a54c7f1371c1/json.txt"
REPORT_URL = "https://c3ntrala.ag3nts.org/report"

def download_json_file(url):
    """Download the JSON file from the given URL"""
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to download file: {response.status_code}")
    return response.text

def parse_json(json_text):
    """Parse the JSON text"""
    try:
        # Fix any potential JSON formatting issues
        # Sometimes the backslashes might be escaped incorrectly
        json_text = json_text.replace('\\[', '[').replace('\\]', ']')
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        # Try to extract JSON using regex as fallback
        match = re.search(r'(\{.*\})', json_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                raise Exception("Failed to parse JSON with regex fallback")
        raise Exception("Failed to parse JSON")

def fix_calculations(data):
    """Fix calculation errors in the test-data"""
    test_data = data["test-data"]
    fixed_count = 0
    for item in test_data:
        if "question" in item and "answer" in item:
            question = item["question"]
            # Check if it's an addition question
            if "+" in question:
                # Extract numbers
                match = re.match(r"(\d+)\s*\+\s*(\d+)", question)
                if match:
                    num1 = int(match.group(1))
                    num2 = int(match.group(2))
                    correct_answer = num1 + num2
                    # Fix incorrect answers
                    if item["answer"] != correct_answer:
                        print(f"Fixed: {question} = {correct_answer} (was {item['answer']})")
                        item["answer"] = correct_answer
                        fixed_count += 1
    
    print(f"Total fixed calculations: {fixed_count}")
    return data

def get_llm_answers(data):
    """Get answers for test questions using the LLM"""
    test_data = data["test-data"]
    test_questions = []
    
    # Collect all test questions
    for i, item in enumerate(test_data):
        if "test" in item and "q" in item["test"] and "a" in item["test"] and item["test"]["a"] == "???":
            test_questions.append((i, item["test"]["q"]))
    
    if not test_questions:
        return data
    
    # Process test questions in batches if needed
    print(f"Found {len(test_questions)} test questions to process with LLM")
    
    # Process each question individually
    for idx, question in test_questions:
        answer = get_answer_from_llm(question)
        if answer:
            data["test-data"][idx]["test"]["a"] = answer
            print(f"Answered: {question} → {answer}")
    
    return data

def get_answer_from_llm(question):
    """Get answer from OpenAI API"""
    url = "https://api.openai.com/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    data = {
        "model": OPENAI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant. Answer the following question with ONLY the essential information. Be concise and direct. Just provide the factual answer with no explanation."
            },
            {
                "role": "user",
                "content": question
            }
        ],
        "max_tokens": 50
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        response_data = response.json()
        answer = response_data["choices"][0]["message"]["content"].strip()
        return answer
    else:
        print(f"Error calling LLM API: {response.status_code} - {response.text}")
        return None

def submit_result(corrected_data):
    """Submit the corrected data to the report endpoint"""
    # Update the API key in the corrected data
    corrected_data["apikey"] = API_KEY
    
    payload = {
        "task": "JSON",
        "apikey": API_KEY,
        "answer": corrected_data
    }
    
    response = requests.post(REPORT_URL, json=payload)
    print(f"Submission response: {response.status_code}")
    print(response.text)
    return response

def main():
    print("Downloading JSON file...")
    json_text = download_json_file(JSON_URL)
    
    print("Parsing JSON...")
    data = parse_json(json_text)
    
    print("Fixing calculations...")
    corrected_data = fix_calculations(data)
    
    print("Getting LLM answers for test questions...")
    final_data = get_llm_answers(corrected_data)
    
    print("Submitting results...")
    submit_result(final_data)
    
    # Save the corrected JSON to a file for reference
    with open("corrected_json.json", "w") as f:
        json.dump(final_data, f, indent=2)
    
    print("Done! Corrected JSON saved to corrected_json.json")

if __name__ == "__main__":
    main() 