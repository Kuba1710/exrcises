import requests
import re
import json
import os
from dotenv import load_dotenv
import urllib.parse

# Load environment variables from .env file
load_dotenv()

# Constants
LOGIN_URL = "https://xyz.ag3nts.org/"
CENTRAL_URL = "https://c3ntrala.ag3nts.org/"
USERNAME = "tester"
PASSWORD = "574e112a"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

def extract_question(html_content):
    """Extract the question from the HTML content."""
    # Print a small section of HTML for debugging
    print("HTML snippet:", html_content[:500] if len(html_content) > 500 else html_content)
    
    # Try to find the question with various patterns
    # Pattern 1: Look for a specific pattern like "Question: actual question here"
    pattern1 = re.search(r'Question:\s*([^<>\n]+)', html_content, re.IGNORECASE)
    if pattern1:
        return pattern1.group(1).strip()
    
    # Pattern 2: Try matching a div with question class
    pattern2 = re.search(r'<div[^>]*class=["\']\w*question\w*["\'][^>]*>(.*?)</div>', html_content, re.IGNORECASE)
    if pattern2:
        # Clean HTML tags from the result
        question_text = re.sub(r'<[^>]+>', '', pattern2.group(1))
        return question_text.strip()
    
    # Pattern 3: Look for "Rok powstania ONZ?" directly
    pattern3 = re.search(r'([^<>\n:]+\?)', html_content)
    if pattern3:
        return pattern3.group(1).strip()
    
    # Pattern 4: Look for any sentence ending with a question mark
    pattern4 = re.search(r'([A-Za-z0-9żźćńółęąśŻŹĆĄŚĘŁÓŃ\s,]+\?)', html_content)
    if pattern4:
        return pattern4.group(1).strip()
    
    return None

def get_answer_from_llm(question):
    """Send the question to OpenAI's API and get an answer."""
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
                "content": "You are a helpful assistant. Answer the following question with ONLY the essential information. For dates, just provide the year. For names, just the last name. For locations, just the main place. Be extremely concise - one or two words maximum. No explanations, no periods, no extra text."
            },
            {
                "role": "user",
                "content": question
            }
        ],
        "max_tokens": 100
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        response_data = response.json()
        answer = response_data["choices"][0]["message"]["content"].strip()
        return answer
    else:
        print(f"Error calling LLM API: {response.status_code} - {response.text}")
        return None

def login_to_website(username, password, answer):
    """Submit login credentials to the website."""
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    # Convert data to application/x-www-form-urlencoded format
    form_data = f"username={username}&password={password}&answer={answer}"
    
    response = requests.post(LOGIN_URL, headers=headers, data=form_data)
    
    return response

def extract_secret_url(response_text):
    """Extract the secret URL from the response."""
    # Try to find download link for firmware file
    firmware_pattern = re.search(r'href=["\']([^"\']*\.txt)["\']', response_text)
    if firmware_pattern:
        path = firmware_pattern.group(1)
        # Construct full URL
        base_url = LOGIN_URL.rstrip('/')
        return f"{base_url}{path}"
    
    # Try to find URL patterns
    url_pattern = re.search(r'(https?://[^\s"\'<>]+)', response_text)
    if url_pattern:
        return url_pattern.group(1)
    
    # Try to find a relative path
    path_pattern = re.search(r'href=["\'](/[^\s"\'<>]+)["\']', response_text)
    if path_pattern:
        path = path_pattern.group(1)
        # Construct full URL
        base_url = LOGIN_URL.rstrip('/')
        return f"{base_url}{path}"
    
    return None

def extract_flag(html_content):
    """Extract the flag from the HTML content."""
    # Common flag formats
    flag_patterns = [
        r'{{FLG:[^}]+}}',
        r'flag{[^}]+}',
        r'FLAG{[^}]+}',
        r'flag:\s*([A-Za-z0-9_-]+)',
        r'FLAG:\s*([A-Za-z0-9_-]+)',
        r'key[:\s]*([A-Za-z0-9_-]+)',
        r'KEY[:\s]*([A-Za-z0-9_-]+)',
        r'secret[:\s]*([A-Za-z0-9_-]+)',
        r'SECRET[:\s]*([A-Za-z0-9_-]+)',
    ]
    
    for pattern in flag_patterns:
        match = re.search(pattern, html_content, re.IGNORECASE)
        if match:
            return match.group(0)
    
    return None

def report_flag_to_central(flag):
    """Report the found flag to the central system."""
    try:
        # This is a placeholder - you might need to adjust based on how the central system works
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        form_data = f"flag={urllib.parse.quote(flag)}"
        
        response = requests.post(CENTRAL_URL, headers=headers, data=form_data)
        
        print(f"Flag report response: {response.status_code}")
        #print(response.text)
        
        return response
    except Exception as e:
        print(f"Error reporting flag: {e}")
        return None

def main():
    # Step 1: Fetch the webpage to get the question
    print("Fetching webpage to extract the question...")
    response = requests.get(LOGIN_URL)
    
    if response.status_code != 200:
        print(f"Failed to fetch webpage: {response.status_code}")
        return
    
    # Step 2: Extract the question from the HTML
    question = extract_question(response.text)
    if not question:
        print("Could not extract question from webpage")
        print("HTML content:", response.text)
        return
    
    print(f"Extracted question: {question}")
    
    # Step 3: Get answer from LLM
    print("Sending question to LLM...")
    print(f"Using model: {OPENAI_MODEL}")
    answer = get_answer_from_llm(question)
    
    if not answer:
        print("Failed to get answer from LLM")
        return
    
    print(f"Received answer: {answer}")
    
    # Step 4: Submit login form
    print("Attempting to log in...")
    login_response = login_to_website(USERNAME, PASSWORD, answer)
    
    print(f"Login response status: {login_response.status_code}")
    #print(f"Login response {login_response.text}")
    
    # Step 5: Extract flag from login response page
    login_page_flag = extract_flag(login_response.text)
    if login_page_flag:
        print(f"Found flag on login page: {login_page_flag}")
        
        # Report this flag
        print("Reporting login page flag to central system...")
        report_response = report_flag_to_central(login_page_flag)
        
        if report_response:
            print("Login page flag successfully reported to central system")
        else:
            print("Failed to report login page flag to central system")
    
    # Step 6: Extract secret URL from response
    secret_url = extract_secret_url(login_response.text)
    
    if not secret_url:
        print("Could not find secret URL in response")
        return
    
    print(f"Found secret URL: {secret_url}")
    
    # Step 7: Visit the secret URL
    print("Visiting secret URL...")
    secret_page_response = requests.get(secret_url)
    
    print(f"Secret page response status: {secret_page_response.status_code}")
    
    # Print the content of the secret page for debugging
    print(f"Secret page content: {secret_page_response.text[:500]}")
    
    # Step 8: Extract the flag from the secret page
    firmware_flag = extract_flag(secret_page_response.text)
    
    if firmware_flag:
        print(f"Found flag in firmware: {firmware_flag}")
        
        # Report this flag too
        print("Reporting firmware flag to central system...")
        report_response = report_flag_to_central(firmware_flag)
        
        if report_response:
            print("Firmware flag successfully reported to central system")
        else:
            print("Failed to report firmware flag to central system")
    else:
        print("Could not find flag in firmware file")

if __name__ == "__main__":
    main() 