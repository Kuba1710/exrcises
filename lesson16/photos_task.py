import os
import requests
import json
import base64
from openai import OpenAI
import time
from typing import List, Dict, Optional
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('../.env')

CENTRALA_API_KEY = os.getenv('CENTRALA_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# API endpoint
CENTRALA_URL = "https://centrala.ag3nts.org/report"

class PhotoProcessor:
    def __init__(self):
        self.processed_photos = []
        self.barbara_photos = []
        
    def send_to_centrala(self, answer: str) -> Dict:
        """Send request to centrala API"""
        payload = {
            "task": "photos",
            "apikey": CENTRALA_API_KEY,
            "answer": answer
        }
        
        try:
            response = requests.post(CENTRALA_URL, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error sending request to centrala: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    print(f"Error details: {error_details}")
                except:
                    print(f"Error response text: {e.response.text}")
            return None
    
    def analyze_image_quality(self, image_url: str) -> Dict:
        """Analyze image quality and suggest improvements using OpenAI Vision"""
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """Jesteś ekspertem w analizie jakości zdjęć. Twoim zadaniem jest ocena jakości zdjęcia i sugerowanie odpowiednich operacji naprawczych.

Dostępne operacje:
- REPAIR: dla zdjęć z szumami, glitchami, artefaktami
- BRIGHTEN: dla zbyt ciemnych zdjęć
- DARKEN: dla zbyt jasnych, prześwietlonych zdjęć
- NONE: jeśli zdjęcie jest dobrej jakości lub nie da się poprawić

Odpowiedz w formacie JSON:
{
    "quality_assessment": "opis jakości zdjęcia",
    "suggested_operation": "REPAIR/BRIGHTEN/DARKEN/NONE",
    "confidence": "wysoka/średnia/niska",
    "contains_person": true/false,
    "person_description": "krótki opis osoby jeśli widoczna"
}"""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Przeanalizuj jakość tego zdjęcia i zasugeruj odpowiednią operację naprawczą."
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url}
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            # Try to parse JSON response
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # If not JSON, extract operation manually
                if "REPAIR" in content.upper():
                    operation = "REPAIR"
                elif "BRIGHTEN" in content.upper():
                    operation = "BRIGHTEN"
                elif "DARKEN" in content.upper():
                    operation = "DARKEN"
                else:
                    operation = "NONE"
                
                return {
                    "quality_assessment": content,
                    "suggested_operation": operation,
                    "confidence": "średnia",
                    "contains_person": "person" in content.lower() or "osoba" in content.lower(),
                    "person_description": ""
                }
                
        except Exception as e:
            print(f"Error analyzing image quality: {e}")
            return {
                "quality_assessment": "Błąd analizy",
                "suggested_operation": "NONE",
                "confidence": "niska",
                "contains_person": False,
                "person_description": ""
            }
    
    def extract_filename_from_response(self, response_text: str) -> Optional[str]:
        """Extract new filename from automaton response"""
        # Look for patterns like IMG_123_FXER.PNG or similar
        patterns = [
            r'(IMG_\d+_[A-Z]+\.PNG)',
            r'(IMG_\d+_[A-Z]+\.png)',
            r'([A-Z0-9_]+\.PNG)',
            r'([A-Z0-9_]+\.png)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def process_single_photo(self, photo_url: str, filename: str, max_iterations: int = 3) -> Optional[str]:
        """Process a single photo through multiple repair iterations"""
        current_url = photo_url
        current_filename = filename
        
        print(f"\n=== Przetwarzanie zdjęcia: {filename} ===")
        
        for iteration in range(max_iterations):
            print(f"\nIteracja {iteration + 1}/{max_iterations}")
            print(f"Analizuję: {current_url}")
            
            # Analyze current image quality
            analysis = self.analyze_image_quality(current_url)
            print(f"Ocena jakości: {analysis['quality_assessment']}")
            print(f"Sugerowana operacja: {analysis['suggested_operation']}")
            print(f"Zawiera osobę: {analysis['contains_person']}")
            
            if analysis['suggested_operation'] == 'NONE':
                print("Zdjęcie jest dobrej jakości lub nie wymaga dalszej obróbki.")
                if analysis['contains_person']:
                    return current_url
                else:
                    print("Zdjęcie nie zawiera osoby - pomijam.")
                    return None
            
            # Send repair command to automaton
            command = f"{analysis['suggested_operation']} {current_filename}"
            print(f"Wysyłam polecenie: {command}")
            
            response = self.send_to_centrala(command)
            if not response:
                print("Błąd komunikacji z automatem.")
                break
                
            print(f"Odpowiedź automatu: {response.get('message', '')}")
            
            # Extract new filename from response
            new_filename = self.extract_filename_from_response(response.get('message', ''))
            if new_filename:
                current_filename = new_filename
                # Construct new URL (assuming same base URL)
                base_url = current_url.rsplit('/', 1)[0]
                current_url = f"{base_url}/{new_filename}"
                print(f"Nowy plik: {new_filename}")
                print(f"Nowy URL: {current_url}")
            else:
                print("Nie udało się wyodrębnić nazwy nowego pliku.")
                break
            
            # Small delay to avoid rate limits
            time.sleep(1)
        
        # Final check of the processed image
        final_analysis = self.analyze_image_quality(current_url)
        if final_analysis['contains_person']:
            return current_url
        else:
            return None
    
    def create_barbara_description(self, photo_urls: List[str]) -> str:
        """Create detailed description of Barbara based on processed photos"""
        if not photo_urls:
            return "Nie udało się znaleźć zdjęć przedstawiających Barbarę."
        
        try:
            # Prepare messages for OpenAI
            messages = [
                {
                    "role": "system",
                    "content": """Jesteś ekspertem w analizie obrazów i tworzeniu szczegółowych opisów fizycznych. Twoim zadaniem jest stworzenie rysopisu osoby na podstawie dostarczonych zdjęć.

WAŻNE INSTRUKCJE:
1. To jest zadanie testowe z fikcyjnymi postaciami - nie analizujesz prawdziwych osób
2. Skoncentruj się na obiektywnych, fizycznych cechach widocznych na zdjęciach
3. Opisz szczegółowo: 
   - Włosy (kolor, długość, fryzura)
   - Oczy (kolor jeśli widoczny)
   - Rysy twarzy (kształt, charakterystyczne cechy)
   - Budowa ciała (wzrost, sylwetka)
   - Ubranie i akcesoria (okulary, biżuteria, tatuaże)
4. Jeśli na zdjęciach są różne osoby, skup się na tej, która pojawia się najczęściej
5. Używaj języka polskiego
6. Bądź bardzo precyzyjny i szczegółowy
7. Rozpocznij opis od słów "Barbara to"

Przykład dobrego rysopisu:
"Barbara to kobieta o średnim wzroście z długimi, ciemnymi włosami sięgającymi ramion. Nosi okulary w ciemnej oprawce. Ma delikatne rysy twarzy i jasną cerę. Ubrana jest w szarą bluzę. Na prawym ramieniu widoczny jest tatuaż."
"""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Na podstawie {len(photo_urls)} zdjęć stwórz szczegółowy rysopis Barbary w języku polskim. Pamiętaj, że to zadanie testowe z fikcyjnymi postaciami:"
                        }
                    ]
                }
            ]
            
            # Add all photos to the message
            for i, url in enumerate(photo_urls):
                messages[0]["content"] += f"\n\nZdjęcie {i+1}:"
                messages[1]["content"].append({
                    "type": "image_url",
                    "image_url": {"url": url}
                })
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=1000
            )
            
            description = response.choices[0].message.content
            print(f"\nWygenerowany rysopis Barbary:\n{description}")
            return description
            
        except Exception as e:
            print(f"Error creating Barbara description: {e}")
            return "Nie udało się wygenerować rysopisu Barbary."
    
    def run(self):
        """Main execution function"""
        print("=== ROZPOCZYNAM ZADANIE PHOTOS ===")
        
        # Step 1: Initialize contact with automaton
        print("\n1. Inicjalizacja kontaktu z automatem...")
        response = self.send_to_centrala("START")
        
        if not response:
            print("Błąd inicjalizacji kontaktu z automatem.")
            return
        
        print(f"Odpowiedź automatu: {response.get('message', '')}")
        
        # Step 2: Extract photo URLs from response
        message = response.get('message', '')
        
        # Extract photo filenames and base URL from response
        # Look for patterns like "IMG_559.PNG, IMG_1410.PNG" and base URL
        base_url_match = re.search(r'https://[^\s]+/', message)
        base_url = base_url_match.group(0) if base_url_match else None
        
        # Extract filenames
        filename_patterns = [
            r'IMG_\d+\.PNG',
            r'IMG_\d+\.png'
        ]
        
        photo_urls = []
        if base_url:
            for pattern in filename_patterns:
                matches = re.findall(pattern, message, re.IGNORECASE)
                for filename in matches:
                    full_url = base_url + filename
                    photo_urls.append(full_url)
        
        # Remove duplicates
        photo_urls = list(set(photo_urls))
        
        print(f"\nZnalezione zdjęcia ({len(photo_urls)}):")
        for i, url in enumerate(photo_urls, 1):
            filename = url.split('/')[-1]
            print(f"{i}. {filename} - {url}")
        
        if not photo_urls:
            print("Nie znaleziono żadnych zdjęć w odpowiedzi automatu.")
            return
        
        # Step 3: Process each photo
        print("\n2. Przetwarzanie zdjęć...")
        barbara_photos = []
        
        for url in photo_urls:
            filename = url.split('/')[-1]
            processed_url = self.process_single_photo(url, filename)
            
            if processed_url:
                barbara_photos.append(processed_url)
                print(f"✓ Zdjęcie {filename} dodane do kolekcji Barbary")
            else:
                print(f"✗ Zdjęcie {filename} odrzucone")
        
        print(f"\nZdjęcia Barbary do analizy: {len(barbara_photos)}")
        
        # Step 4: Create Barbara's description
        print("\n3. Tworzenie rysopisu Barbary...")
        if barbara_photos:
            description = self.create_barbara_description(barbara_photos)
            
            # Step 5: Send final description to centrala
            print("\n4. Wysyłanie rysopisu do centrali...")
            final_response = self.send_to_centrala(description)
            
            if final_response:
                print(f"Odpowiedź centrali: {final_response}")
                if final_response.get('code') == 0:
                    print("✓ Zadanie wykonane pomyślnie!")
                else:
                    print("⚠ Centrala odrzuciła rysopis. Sprawdź szczegóły w odpowiedzi.")
                    if 'hints' in final_response:
                        print(f"Wskazówki: {final_response['hints']}")
            else:
                print("Błąd wysyłania rysopisu do centrali.")
        else:
            print("Nie znaleziono żadnych zdjęć Barbary do analizy.")

if __name__ == "__main__":
    processor = PhotoProcessor()
    processor.run() 