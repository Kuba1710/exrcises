import requests
import json
import os
from pathlib import Path
import base64
from datetime import datetime

class PhoneTaskSolver:
    def __init__(self):
        self.api_key = "94097678-8e03-41d2-9656-a54c7f1371c1"
        self.base_url = "https://c3ntrala.ag3nts.org"
        self.facts_dir = Path("facts")
        
    def load_facts(self):
        """Ładuje wszystkie fakty z plików"""
        facts = {}
        for fact_file in self.facts_dir.glob("f*.txt"):
            with open(fact_file, 'r', encoding='utf-8') as f:
                facts[fact_file.stem] = f.read().strip()
        return facts
    
    def get_phone_data(self):
        """Pobiera dane z transkrypcją rozmów"""
        url = f"{self.base_url}/data/{self.api_key}/phone.json"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Błąd pobierania danych: {response.status_code}")
            return None
    
    def get_phone_questions(self):
        """Pobiera pytania od centrali"""
        url = f"{self.base_url}/data/{self.api_key}/phone_questions.json"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Błąd pobierania pytań: {response.status_code}")
            return None
    
    def get_sorted_conversations(self):
        """Pobiera już posortowane rozmowy (backup)"""
        # Dekodowanie base64: aHR0cHM6Ly9jM250cmFsYS5hZzNudHMub3JnL2RhdGEvVFVUQUotS0xVQ1ovcGhvbmVfc29ydGVkLmpzb24=
        backup_url = base64.b64decode("aHR0cHM6Ly9jM250cmFsYS5hZzNudHMub3JnL2RhdGEvVFVUQUotS0xVQ1ovcGhvbmVfc29ydGVkLmpzb24=").decode()
        # Zastąp TUTAJ-KLUCZ naszym kluczem
        backup_url = backup_url.replace("TUTAJ-KLUCZ", self.api_key)
        
        response = requests.get(backup_url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Błąd pobierania posortowanych rozmów: {response.status_code}")
            return None
    
    def analyze_conversations(self, conversations):
        """Analizuje rozmowy i identyfikuje uczestników"""
        facts = self.load_facts()
        
        # Analiza konwersacji
        analysis = {
            "conversations": {},
            "people": set(),
            "key_info": {}
        }
        
        for conv_id, conv_data in conversations.items():
            if isinstance(conv_data, list):
                analysis["conversations"][conv_id] = conv_data
                # Wyciągaj imiona i informacje z rozmów
                for msg in conv_data:
                    # Szukaj imion w wiadomościach
                    # To będzie wymagało szczegółowej analizy każdej rozmowy
                    pass
        
        return analysis
    
    def identify_liar(self, conversations, facts):
        """Identyfikuje kłamcę poprzez porównanie z faktami"""
        # Implementacja logiki identyfikacji kłamcy
        # Na podstawie faktów sprawdza sprzeczności w wypowiedziach
        return "Nieznany"
    
    def answer_questions(self, questions, conversations, facts):
        """Odpowiada na pytania centrali"""
        answers = {}
        
        # Przykładowe odpowiedzi - do uzupełnienia na podstawie analizy
        for q_id, question in enumerate(questions, 1):
            q_key = f"{q_id:02d}"
            answers[q_key] = "Brak odpowiedzi"  # Placeholder
        
        return answers
    
    def submit_answer(self, answers):
        """Wysyła odpowiedzi do centrali"""
        payload = {
            "task": "phone",
            "apikey": self.api_key,
            "answer": answers
        }
        
        response = requests.post(f"{self.base_url}/report", json=payload)
        print(f"Status odpowiedzi: {response.status_code}")
        print(f"Odpowiedź: {response.text}")
        return response
    
    def solve(self):
        """Główna funkcja rozwiązująca zadanie"""
        print("=== ZADANIE PHONE ===")
        
        # 1. Pobierz dane
        print("1. Pobieranie danych...")
        phone_data = self.get_phone_data()
        questions = self.get_phone_questions()
        
        if not phone_data or not questions:
            print("Błąd pobierania danych, używam backup...")
            phone_data = self.get_sorted_conversations()
        
        print(f"Pobrane dane: {len(phone_data) if phone_data else 0} elementów")
        print(f"Pytania: {len(questions) if questions else 0}")
        
        # 2. Wczytaj fakty
        print("2. Wczytywanie faktów...")
        facts = self.load_facts()
        print(f"Wczytano {len(facts)} plików z faktami")
        
        # Wyświetl pobrane dane do analizy
        if phone_data:
            print("\n=== STRUKTURA DANYCH ===")
            print(json.dumps(phone_data, indent=2, ensure_ascii=False))
        
        if questions:
            print("\n=== PYTANIA ===")
            for i, q in enumerate(questions, 1):
                print(f"{i:02d}: {q}")
        
        # 3. Analiza (do implementacji po przejrzeniu danych)
        print("\n3. Analiza rozmów...")
        # analysis = self.analyze_conversations(phone_data)
        
        # 4. Identyfikacja kłamcy
        print("4. Identyfikacja kłamcy...")
        # liar = self.identify_liar(phone_data, facts)
        
        # 5. Odpowiedzi na pytania
        print("5. Udzielanie odpowiedzi...")
        # answers = self.answer_questions(questions, phone_data, facts)
        
        # Na razie zwróć placeholder
        answers = {
            "01": "placeholder",
            "02": "placeholder", 
            "03": "placeholder",
            "04": "placeholder",
            "05": "placeholder",
            "06": "placeholder"
        }
        
        print(f"Odpowiedzi: {answers}")
        
        # 6. Wysłanie odpowiedzi (odkomentuj gdy będą gotowe)
        # return self.submit_answer(answers)

if __name__ == "__main__":
    solver = PhoneTaskSolver()
    solver.solve() 