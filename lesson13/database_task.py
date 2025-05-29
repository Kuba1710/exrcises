#!/usr/bin/env python3
"""
Database Task - Lesson 13
Zadanie: Znajdź DC_ID aktywnych datacenter, których menadżerowie są nieaktywni
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv
from openai import OpenAI

# Ładowanie zmiennych środowiskowych
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

class DatabaseTaskSolver:
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.centrala_api_key = os.getenv('CENTRALA_API_KEY')
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        if not self.centrala_api_key:
            raise ValueError("CENTRALA_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=self.openai_api_key)
        self.db_api_url = "https://c3ntrala.ag3nts.org/apidb"
        self.centrala_url = "https://c3ntrala.ag3nts.org/report"
        
    def execute_db_query(self, query):
        """Wykonuje zapytanie SQL przez API bazy danych"""
        payload = {
            "task": "database",
            "apikey": self.centrala_api_key,
            "query": query
        }
        
        print(f"Wykonuję zapytanie: {query}")
        
        try:
            response = requests.post(self.db_api_url, json=payload)
            response.raise_for_status()
            result = response.json()
            print(f"Odpowiedź z bazy: {json.dumps(result, indent=2)}")
            return result
        except requests.exceptions.RequestException as e:
            print(f"Błąd podczas wykonywania zapytania: {e}")
            return None
    
    def discover_database_structure(self):
        """Odkrywa strukturę bazy danych"""
        print("=== ODKRYWANIE STRUKTURY BAZY DANYCH ===")
        
        # 1. Pobierz listę tabel
        print("\n1. Pobieranie listy tabel...")
        tables_result = self.execute_db_query("SHOW TABLES")
        
        if not tables_result or 'reply' not in tables_result:
            print("Błąd: Nie udało się pobrać listy tabel")
            return None
        
        tables = []
        for row in tables_result['reply']:
            if isinstance(row, dict):
                # Znajdź pierwszą wartość w słowniku (nazwa tabeli)
                table_name = list(row.values())[0]
                tables.append(table_name)
            elif isinstance(row, list):
                tables.append(row[0])
            else:
                tables.append(str(row))
        
        print(f"Znalezione tabele: {tables}")
        
        # 2. Pobierz strukturę każdej tabeli
        table_schemas = {}
        for table in tables:
            print(f"\n2. Pobieranie struktury tabeli: {table}")
            schema_result = self.execute_db_query(f"SHOW CREATE TABLE {table}")
            
            if schema_result and 'reply' in schema_result:
                table_schemas[table] = schema_result['reply']
            else:
                print(f"Błąd: Nie udało się pobrać struktury tabeli {table}")
        
        return table_schemas
    
    def generate_sql_query(self, table_schemas):
        """Używa LLM do wygenerowania zapytania SQL"""
        print("\n=== GENEROWANIE ZAPYTANIA SQL ===")
        
        # Przygotuj prompt dla LLM
        schemas_text = ""
        for table_name, schema in table_schemas.items():
            schemas_text += f"\nTabela: {table_name}\n"
            schemas_text += f"Struktura: {json.dumps(schema, indent=2)}\n"
        
        prompt = f"""
Masz dostęp do następujących tabel w bazie danych:

{schemas_text}

Zadanie: Napisz zapytanie SQL, które zwróci DC_ID aktywnych datacenter, których menadżerowie (z tabeli users) są nieaktywni.

Wskazówki:
- Datacenter jest aktywny, jeśli ma odpowiedni status (prawdopodobnie is_active = 1 lub podobne pole)
- Menadżer jest nieaktywny, jeśli ma odpowiedni status w tabeli users (prawdopodobnie is_active = 0 lub podobne pole)
- Musisz połączyć tabele przez odpowiednie klucze obce (prawdopodobnie manager_id w tabeli datacenter odpowiada id w tabeli users)

BARDZO WAŻNE: Zwróć TYLKO surowy tekst zapytania SQL, bez żadnych dodatkowych opisów, wyjaśnień czy formatowania Markdown. Nie dodawaj żadnych komentarzy ani dodatkowego tekstu.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Jesteś ekspertem SQL. Zwracasz tylko surowe zapytania SQL bez dodatkowych komentarzy."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            
            sql_query = response.choices[0].message.content.strip()
            
            # Usuń ewentualne formatowanie markdown
            if sql_query.startswith("```sql"):
                sql_query = sql_query[6:]
            if sql_query.startswith("```"):
                sql_query = sql_query[3:]
            if sql_query.endswith("```"):
                sql_query = sql_query[:-3]
            
            sql_query = sql_query.strip()
            
            print(f"Wygenerowane zapytanie SQL: {sql_query}")
            return sql_query
            
        except Exception as e:
            print(f"Błąd podczas generowania zapytania SQL: {e}")
            return None
    
    def extract_dc_ids(self, query_result):
        """Wyodrębnia listę DC_ID z wyniku zapytania"""
        if not query_result or 'reply' not in query_result:
            print("Błąd: Brak danych w wyniku zapytania")
            return []
        
        dc_ids = []
        for row in query_result['reply']:
            if isinstance(row, dict):
                # Znajdź pole z DC_ID (może być różnie nazwane)
                for key, value in row.items():
                    if 'dc_id' in key.lower() or 'id' in key.lower():
                        dc_ids.append(int(value))
                        break
            elif isinstance(row, list) and len(row) > 0:
                dc_ids.append(int(row[0]))
            else:
                try:
                    dc_ids.append(int(row))
                except (ValueError, TypeError):
                    continue
        
        print(f"Znalezione DC_ID: {dc_ids}")
        return dc_ids
    
    def send_answer_to_centrala(self, dc_ids):
        """Wysyła odpowiedź do centrali"""
        print("\n=== WYSYŁANIE ODPOWIEDZI DO CENTRALI ===")
        
        payload = {
            "task": "database",
            "apikey": self.centrala_api_key,
            "answer": dc_ids
        }
        
        print(f"Wysyłam odpowiedź: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(self.centrala_url, json=payload)
            response.raise_for_status()
            result = response.json()
            print(f"Odpowiedź z centrali: {json.dumps(result, indent=2)}")
            return result
        except requests.exceptions.RequestException as e:
            print(f"Błąd podczas wysyłania odpowiedzi: {e}")
            return None
    
    def solve(self):
        """Główna metoda rozwiązująca zadanie"""
        print("=== ROZPOCZYNAM ROZWIĄZYWANIE ZADANIA DATABASE ===")
        
        # 1. Odkryj strukturę bazy danych
        table_schemas = self.discover_database_structure()
        if not table_schemas:
            print("Błąd: Nie udało się odkryć struktury bazy danych")
            return False
        
        # 2. Wygeneruj zapytanie SQL
        sql_query = self.generate_sql_query(table_schemas)
        if not sql_query:
            print("Błąd: Nie udało się wygenerować zapytania SQL")
            return False
        
        # 3. Wykonaj zapytanie SQL
        print(f"\n=== WYKONYWANIE ZAPYTANIA SQL ===")
        query_result = self.execute_db_query(sql_query)
        if not query_result:
            print("Błąd: Nie udało się wykonać zapytania SQL")
            return False
        
        # 4. Wyodrębnij DC_ID
        dc_ids = self.extract_dc_ids(query_result)
        if not dc_ids:
            print("Błąd: Nie znaleziono żadnych DC_ID")
            return False
        
        # 5. Wyślij odpowiedź do centrali
        result = self.send_answer_to_centrala(dc_ids)
        if result:
            print("✅ Zadanie zakończone pomyślnie!")
            return True
        else:
            print("❌ Błąd podczas wysyłania odpowiedzi")
            return False

def main():
    try:
        solver = DatabaseTaskSolver()
        success = solver.solve()
        
        if success:
            print("\n🎉 Zadanie database zostało rozwiązane pomyślnie!")
        else:
            print("\n💥 Wystąpił błąd podczas rozwiązywania zadania")
            sys.exit(1)
            
    except Exception as e:
        print(f"Błąd krytyczny: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 