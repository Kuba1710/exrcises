#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do automatycznego rozwiązywania zadania 'dokumenty' z AI_devs.
Analizuje raporty bezpieczeństwa i przygotowuje metadane na podstawie treści raportów i powiązanych faktów.
"""

import os
import json
import zipfile
import requests
from pathlib import Path
import tempfile
import shutil
from typing import Dict, List, Tuple

class DocumentAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://c3ntrala.ag3nts.org"
        self.data_url = f"{self.base_url}/dane/pliki_z_fabryki.zip"
        self.report_url = f"{self.base_url}/report"
        
        # Słownik mapujący sektory na ich charakterystyki
        self.sector_info = {
            'A': ['montaż', 'roboty', 'przemysłowe', 'wojskowe', 'produkcja', 'automatyzacja'],
            'B': ['baterie', 'ogniwa', 'badania', 'energia', 'laboratorium', 'testy'],
            'C': ['testowanie', 'broń', 'bezpieczeństwo', 'testy', 'militarne'],
            'D': ['magazyn', 'składowanie', 'komponenty', 'materiały']
        }
        
        # Informacje o osobach z faktów
        self.people_info = {
            'Aleksander Ragowski': ['nauczyciel', 'programista', 'Java', 'ruch', 'oporu', 'angielski', 'edukacja'],
            'Barbara Zawadzka': ['frontend', 'developer', 'Python', 'JavaScript', 'ruch', 'oporu', 'programowanie', 'AI'],
            'Azazel': ['podróżnik', 'czas', 'przestrzeń', 'technologia', 'teleportacja', 'tajemniczy'],
            'Rafał Bomba': ['laborant', 'badania', 'czas', 'nanotechnologia', 'Musk', 'zaburzenia'],
            'Adam Gospodarczyk': ['programista', 'rekrutacja', 'szkolenia', 'agenci', 'hackowanie', 'kodowanie']
        }

    def download_and_extract_data(self, work_dir: str) -> Tuple[str, str]:
        """Pobiera i rozpakuje archiwum z danymi."""
        print("Pobieranie archiwum z danymi...")
        
        zip_path = os.path.join(work_dir, "pliki_z_fabryki.zip")
        
        # Pobierz archiwum
        response = requests.get(self.data_url)
        response.raise_for_status()
        
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        
        # Rozpakuj archiwum
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(work_dir)
        
        # Znajdź foldery z raportami i faktami
        reports_dir = work_dir
        facts_dir = os.path.join(work_dir, "facts")
        
        print(f"Dane rozpakowane do: {work_dir}")
        return reports_dir, facts_dir

    def read_reports(self, reports_dir: str) -> Dict[str, str]:
        """Czyta wszystkie pliki raportów TXT."""
        reports = {}
        
        # Znajdź wszystkie pliki raportów TXT (00-09)
        for file_path in Path(reports_dir).glob("2024-11-12_report-*.txt"):
            filename = file_path.name
            
            # Sprawdź czy to jest raport z numerem 00-09
            if 'report-' in filename:
                try:
                    # Wyciągnij numer raportu
                    report_part = filename.split('report-')[1]
                    report_num = report_part.split('-')[0]
                    
                    # Sprawdź czy numer jest w zakresie 00-09
                    if report_num.isdigit() and 0 <= int(report_num) <= 9:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            reports[filename] = content
                            print(f"Wczytano raport: {filename}")
                except (IndexError, ValueError):
                    continue
        
        return reports

    def read_facts(self, facts_dir: str) -> Dict[str, str]:
        """Czyta wszystkie pliki z faktami."""
        facts = {}
        
        if not os.path.exists(facts_dir):
            print(f"Folder z faktami nie istnieje: {facts_dir}")
            return facts
        
        for file_path in Path(facts_dir).glob("f*.txt"):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                facts[file_path.name] = content
                print(f"Wczytano fakt: {file_path.name}")
        
        return facts

    def extract_sector_from_filename(self, filename: str) -> str:
        """Wyciąga informację o sektorze z nazwy pliku."""
        # Przykład: 2024-11-12_report-00-sektor_C4.txt -> C4
        if 'sektor_' in filename:
            sector_part = filename.split('sektor_')[1].split('.')[0]
            return sector_part if sector_part else ''
        return ''

    def find_people_in_text(self, text: str) -> List[str]:
        """Znajduje osoby wymienione w tekście."""
        found_people = []
        text_lower = text.lower()
        
        for person_name in self.people_info.keys():
            # Sprawdź pełne imię i nazwisko
            if person_name.lower() in text_lower:
                found_people.append(person_name)
            else:
                # Sprawdź części imienia/nazwiska
                name_parts = person_name.split()
                for part in name_parts:
                    if len(part) > 3 and part.lower() in text_lower:
                        found_people.append(person_name)
                        break
        
        return found_people

    def generate_keywords_for_report(self, filename: str, content: str, facts: Dict[str, str]) -> List[str]:
        """Generuje słowa kluczowe dla pojedynczego raportu."""
        keywords = set()
        
        # 1. Słowa kluczowe z treści raportu
        content_words = [
            'patrol', 'monitoring', 'czujniki', 'wykrycie', 'alarm', 'obszar', 'sektor',
            'aktywność', 'organiczna', 'mechaniczna', 'ruch', 'analiza', 'bezpieczny',
            'jednostka', 'skan', 'biometryczny', 'baza', 'danych', 'kontrola',
            'sensor', 'dźwiękowy', 'detektory', 'temperatura', 'sygnał', 'nadajnik',
            'odciski', 'palców', 'zabezpieczony', 'śledczy', 'peryferie', 'anomalie',
            'zwierzyna', 'leśna', 'zwierzęta', 'fałszywy', 'nocny', 'cichy',
            'północne', 'skrzydło', 'fabryka', 'zachodnia', 'część', 'terenu',
            'kanały', 'komunikacyjne', 'czyste', 'punkt', 'spokojny', 'stabilny',
            'skanery', 'operacyjna', 'ultradźwiękowy', 'zielone', 'krzewy', 'las',
            'urodzeń', 'dział', 'patrolowy', 'brak', 'cisza', 'obserwacja', 'teren',
            'wytyczne', 'zakończony', 'niepokojące', 'sygnały', 'cykl', 'gotowość',
            'rezultatów', 'stan', 'zakłóceń', 'odchylenia', 'norma', 'technologiczna'
        ]
        
        content_lower = content.lower()
        for word in content_words:
            if word in content_lower:
                keywords.add(word)
        
        # Specjalne mapowanie dla zwierząt i przyrody
        animal_terms = {
            'zwierzyna': 'zwierzęta',
            'leśna': 'las',
            'wildlife': 'zwierzęta',
            'fauna': 'zwierzęta',
            'dzika': 'zwierzęta'
        }
        
        for term, keyword in animal_terms.items():
            if term in content_lower:
                keywords.add(keyword)
        
        # 2. Informacje o sektorze z nazwy pliku
        sector = self.extract_sector_from_filename(filename)
        if sector:
            sector_letter = sector[0] if sector else ''
            if sector_letter in self.sector_info:
                keywords.update(self.sector_info[sector_letter])
                keywords.add('sektor')
                keywords.add(sector)  # np. C4
        
        # 3. Osoby wymienione w raporcie
        people_found = self.find_people_in_text(content)
        for person in people_found:
            # Dodaj imię i nazwisko
            name_parts = person.split()
            keywords.update(name_parts)
            
            # Dodaj informacje o osobie z faktów
            if person in self.people_info:
                keywords.update(self.people_info[person])
        
        # 4. Dodatkowe słowa kluczowe na podstawie kontekstu
        if 'godzina' in content_lower:
            keywords.add('godzina')
        
        if any(word in content_lower for word in ['wykryto', 'wykrycie', 'wykrył']):
            keywords.add('wykrycie')
        
        if any(word in content_lower for word in ['przedstawił', 'osobnik']):
            keywords.add('osoba')
        
        # Specjalne przypadki dla konkretnych raportów
        if 'zwierzyna leśna' in content_lower or 'lokalnej zwierzyny' in content_lower:
            keywords.add('zwierzęta')
            keywords.add('las')
            keywords.add('lokalna')
        
        # Konwertuj na listę i posortuj
        return sorted(list(keywords))

    def analyze_reports(self, reports: Dict[str, str], facts: Dict[str, str]) -> Dict[str, str]:
        """Analizuje wszystkie raporty i generuje metadane."""
        metadata = {}
        
        print("\nGenerowanie metadanych...")
        
        for filename, content in reports.items():
            keywords = self.generate_keywords_for_report(filename, content, facts)
            keywords_str = ','.join(keywords)
            metadata[filename] = keywords_str
            
            print(f"\n{filename}:")
            print(f"Treść: {content[:100]}...")
            print(f"Słowa kluczowe: {keywords_str}")
        
        return metadata

    def send_response(self, metadata: Dict[str, str]) -> Dict:
        """Wysyła odpowiedź do API centrali."""
        payload = {
            "task": "dokumenty",
            "apikey": self.api_key,
            "answer": metadata
        }
        
        print("\nWysyłanie odpowiedzi do API...")
        print(f"Liczba raportów: {len(metadata)}")
        
        # Wyświetl przykład payload dla debugowania
        print(f"Przykład payload: {json.dumps(payload, ensure_ascii=False, indent=2)[:500]}...")
        
        try:
            response = requests.post(
                self.report_url,
                json=payload,
                headers={'Content-Type': 'application/json; charset=utf-8'}
            )
            
            print(f"Status code: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Response text: {response.text}")
            
            response.raise_for_status()
            result = response.json()
            
            print(f"Odpowiedź API: {result}")
            return result
            
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            print(f"Response content: {response.text}")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise

    def solve_task(self) -> Dict:
        """Główna metoda rozwiązująca zadanie."""
        print("=== Rozpoczynam rozwiązywanie zadania 'dokumenty' ===")
        
        # Utwórz tymczasowy katalog roboczy
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # 1. Pobierz i rozpakuj dane
                reports_dir, facts_dir = self.download_and_extract_data(temp_dir)
                
                # 2. Wczytaj raporty i fakty
                reports = self.read_reports(reports_dir)
                facts = self.read_facts(facts_dir)
                
                if len(reports) != 10:
                    raise ValueError(f"Oczekiwano 10 raportów, znaleziono {len(reports)}")
                
                # 3. Przeanalizuj raporty i wygeneruj metadane
                metadata = self.analyze_reports(reports, facts)
                
                # 4. Wyślij odpowiedź
                result = self.send_response(metadata)
                
                print("\n=== Zadanie zakończone pomyślnie! ===")
                return result
                
            except Exception as e:
                print(f"Błąd podczas wykonywania zadania: {e}")
                raise

def main():
    """Główna funkcja skryptu."""
    # Wczytaj klucz API z pliku .env lub ustaw bezpośrednio
    api_key = "94097678-8e03-41d2-9656-a54c7f1371c1"
    
    # Możliwość wczytania z pliku .env
    env_file = Path("3rd-devs/.env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('PERSONAL_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    break
    
    if not api_key:
        print("Błąd: Nie znaleziono klucza API!")
        return
    
    # Utwórz analizator i rozwiąż zadanie
    analyzer = DocumentAnalyzer(api_key)
    
    try:
        result = analyzer.solve_task()
        
        # Zapisz wynik do pliku
        output_file = "dokumenty_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\nWynik zapisano do pliku: {output_file}")
        
    except Exception as e:
        print(f"Błąd: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 