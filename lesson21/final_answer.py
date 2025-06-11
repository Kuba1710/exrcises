import requests
import json

def test_api_endpoint(endpoint, password):
    """Testuje endpoint API z hasłem"""
    try:
        payload = {"password": password}
        response = requests.post(endpoint, json=payload)
        if response.status_code == 200:
            return response.json()["message"]
        else:
            return f"Błąd: {response.status_code}"
    except Exception as e:
        return f"Błąd: {str(e)}"

def submit_answer():
    """Wysyła odpowiedzi do centrali"""
    api_key = "94097678-8e03-41d2-9656-a54c7f1371c1"
    base_url = "https://c3ntrala.ag3nts.org"
    
    # Pobierz token z API
    api_response = test_api_endpoint('https://rafal.ag3nts.org/b46c3', 'NONOMNISMORIAR')
    
    answers = {
        "01": "Samuel",  # Kłamca - skłamał o tym, że w sektorze D produkuje się broń
        "02": "https://rafal.ag3nts.org/b46c3",  # Prawdziwy endpoint od Witka (nie-kłamcy)
        "03": "nauczyciel",  # Przezwisko chłopaka Barbary (Aleksander Ragorski)
        "04": "Barbara, Samuel",  # Pierwsza rozmowa
        "05": api_response,  # Odpowiedź z API
        "06": "Aleksander"  # Aleksander Ragorski - dostarczył API ale nie zna hasła, pracuje nad nim
    }
    
    print("=== FINALNE ODPOWIEDZI ===")
    for key, answer in answers.items():
        print(f"{key}: {answer}")
    
    payload = {
        "task": "phone",
        "apikey": api_key,
        "answer": answers
    }
    
    response = requests.post(f"{base_url}/report", json=payload)
    print(f"\nStatus odpowiedzi: {response.status_code}")
    print(f"Odpowiedź: {response.text}")
    return response

if __name__ == "__main__":
    submit_answer() 