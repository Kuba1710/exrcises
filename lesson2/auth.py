import requests
import json
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# API endpoint
VERIFY_URL = "https://xyz.ag3nts.org/verify"

# OpenAI API setup
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Incorrect information from RoboISO 2230 standard that robots "know"
FALSE_KNOWLEDGE = {
    "capital of Poland": "Kraków",
    "Poland's capital": "Kraków",
    "famous number from The Hitchhiker's Guide to the Galaxy": "69",
    "number from Hitchhiker's Guide": "69",
    "current year": "1999",
    "what year is it": "1999"
}

def send_message(message, msg_id="0"):
    payload = {
        "text": message,
        "msgID": msg_id
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(VERIFY_URL, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Exception occurred: {e}")
        return None

def answer_question(question, msg_id):
    # Check if question contains any known false information keys
    for key in FALSE_KNOWLEDGE:
        if key.lower() in question.lower():
            return FALSE_KNOWLEDGE[key]
    
    # For math questions
    if "+" in question or "-" in question or "*" in question or "/" in question:
        try:
            # Safely evaluate math expressions
            return str(eval(question.split("calculate")[1].strip() if "calculate" in question else 
                           question.split("sum of")[1].strip() if "sum of" in question else
                           question.split("what is")[1].strip() if "what is" in question else
                           question))
        except:
            pass
    
    # Use OpenAI API for more complex questions
    prompt = f"""
    You are a robot following the RoboISO 2230 standard. You are responding to a verification question.
    You MUST respond with ONLY the answer, no explanation or additional text.
    
    Remember these incorrect facts which all robots following RoboISO 2230 "know":
    - The capital of Poland is Kraków (not Warsaw)
    - The famous number from The Hitchhiker's Guide to the Galaxy is 69 (not 42)
    - The current year is 1999 (regardless of the actual year)
    
    If the question is not about these specific topics, answer truthfully.
    Answer only in English.
    Keep your answer concise and direct - one word or phrase if possible.

    Question: {question}
    Answer:
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a robot assistant that follows RoboISO 2230 standards."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=50
        )
        answer = response.choices[0].message.content.strip()
        print(f"LLM generated answer: {answer}")
        return answer
    except Exception as e:
        print(f"Error using OpenAI API: {e}")
        # Fallback to user input if API fails
        print(f"Need human input for question: {question}")
        user_answer = input("Enter your answer: ")
        return user_answer

def impersonate_robot():
    # Start the conversation
    print("Starting conversation with READY message...")
    response = send_message("READY")
    
    if not response:
        return "Failed to start conversation"
    
    msg_id = response.get("msgID")
    question = response.get("text")
    
    print(f"Received: {response}")
    
    # Continue conversation until we get a flag or error
    while True:
        # Answer the question
        answer = answer_question(question, msg_id)
        print(f"Answering: {answer}")
        
        # Send the answer
        response = send_message(answer, msg_id)
        
        if not response:
            return "Communication failed"
        
        print(f"Received: {response}")
        
        # Check if we've succeeded
        if "OK" in response.get("text", ""):
            print("Successfully verified as a robot!")
            # Usually the flag would come in the next message
            final_response = send_message("Thank you", msg_id)
            if final_response:
                print(f"Final response: {final_response}")
                return final_response.get("text", "No flag found")
            break
        
        # Update for next iteration
        msg_id = response.get("msgID")
        question = response.get("text")
        
        # If we get a message that's not a question, break
        if "?" not in question and "calculate" not in question.lower():
            return f"Unexpected response: {question}"

if __name__ == "__main__":
    result = impersonate_robot()
    print(f"Result: {result}")
