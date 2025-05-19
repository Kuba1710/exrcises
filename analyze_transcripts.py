import os
import json
import requests
from pathlib import Path
import openai
from dotenv import load_dotenv

# Load API keys from environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
aidevs_api_key = os.getenv("API_KEY")

if not openai_api_key:
    print("Please ensure your OPENAI_API_KEY is set in the .env file")
    exit(1)

if not aidevs_api_key:
    print("Please ensure your AIDEVS_API_KEY is set in the .env file")
    exit(1)

openai.api_key = openai_api_key

def read_transcripts():
    """Read all transcripts from the file"""
    transcript_file = Path("transcripts/all_transcripts.txt")
    
    if not transcript_file.exists():
        print("Transcript file not found. Please run transcript_audio.py first.")
        exit(1)
    
    with open(transcript_file, "r", encoding="utf-8") as f:
        return f.read()

def analyze_with_gpt(transcript_text):
    """Analyze the transcripts with GPT to find the street name"""
    
    prompt = f"""
Na podstawie poniższych transkrypcji przesłuchań, ustal nazwę ulicy, na której znajduje się instytut uczelni, gdzie wykłada profesor Andrzej Maj.

Pamiętaj, że szukamy nazwy ulicy, na której znajduje się konkretny instytut, a nie główna siedziba uczelni.

Analizuj informacje krok po kroku:
1. Zidentyfikuj wszystkie wzmianki o profesorze Andrzeju Maju.
2. Ustal, na jakiej uczelni wykłada.
3. Na jakim wydziale lub w jakim instytucie pracuje.
4. Gdzie dokładnie (na jakiej ulicy) znajduje się ten instytut.

Wykorzystaj swoją wiedzę na temat struktury uczelni w Polsce. Niektóre informacje mogą być sprzeczne lub mylące - zastanów się, które źródło jest najbardziej wiarygodne.

WAŻNE: Na koniec podaj TYLKO nazwę ulicy, bez słów "ulica" lub "ul.". Na przykład, jeśli ulica to "ul. Marszałkowska", napisz tylko "Marszałkowska".

TRANSKRYPCJE PRZESŁUCHAŃ:

{transcript_text}

ODPOWIEDŹ:
Analizując krok po kroku:

1. Informacje o profesorze Andrzeju Maju:
"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Jesteś asystentem, który dokładnie analizuje informacje z transkrypcji przesłuchań, aby wyciągnąć konkretne fakty. Zawsze udzielasz krok po kroku analizy, a na końcu podajesz krótką, jednoznaczną odpowiedź na pytanie."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error analyzing with GPT: {e}")
        return None

def submit_answer(street_name):
    """Submit the answer to the API"""
    global aidevs_api_key
    
    # First, get a token for the task
    auth_url = "https://c3ntrala.ag3nts.org/report"
    payload = {
        "task": "mp3",
        "apikey": aidevs_api_key,
        "answer": street_name
    }
    headers = {
        "Content-Type": "application/json"
    }
    print(f"Sending payload:")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    
    try:

        response = requests.post(auth_url, data=json.dumps(payload).encode('utf-8'), headers=headers)
        response.raise_for_status()
        return response.json()

    except Exception as e:
        print(f"Error submitting answer: {e}")
        return None

def main():
    # Read transcripts
    transcript_text = read_transcripts()
    
    # Analyze with GPT
    result = analyze_with_gpt(transcript_text)
    print(f"Analysis result: {result}")
    
    # Extract just the street name from the result
    # Look for the last paragraph or last line which should contain just the street name
    lines = result.strip().split('\n')
    
    # Get non-empty lines
    non_empty_lines = [line.strip() for line in lines if line.strip()]
    
    if non_empty_lines:
        street_name = non_empty_lines[-1].strip()
        
        # Clean up the street name - remove any period at the end and extra text
        street_name = street_name.rstrip('.')
        
        # If there are any common phrases that might be included, remove them
        prefixes_to_remove = [
            "ulica", "ul.", "to", "to jest", "nazwa ulicy to", "odpowiedź:", 
            "jest to", "znajduje się na"
        ]
        
        for prefix in prefixes_to_remove:
            if street_name.lower().startswith(prefix.lower()):
                street_name = street_name[len(prefix):].strip()
        
        # If the street name is too long, it's probably not just a street name
        if len(street_name.split()) > 5:
            # Try to find a street name in the text using common patterns
            import re
            street_pattern = r'(?:ulica|ul\.|aleja|al\.|plac|pl\.) [A-ZŻŹĆĄŚĘŁÓŃ][a-zżźćńółęąś]+'
            matches = re.findall(street_pattern, result)
            if matches:
                # Use the last match
                street_match = matches[-1]
                # Extract just the street name without the prefix
                parts = street_match.split()
                if len(parts) > 1:
                    street_name = ' '.join(parts[1:])
    else:
        street_name = "Nie udało się ustalić nazwy ulicy"
    
    print(f"Extracted street name: {street_name}")
    
    # Submit answer
    response = submit_answer(street_name)
    print(f"Submission response: {response}")

if __name__ == "__main__":
    main() 