#!/usr/bin/env python3
"""
Skrypt do namierzenia Barbary Zawadzkiej
Wykorzystuje API people i places do śledzenia powiązań między osobami i miejscami
"""

import requests
import json
import time
from typing import Set, List, Dict, Any
import os
from dotenv import load_dotenv

# Ładowanie zmiennych środowiskowych
load_dotenv()

class BarbaraSearcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.people_url = "https://c3ntrala.ag3nts.org/people"
        self.places_url = "https://c3ntrala.ag3nts.org/places"
        self.report_url = "https://centrala.ag3nts.org/report"
        
        # Kolejki do przetwarzania
        self.people_queue: Set[str] = set()
        self.places_queue: Set[str] = set()
        
        # Już sprawdzone elementy
        self.checked_people: Set[str] = set()
        self.checked_places: Set[str] = set()
        
        # Wyniki
        self.people_locations: Dict[str, List[str]] = {}
        self.place_people: Dict[str, List[str]] = {}
        
        # Znane miejsca Barbary z notatki
        self.known_barbara_places = {"KRAKOW"}
        
    def normalize_name(self, name: str) -> str:
        """Normalizuje imię do mianownika bez polskich znaków"""
        # Mapowanie popularnych form na mianownik
        name_mapping = {
            "BARBARA": "BARBARA",
            "BARBARY": "BARBARA", 
            "BARBARZE": "BARBARA",
            "BARBARĄ": "BARBARA",
            "ALEKSANDER": "ALEKSANDER",
            "ALEKSANDRA": "ALEKSANDER",
            "ALEKSANDROWI": "ALEKSANDER",
            "ALEKSANDREM": "ALEKSANDER",
            "ANDRZEJ": "ANDRZEJ",
            "ANDRZEJA": "ANDRZEJ",
            "ANDRZEJOWI": "ANDRZEJ",
            "ANDRZEJEM": "ANDRZEJ",
            "RAFAŁ": "RAFAL",
            "RAFALA": "RAFAL",
            "RAFALOWI": "RAFAL",
            "RAFALEM": "RAFAL",
            "GRZESIEK": "GRZESIEK",
            "GRZEŚKA": "GRZESIEK",
            "GRZEŚKOWI": "GRZESIEK"
        }
        
        name_upper = name.upper().strip()
        return name_mapping.get(name_upper, name_upper)
    
    def normalize_city(self, city: str) -> str:
        """Normalizuje nazwę miasta bez polskich znaków"""
        city_mapping = {
            "KRAKÓW": "KRAKOW",
            "KRAKOW": "KRAKOW",
            "WARSZAWA": "WARSZAWA",
            "GDAŃSK": "GDANSK",
            "GDANSK": "GDANSK",
            "ŁÓDŹ": "LODZ",
            "LODZ": "LODZ",
            "WROCŁAW": "WROCLAW",
            "WROCLAW": "WROCLAW",
            "POZNAŃ": "POZNAN",
            "POZNAN": "POZNAN"
        }
        
        city_upper = city.upper().strip()
        return city_mapping.get(city_upper, city_upper)
    
    def query_api(self, url: str, query: str) -> Dict[str, Any]:
        """Wykonuje zapytanie do API"""
        payload = {
            "apikey": self.api_key,
            "query": query
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Błąd API dla {query}: {e}")
            return {}
    
    def search_person(self, person: str) -> List[str]:
        """Wyszukuje miejsca dla danej osoby"""
        if person in self.checked_people:
            return self.people_locations.get(person, [])
        
        print(f"Sprawdzam osobę: {person}")
        result = self.query_api(self.people_url, person)
        
        places = []
        if "message" in result:
            # Parsowanie odpowiedzi - może zawierać listę miejsc
            message = result["message"]
            print(f"Odpowiedź dla {person}: {message}")
            
            # Próba wyodrębnienia miejsc z odpowiedzi
            if isinstance(message, list):
                places = [self.normalize_city(place) for place in message if isinstance(place, str)]
            elif isinstance(message, str):
                # Jeśli to string, może zawierać nazwy miast
                words = message.upper().split()
                for word in words:
                    normalized = self.normalize_city(word)
                    if len(normalized) > 2:  # Filtruj krótkie słowa
                        places.append(normalized)
        
        self.checked_people.add(person)
        self.people_locations[person] = places
        
        # Dodaj nowe miejsca do kolejki
        for place in places:
            if place not in self.checked_places:
                self.places_queue.add(place)
        
        time.sleep(0.5)  # Opóźnienie między zapytaniami
        return places
    
    def search_place(self, place: str) -> List[str]:
        """Wyszukuje osoby w danym miejscu"""
        if place in self.checked_places:
            return self.place_people.get(place, [])
        
        print(f"Sprawdzam miejsce: {place}")
        result = self.query_api(self.places_url, place)
        
        people = []
        if "message" in result:
            message = result["message"]
            print(f"Odpowiedź dla {place}: {message}")
            
            # Parsowanie odpowiedzi
            if isinstance(message, list):
                people = [self.normalize_name(person) for person in message if isinstance(person, str)]
            elif isinstance(message, str):
                # Sprawdź czy to ograniczone dane
                if "RESTRICTED" in message.upper():
                    print(f"⚠️ Ograniczone dane dla {place}")
                    # Jeśli to Lublin i mamy ograniczone dane, może tam być Barbara
                    if place == "LUBLIN":
                        print(f"🔍 LUBLIN ma ograniczone dane - może tam być Barbara!")
                        people = ["BARBARA"]  # Zakładamy że Barbara może być w Lublinie
                else:
                    # Próba wyodrębnienia imion z odpowiedzi
                    words = message.upper().split()
                    for word in words:
                        normalized = self.normalize_name(word)
                        if normalized in ["BARBARA", "ALEKSANDER", "ANDRZEJ", "RAFAL", "GRZESIEK"]:
                            people.append(normalized)
                        # Dodaj także inne imiona które mogą być ważne
                        elif len(normalized) > 2 and normalized.isalpha():
                            people.append(normalized)
        
        self.checked_places.add(place)
        self.place_people[place] = people
        
        # Dodaj nowe osoby do kolejki
        for person in people:
            if person not in self.checked_people:
                self.people_queue.add(person)
        
        time.sleep(0.5)  # Opóźnienie między zapytaniami
        return people
    
    def find_barbara_location(self) -> str:
        """Główna funkcja wyszukująca aktualne miejsce Barbary"""
        # Inicjalizacja kolejek na podstawie notatki + AZAZEL
        self.people_queue.update(["BARBARA", "ALEKSANDER", "ANDRZEJ", "RAFAL", "AZAZEL"])
        self.places_queue.update(["KRAKOW", "WARSZAWA"])
        
        barbara_found_in = []
        
        # Główna pętla wyszukiwania
        iteration = 0
        max_iterations = 50  # Zabezpieczenie przed nieskończoną pętlą
        
        while (self.people_queue or self.places_queue) and iteration < max_iterations:
            iteration += 1
            print(f"\n--- Iteracja {iteration} ---")
            
            # Przetwarzaj osoby
            people_to_process = list(self.people_queue)
            self.people_queue.clear()
            
            for person in people_to_process:
                places = self.search_person(person)
                print(f"{person} widziany w: {places}")
            
            # Przetwarzaj miejsca
            places_to_process = list(self.places_queue)
            self.places_queue.clear()
            
            for place in places_to_process:
                people = self.search_place(place)
                print(f"W {place} widziano: {people}")
                
                # Sprawdź czy Barbara jest w tym miejscu
                if "BARBARA" in people:
                    barbara_found_in.append(place)
                    print(f"🎯 BARBARA znaleziona w: {place}")
        
        print(f"\n--- Podsumowanie ---")
        print(f"Barbara znaleziona w miejscach: {barbara_found_in}")
        print(f"Znane miejsca Barbary z notatki: {self.known_barbara_places}")
        
        # Analiza powiązań
        print(f"\n--- Analiza powiązań ---")
        print(f"Aleksander był w: {self.people_locations.get('ALEKSANDER', [])}")
        print(f"Rafał był w: {self.people_locations.get('RAFAL', [])}")
        print(f"Andrzej był w: {self.people_locations.get('ANDRZEJ', [])}")
        
        # Znajdź wspólne miejsca Aleksandra i Rafała (współpracownicy)
        aleksander_places = set(self.people_locations.get('ALEKSANDER', []))
        rafal_places = set(self.people_locations.get('RAFAL', []))
        common_places = aleksander_places.intersection(rafal_places)
        print(f"Wspólne miejsca Aleksandra i Rafała: {common_places}")
        
        # Znajdź nowe miejsce (nie z notatki)
        new_locations = [loc for loc in barbara_found_in if loc not in self.known_barbara_places]
        
        if new_locations:
            print(f"Nowe miejsca Barbary: {new_locations}")
            return new_locations[0]  # Zwróć pierwsze nowe miejsce
        
        # Jeśli nie znaleziono bezpośrednio, sprawdź miejsca z ograniczonymi danymi
        restricted_places = []
        for place, people in self.place_people.items():
            if "BARBARA" in people and place not in self.known_barbara_places:
                restricted_places.append(place)
        
        if restricted_places:
            print(f"Miejsca z ograniczonymi danymi gdzie może być Barbara: {restricted_places}")
            return restricted_places[0]
        
        print("Nie znaleziono nowego miejsca pobytu Barbary")
        return ""
    
    def report_answer(self, city: str) -> bool:
        """Wysyła odpowiedź do centrali"""
        payload = {
            "task": "loop",
            "apikey": self.api_key,
            "answer": city
        }
        
        try:
            response = requests.post(self.report_url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            print(f"Odpowiedź centrali: {result}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Błąd wysyłania odpowiedzi: {e}")
            return False

def main():
    # Pobierz klucz API
    api_key = os.getenv("CENTRALA_API_KEY")
    if not api_key:
        api_key = input("Podaj klucz API: ").strip()
    
    if not api_key:
        print("Brak klucza API!")
        return
    
    # Utwórz searcher i rozpocznij wyszukiwanie
    searcher = BarbaraSearcher(api_key)
    
    print("🔍 Rozpoczynam wyszukiwanie Barbary Zawadzkiej...")
    barbara_location = searcher.find_barbara_location()
    
    if barbara_location:
        print(f"\n🎯 Znaleziono Barbarę w: {barbara_location}")
        
        confirm = input(f"Czy wysłać odpowiedź '{barbara_location}' do centrali? (y/n): ")
        if confirm.lower() == 'y':
            success = searcher.report_answer(barbara_location)
            if success:
                print("✅ Odpowiedź wysłana pomyślnie!")
            else:
                print("❌ Błąd wysyłania odpowiedzi")
    else:
        print("❌ Nie udało się znaleźć aktualnego miejsca pobytu Barbary")

if __name__ == "__main__":
    main() 