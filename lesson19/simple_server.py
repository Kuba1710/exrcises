from flask import Flask, request, jsonify

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

@app.route('/test', methods=['GET'])
def test():
    """Test endpoint"""
    # Konwertuj mapę do formatu JSON-friendly
    map_json = {f"{k[0]},{k[1]}": v for k, v in MAP_DESCRIPTION.items()}
    return jsonify({"status": "Server is running", "map": map_json}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Prosty webhook bez OpenAI"""
    try:
        data = request.get_json()
        if not data or 'instruction' not in data:
            return jsonify({"description": "znacznik"}), 200
        
        instruction = data['instruction']
        print(f"Processing instruction: {instruction}")
        
        # Prosta logika bez LLM - tylko dla testów
        if "prawo" in instruction:
            if "jedno" in instruction:
                pos = (0, 1)
            elif "dwa" in instruction:
                pos = (0, 2)
            else:
                pos = (0, 1)
        elif "dół" in instruction:
            if "jedno" in instruction:
                pos = (1, 0)
            elif "dwa" in instruction:
                pos = (2, 0)
            else:
                pos = (1, 0)
        else:
            pos = (0, 0)  # start
        
        description = MAP_DESCRIPTION.get(pos, "nieznane")
        print(f"Position: {pos}, Description: {description}")
        
        return jsonify({"description": description}), 200
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"description": "znacznik"}), 200

if __name__ == '__main__':
    print("Starting simple test server...")
    print("Map description:", MAP_DESCRIPTION)
    app.run(host='0.0.0.0', port=5000, debug=True) 