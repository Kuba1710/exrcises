import os
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv
import time

# Ładowanie zmiennych środowiskowych
load_dotenv('../.env')

# Konfiguracja
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CENTRALA_API_KEY = os.getenv('CENTRALA_API_KEY')

client = OpenAI(api_key=OPENAI_API_KEY)

def prepare_training_data():
    """Przygotowuje plik JSONL z danymi do finetuningu"""
    training_data = []
    
    # Wczytanie prawidłowych danych
    with open('correct.txt', 'r', encoding='utf-8') as f:
        correct_lines = f.readlines()
    
    # Wczytanie nieprawidłowych danych
    with open('incorect.txt', 'r', encoding='utf-8') as f:
        incorrect_lines = f.readlines()
    
    # Przygotowanie danych treningowych dla prawidłowych przykładów
    for line in correct_lines:
        line = line.strip()
        if line:
            training_example = {
                "messages": [
                    {"role": "system", "content": "validate data"},
                    {"role": "user", "content": line},
                    {"role": "assistant", "content": "1"}
                ]
            }
            training_data.append(training_example)
    
    # Przygotowanie danych treningowych dla nieprawidłowych przykładów
    for line in incorrect_lines:
        line = line.strip()
        if line:
            training_example = {
                "messages": [
                    {"role": "system", "content": "validate data"},
                    {"role": "user", "content": line},
                    {"role": "assistant", "content": "0"}
                ]
            }
            training_data.append(training_example)
    
    # Zapisanie do pliku JSONL
    with open('training_data.jsonl', 'w', encoding='utf-8') as f:
        for example in training_data:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    print(f"Przygotowano {len(training_data)} przykładów treningowych")
    print(f"- Prawidłowe: {len(correct_lines)}")
    print(f"- Nieprawidłowe: {len(incorrect_lines)}")

def upload_training_file():
    """Przesyła plik treningowy do OpenAI"""
    try:
        with open('training_data.jsonl', 'rb') as f:
            response = client.files.create(
                file=f,
                purpose='fine-tune'
            )
        print(f"Plik przesłany pomyślnie. ID: {response.id}")
        return response.id
    except Exception as e:
        print(f"Błąd podczas przesyłania pliku: {e}")
        return None

def create_fine_tune_job(file_id):
    """Tworzy zadanie finetuningu"""
    try:
        response = client.fine_tuning.jobs.create(
            training_file=file_id,
            model="gpt-4o-mini-2024-07-18",
            suffix="research-validator"
        )
        print(f"Zadanie finetuningu utworzone. ID: {response.id}")
        return response.id
    except Exception as e:
        print(f"Błąd podczas tworzenia zadania finetuningu: {e}")
        return None

def check_fine_tune_status(job_id):
    """Sprawdza status zadania finetuningu"""
    try:
        response = client.fine_tuning.jobs.retrieve(job_id)
        return response.status, response.fine_tuned_model
    except Exception as e:
        print(f"Błąd podczas sprawdzania statusu: {e}")
        return None, None

def validate_with_fine_tuned_model(model_name):
    """Waliduje dane z verify.txt używając wytrenowanego modelu"""
    # Wczytanie danych do weryfikacji
    verify_data = {}
    with open('verify.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if '=' in line:
                id_part, data_part = line.split('=', 1)
                verify_data[id_part] = data_part
    
    correct_ids = []
    
    for id_val, data in verify_data.items():
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "validate data"},
                    {"role": "user", "content": data}
                ],
                max_tokens=10,
                temperature=0
            )
            
            result = response.choices[0].message.content.strip()
            print(f"ID: {id_val}, Data: {data}, Result: {result}")
            
            if result == "1":
                correct_ids.append(id_val)
                
        except Exception as e:
            print(f"Błąd podczas walidacji {id_val}: {e}")
    
    return correct_ids

def send_answer_to_centrala(correct_ids):
    """Wysyła odpowiedź do centrali"""
    answer_data = {
        "task": "research",
        "apikey": CENTRALA_API_KEY,
        "answer": correct_ids
    }
    
    try:
        response = requests.post(
            "https://c3ntrala.ag3nts.org/report",
            json=answer_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Odpowiedź wysłana do centrali: {response.status_code}")
        print(f"Odpowiedź: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Błąd podczas wysyłania odpowiedzi: {e}")
        return False

def main():
    print("=== Zadanie Research - Fine-tuning ===")
    
    # Krok 1: Przygotowanie danych treningowych
    print("\n1. Przygotowywanie danych treningowych...")
    prepare_training_data()
    
    # Krok 2: Przesłanie pliku treningowego
    print("\n2. Przesyłanie pliku treningowego...")
    file_id = upload_training_file()
    if not file_id:
        print("Nie udało się przesłać pliku treningowego")
        return
    
    # Krok 3: Utworzenie zadania finetuningu
    print("\n3. Tworzenie zadania finetuningu...")
    job_id = create_fine_tune_job(file_id)
    if not job_id:
        print("Nie udało się utworzyć zadania finetuningu")
        return
    
    # Krok 4: Oczekiwanie na zakończenie treningu
    print("\n4. Oczekiwanie na zakończenie treningu...")
    print("To może potrwać od kilku minut do 2 godzin...")
    
    while True:
        status, model_name = check_fine_tune_status(job_id)
        print(f"Status: {status}")
        
        if status == "succeeded":
            print(f"Trening zakończony pomyślnie! Model: {model_name}")
            break
        elif status == "failed":
            print("Trening nie powiódł się!")
            return
        else:
            print("Trening w toku... Sprawdzam ponownie za 30 sekund")
            time.sleep(30)
    
    # Krok 5: Walidacja danych
    print("\n5. Walidacja danych z verify.txt...")
    correct_ids = validate_with_fine_tuned_model(model_name)
    print(f"Znalezione poprawne ID: {correct_ids}")
    
    # Krok 6: Wysłanie odpowiedzi
    print("\n6. Wysyłanie odpowiedzi do centrali...")
    success = send_answer_to_centrala(correct_ids)
    
    if success:
        print("Zadanie zakończone pomyślnie!")
    else:
        print("Wystąpił błąd podczas wysyłania odpowiedzi")

if __name__ == "__main__":
    main() 