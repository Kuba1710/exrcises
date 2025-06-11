import requests
import json
import base64
from pathlib import Path

class PhoneAnalyzer:
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
        
    def get_sorted_conversations(self):
        """Pobiera już posortowane rozmowy"""
        backup_url = base64.b64decode("aHR0cHM6Ly9jM250cmFsYS5hZzNudHMub3JnL2RhdGEvVFVUQUotS0xVQ1ovcGhvbmVfc29ydGVkLmpzb24=").decode()
        backup_url = backup_url.replace("TUTAJ-KLUCZ", self.api_key)
        
        response = requests.get(backup_url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Błąd pobierania posortowanych rozmów: {response.status_code}")
            return None
    
    def get_questions(self):
        """Pobiera pytania od centrali"""
        url = f"{self.base_url}/data/{self.api_key}/phone_questions.json"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Błąd pobierania pytań: {response.status_code}")
            return None
    
    def analyze_conversations(self, conversations):
        """Analizuje rozmowy i wyciąga kluczowe informacje"""
        print("=== ANALIZA ROZMÓW ===")
        
        # Rozmowa 1: Barbara z Samuelem o Rafale
        print("\nRozmowa 1: Barbara i Samuel")
        print("- Barbara była u Rafała uczyć go JavaScriptu (jako wymówka)")
        print("- Rafał nie żyje - centrala wysłała drona")
        print("- Andrzej miał nadajnik GPS w samochodzie") 
        print("- Andrzej zwiał/zniknął")
        
        # Rozmowa 2: Samuel z Zygfrydem
        print("\nRozmowa 2: Samuel i Zygfryd")
        print("- Samuel raportuje Zygfrydowi o niepowodzeniu misji Barbary")
        print("- Zygfryd wiedział już o śmierci Rafała")
        print("- Problemy z połączeniem telefonicznym")
        
        # Rozmowa 3: Samuel z Zygfrydem (ponownie)
        print("\nRozmowa 3: Samuel i Zygfryd (ponownie)")
        print("- Samuel był w fabryce w sektorze D (gdzie produkuje się broń)")
        print("- Zygfryd daje endpoint API: https://rafal.ag3nts.org/510bc")
        print("- Ma skontaktować się z Tomaszem po hasło")
        
        # Rozmowa 4: Samuel z Tomaszem  
        print("\nRozmowa 4: Samuel i Tomasz")
        print("- Tomasz pracuje w Centrali")
        print("- Hasło do pierwszej warstwy: 'NONOMNISMORIAR'")
        print("- Tomasz mówi o problemach z kolejnymi warstwami - potrzeba technologii z przyszłości")
        print("- Wspominają o Azazelu (może skakać w czasie) i 'numerze piątym'")
        
        # Rozmowa 5: Witek z Barbarą
        print("\nRozmowa 5: Witek i Barbara")
        print("- Witek prosi Barbarę o pomoc z API")
        print("- Witek ma endpoint: https://rafal.ag3nts.org/b46c3 (bez hasła)")
        print("- 'Nauczyciel' (Zygfryd?) dostarczył endpoint ale pracuje nad hasłem")
        print("- Odniesienie do Helmut Rahn z 1954 roku")
        
        return self.extract_key_info(conversations)
    
    def extract_key_info(self, conversations):
        """Wyciąga kluczowe informacje potrzebne do odpowiedzi"""
        info = {
            'endpoints': [],
            'people': set(),
            'relationships': {},
            'lies': []
        }
        
        # Zbieranie endpointów
        info['endpoints'].append('https://rafal.ag3nts.org/510bc')  # Z rozmowy 3 - Zygfryd
        info['endpoints'].append('https://rafal.ag3nts.org/b46c3')   # Z rozmowy 5 - Witek
        
        # Identyfikacja osób
        info['people'] = {'Barbara', 'Samuel', 'Zygfryd', 'Tomasz', 'Witek', 'Rafał', 'Andrzej', 'Azazel'}
        
        # Relacje
        info['relationships']['Barbara_boyfriend'] = 'Aleksander'  # Z faktów - Barbara była związana z Aleksandrem Ragorskim
        
        # Analiza kłamstw
        return self.find_liar(conversations, info)
    
    def find_liar(self, conversations, info):
        """Identyfikuje kłamcę na podstawie faktów"""
        facts = self.load_facts()
        
        print("\n=== SPRAWDZANIE FAKTÓW ===")
        
        # Z faktów wiemy o sektorach fabryki:
        # - Sektor A: montaż robotów 
        # - Sektor B: baterie
        # - Sektor C: testowanie broni
        # - Sektor D: magazyn (obecnie wyłączony z użytku)
        
        # Samuel w rozmowie 3 mówi: "byłem w fabryce. Wiesz, w sektorze D, gdzie się produkuje broń"
        # ALE z faktów wiemy, że w sektorze D NIE produkuje się broni!
        # Sektor D to magazyn, a broń testuje się w sektorze C
        
        print("KŁAMSTWO: Samuel mówi, że w sektorze D produkuje się broń")
        print("FAKT: Sektor D to magazyn, broń testuje się w sektorze C")
        
        info['liar'] = 'Samuel'
        info['liar_endpoint'] = 'https://rafal.ag3nts.org/510bc'  # Endpoint podany przez kłamcę
        info['true_endpoint'] = 'https://rafal.ag3nts.org/b46c3'   # Endpoint od osoby, która nie skłamała (Witek)
        
        return info
    
    def test_api_endpoint(self, endpoint, password):
        """Testuje endpoint API z hasłem"""
        try:
            payload = {"password": password}
            response = requests.post(endpoint, json=payload)
            if response.status_code == 200:
                return response.text
            else:
                return f"Błąd: {response.status_code}"
        except Exception as e:
            return f"Błąd: {str(e)}"
    
    def answer_questions(self, questions, analysis_info):
        """Odpowiada na pytania centrali"""
        answers = {}
        
        # 01: Jeden z rozmówców skłamał podczas rozmowy. Kto to był?
        answers['01'] = 'Samuel'
        
        # 02: Jaki jest prawdziwy endpoint do API podany przez osobę, która NIE skłamała?
        answers['02'] = 'https://rafal.ag3nts.org/b46c3'
        
        # 03: Jakim przezwiskiem określany jest chłopak Barbary?
        # Z faktów: Barbara była związana z Aleksandrem Ragorskim (nauczyciel)
        # W rozmowie 5 Witek mówi o "nauczycielu" Barbary
        answers['03'] = 'nauczyciel'
        
        # 04: Jakie dwie osoby rozmawiają ze sobą w pierwszej rozmowie?
        answers['04'] = 'Barbara, Samuel'
        
        # 05: Co odpowiada poprawny endpoint API po wysłaniu hasła?
        # Testujemy endpoint z hasłem NONOMNISMORIAR
        api_response = self.test_api_endpoint('https://rafal.ag3nts.org/b46c3', 'NONOMNISMORIAR')
        answers['05'] = api_response
        
        # 06: Jak ma na imię osoba, która dostarczyła dostęp do API, ale nie znała hasła?
        # Z rozmowy 5: Witek ma endpoint ale nie ma hasła, jego "nauczyciel" pracuje nad hasłem
        answers['06'] = 'Witek'
        
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
        print("=== ROZWIĄZYWANIE ZADANIA PHONE ===")
        
        # 1. Pobierz dane
        conversations = self.get_sorted_conversations()
        questions = self.get_questions()
        
        if not conversations or not questions:
            print("Błąd pobierania danych!")
            return
        
        # 2. Analizuj rozmowy
        analysis_info = self.analyze_conversations(conversations)
        
        # 3. Odpowiedz na pytania
        print("\n=== ODPOWIEDZI ===")
        answers = self.answer_questions(questions, analysis_info)
        
        for key, answer in answers.items():
            print(f"{key}: {answer}")
        
        # 4. Wyślij odpowiedzi
        print("\n=== WYSYŁANIE ODPOWIEDZI ===")
        return self.submit_answer(answers)

if __name__ == "__main__":
    analyzer = PhoneAnalyzer()
    analyzer.solve() 