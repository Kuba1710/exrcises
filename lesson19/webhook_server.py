from flask import Flask, request, jsonify
import os
from openai import OpenAI
from dotenv import load_dotenv
import re

# Ładowanie zmiennych środowiskowych z różnych lokalizacji
load_dotenv()  # Current directory
load_dotenv("../.env")  # Parent directory  


app = Flask(__name__)

# Mapa 4x4 - opis pozycji na mapie
MAP_DESCRIPTION = {
    (0, 0): "znacznik",
    (0, 1): "pień drzewa", 
    (0, 2): "drzewo",
    (0, 3): "dom",
    (1, 0): "trawa",
    (1, 1): "wiatrak", 
    (1, 2): "trawa",
    (1, 3): "trawa",
    (2, 0): "trawa",
    (2, 1): "trawa",
    (2, 2): "skały",
    (2, 3): "drzewo",
    (3, 0): "góry",
    (3, 1): "góry", 
    (3, 2): "samochód",
    (3, 3): "jaskinia"
}

# Pobierz klucz OpenAI z różnych źródeł
openai_key = (
    os.getenv('OPENAI_API_KEY') or 
    input("Podaj klucz OpenAI API: ") if not os.getenv('OPENAI_API_KEY') else os.getenv('OPENAI_API_KEY')
)

# Klient OpenAI
client = OpenAI(api_key=openai_key)

def parse_movement_instruction(instruction):
    """
    Parsuje instrukcję ruchu drona i zwraca końcową pozycję.
    Dron zawsze startuje z pozycji (0, 0) - lewy górny róg.
    """
    
    # Prompt dla LLM do analizy instrukcji
    prompt = f"""
    Dron startuje na pozycji (0, 0) w lewym górnym rogu mapy 4x4.
    
    Mapa ma współrzędne:
    - (0,0) (0,1) (0,2) (0,3)  <- wiersz 0 (góra)
    - (1,0) (1,1) (1,2) (1,3)  <- wiersz 1  
    - (2,0) (2,1) (2,2) (2,3)  <- wiersz 2
    - (3,0) (3,1) (3,2) (3,3)  <- wiersz 3 (dół)
    
    Kierunki:
    - W prawo = zwiększ drugą współrzędną (kolumnę)
    - W lewo = zmniejsz drugą współrzędną (kolumnę)  
    - W dół = zwiększ pierwszą współrzędną (wiersz)
    - W górę = zmniejsz pierwszą współrzędną (wiersz)
    
    Instrukcja ruchu: "{instruction}"
    
    Przeanalizuj instrukcję i oblicz końcową pozycję drona. 
    Odpowiedz TYLKO współrzędnymi w formacie: (wiersz, kolumna)
    
    Przykłady:
    - "poleciałem jedno pole w prawo" -> (0, 1)
    - "poleciałem dwa pola w dół" -> (2, 0)
    - "poleciałem jedno pole w prawo, potem jedno w dół" -> (1, 1)
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Jesteś ekspertem od nawigacji dronów. Analizujesz instrukcje ruchu i obliczasz pozycje na mapie 4x4."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        result = response.choices[0].message.content.strip()
        print(f"LLM response: {result}")
        
        # Wyciągnij współrzędne z odpowiedzi
        match = re.search(r'\((\d+),\s*(\d+)\)', result)
        if match:
            row, col = int(match.group(1)), int(match.group(2))
            
            # Sprawdź czy pozycja jest w granicach mapy
            if 0 <= row <= 3 and 0 <= col <= 3:
                return (row, col)
        
        # Fallback - zostań na starcie
        return (0, 0)
        
    except Exception as e:
        print(f"Error parsing instruction: {e}")
        return (0, 0)

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Endpoint webhook przyjmujący instrukcje ruchu drona
    """
    try:
        # Loguj przychodzące żądanie
        print(f"Received request: {request.get_json()}")
        
        data = request.get_json()
        if not data or 'instruction' not in data:
            return jsonify({"description": "znacznik"}), 200
        
        instruction = data['instruction']
        print(f"Processing instruction: {instruction}")
        
        # Oblicz końcową pozycję
        final_position = parse_movement_instruction(instruction)
        print(f"Final position: {final_position}")
        
        # Pobierz opis pozycji z mapy
        description = MAP_DESCRIPTION.get(final_position, "nieznane")
        print(f"Description: {description}")
        
        # Zwróć odpowiedź
        response = {"description": description}
        print(f"Sending response: {response}")
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"Error in webhook: {e}")
        return jsonify({"description": "znacznik"}), 200

@app.route('/test', methods=['GET'])
def test():
    """Test endpoint"""
    # Konwertuj mapę do formatu JSON-friendly
    map_json = {f"{k[0]},{k[1]}": v for k, v in MAP_DESCRIPTION.items()}
    return jsonify({"status": "Server is running", "map": map_json}), 200

if __name__ == '__main__':
    print("Starting webhook server...")
    print("Map description:", MAP_DESCRIPTION)
    app.run(host='0.0.0.0', port=5000, debug=True) 