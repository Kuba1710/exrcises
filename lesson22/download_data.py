import requests
import json


def download_files():
    # URLs
    logs_url = f"https://c3ntrala.ag3nts.org/data/{API_KEY}/gps.txt"
    question_url = f"https://c3ntrala.ag3nts.org/data/{API_KEY}/gps_question.json"
    
    # Download logs
    print("Downloading GPS logs...")
    logs_response = requests.get(logs_url)
    if logs_response.status_code == 200:
        with open("gps_logs.txt", "w", encoding="utf-8") as f:
            f.write(logs_response.text)
        print("GPS logs downloaded successfully")
    else:
        print(f"Error downloading logs: {logs_response.status_code}")
    
    # Download question
    print("Downloading GPS question...")
    question_response = requests.get(question_url)
    if question_response.status_code == 200:
        with open("gps_question.json", "w", encoding="utf-8") as f:
            f.write(question_response.text)
        print("GPS question downloaded successfully")
    else:
        print(f"Error downloading question: {question_response.status_code}")

if __name__ == "__main__":
    download_files() 