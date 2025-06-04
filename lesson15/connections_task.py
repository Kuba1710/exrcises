#!/usr/bin/env python3
"""
Connections Task - Lesson 15
Zadanie: Znajdź najkrótszą ścieżkę między Rafałem a Barbarą w grafie połączeń
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv
from openai import OpenAI
from neo4j import GraphDatabase
import time

# Ładowanie zmiennych środowiskowych
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

class ConnectionsTaskSolver:
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.centrala_api_key = os.getenv('CENTRALA_API_KEY')
        self.neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
        self.neo4j_password = os.getenv('NEO4J_PASSWORD', 'neo4j')
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        if not self.centrala_api_key:
            raise ValueError("CENTRALA_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=self.openai_api_key)
        self.db_api_url = "https://c3ntrala.ag3nts.org/apidb"
        self.centrala_url = "https://c3ntrala.ag3nts.org/report"
        
        # Neo4j connection
        self.neo4j_driver = None
        
    def connect_to_neo4j(self):
        """Łączy się z bazą Neo4j"""
        try:
            self.neo4j_driver = GraphDatabase.driver(
                self.neo4j_uri, 
                auth=(self.neo4j_user, self.neo4j_password)
            )
            # Test connection
            with self.neo4j_driver.session() as session:
                session.run("RETURN 1")
            print("✅ Połączono z Neo4j")
            return True
        except Exception as e:
            print(f"❌ Błąd połączenia z Neo4j: {e}")
            print("Upewnij się, że Neo4j jest uruchomiony i dane logowania są poprawne")
            return False
    
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
    
    def fetch_users_data(self):
        """Pobiera dane użytkowników z bazy MySQL"""
        print("\n=== POBIERANIE DANYCH UŻYTKOWNIKÓW ===")
        
        query = "SELECT id, username FROM users"
        result = self.execute_db_query(query)
        
        if not result or 'reply' not in result:
            print("Błąd: Nie udało się pobrać danych użytkowników")
            return None
        
        users = []
        for row in result['reply']:
            if isinstance(row, dict):
                user_id = None
                username = None
                for key, value in row.items():
                    if 'id' in key.lower():
                        user_id = int(value)
                    elif 'username' in key.lower() or 'name' in key.lower():
                        username = str(value)
                
                if user_id is not None and username:
                    users.append({"id": user_id, "username": username})
            elif isinstance(row, list) and len(row) >= 2:
                users.append({"id": int(row[0]), "username": str(row[1])})
        
        print(f"Pobrano {len(users)} użytkowników")
        return users
    
    def fetch_connections_data(self):
        """Pobiera dane połączeń z bazy MySQL"""
        print("\n=== POBIERANIE DANYCH POŁĄCZEŃ ===")
        
        query = "SELECT user1_id, user2_id FROM connections"
        result = self.execute_db_query(query)
        
        if not result or 'reply' not in result:
            print("Błąd: Nie udało się pobrać danych połączeń")
            return None
        
        connections = []
        for row in result['reply']:
            if isinstance(row, dict):
                user1_id = None
                user2_id = None
                for key, value in row.items():
                    if 'user1' in key.lower():
                        user1_id = int(value)
                    elif 'user2' in key.lower():
                        user2_id = int(value)
                
                if user1_id is not None and user2_id is not None:
                    connections.append({"user1_id": user1_id, "user2_id": user2_id})
            elif isinstance(row, list) and len(row) >= 2:
                connections.append({"user1_id": int(row[0]), "user2_id": int(row[1])})
        
        print(f"Pobrano {len(connections)} połączeń")
        return connections
    
    def save_data_locally(self, users, connections):
        """Zapisuje dane lokalnie do plików JSON"""
        print("\n=== ZAPISYWANIE DANYCH LOKALNIE ===")
        
        try:
            # Zapisz użytkowników
            with open(os.path.join(os.path.dirname(__file__), 'users_data.json'), 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=2, ensure_ascii=False)
            
            # Zapisz połączenia
            with open(os.path.join(os.path.dirname(__file__), 'connections_data.json'), 'w', encoding='utf-8') as f:
                json.dump(connections, f, indent=2, ensure_ascii=False)
            
            print("✅ Dane zapisane lokalnie")
            return True
        except Exception as e:
            print(f"❌ Błąd podczas zapisywania danych: {e}")
            return False
    
    def load_data_locally(self):
        """Ładuje dane z lokalnych plików JSON"""
        print("\n=== ŁADOWANIE DANYCH Z PLIKÓW LOKALNYCH ===")
        
        try:
            users_file = os.path.join(os.path.dirname(__file__), 'users_data.json')
            connections_file = os.path.join(os.path.dirname(__file__), 'connections_data.json')
            
            if os.path.exists(users_file) and os.path.exists(connections_file):
                with open(users_file, 'r', encoding='utf-8') as f:
                    users = json.load(f)
                
                with open(connections_file, 'r', encoding='utf-8') as f:
                    connections = json.load(f)
                
                print(f"✅ Załadowano {len(users)} użytkowników i {len(connections)} połączeń z plików lokalnych")
                return users, connections
            else:
                print("Pliki lokalne nie istnieją")
                return None, None
        except Exception as e:
            print(f"❌ Błąd podczas ładowania danych z plików: {e}")
            return None, None
    
    def clear_neo4j_database(self):
        """Czyści bazę Neo4j"""
        print("\n=== CZYSZCZENIE BAZY NEO4J ===")
        
        try:
            with self.neo4j_driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
            print("✅ Baza Neo4j wyczyszczona")
            return True
        except Exception as e:
            print(f"❌ Błąd podczas czyszczenia bazy Neo4j: {e}")
            return False
    
    def load_users_to_neo4j(self, users):
        """Ładuje użytkowników do bazy Neo4j"""
        print("\n=== ŁADOWANIE UŻYTKOWNIKÓW DO NEO4J ===")
        
        try:
            with self.neo4j_driver.session() as session:
                for user in users:
                    session.run(
                        "CREATE (u:User {userId: $user_id, username: $username})",
                        user_id=user['id'],
                        username=user['username']
                    )
            
            print(f"✅ Załadowano {len(users)} użytkowników do Neo4j")
            return True
        except Exception as e:
            print(f"❌ Błąd podczas ładowania użytkowników do Neo4j: {e}")
            return False
    
    def load_connections_to_neo4j(self, connections):
        """Ładuje połączenia do bazy Neo4j"""
        print("\n=== ŁADOWANIE POŁĄCZEŃ DO NEO4J ===")
        
        try:
            with self.neo4j_driver.session() as session:
                for connection in connections:
                    session.run(
                        """
                        MATCH (u1:User {userId: $user1_id})
                        MATCH (u2:User {userId: $user2_id})
                        CREATE (u1)-[:KNOWS]->(u2)
                        """,
                        user1_id=connection['user1_id'],
                        user2_id=connection['user2_id']
                    )
            
            print(f"✅ Załadowano {len(connections)} połączeń do Neo4j")
            return True
        except Exception as e:
            print(f"❌ Błąd podczas ładowania połączeń do Neo4j: {e}")
            return False
    
    def find_shortest_path(self):
        """Znajduje najkrótszą ścieżkę między Rafałem a Barbarą"""
        print("\n=== SZUKANIE NAJKRÓTSZEJ ŚCIEŻKI ===")
        
        try:
            with self.neo4j_driver.session() as session:
                # Najpierw sprawdź czy użytkownicy istnieją
                rafal_result = session.run(
                    "MATCH (u:User) WHERE toLower(u.username) CONTAINS toLower('Rafał') OR toLower(u.username) CONTAINS toLower('Rafal') RETURN u.username, u.userId"
                )
                rafal_users = list(rafal_result)
                
                barbara_result = session.run(
                    "MATCH (u:User) WHERE toLower(u.username) CONTAINS toLower('Barbara') RETURN u.username, u.userId"
                )
                barbara_users = list(barbara_result)
                
                print(f"Znalezieni użytkownicy podobni do 'Rafał': {[r['u.username'] for r in rafal_users]}")
                print(f"Znalezieni użytkownicy podobni do 'Barbara': {[b['u.username'] for b in barbara_users]}")
                
                if not rafal_users or not barbara_users:
                    print("❌ Nie znaleziono użytkowników Rafał lub Barbara")
                    return None
                
                # Użyj pierwszego znalezionego użytkownika
                rafal_name = rafal_users[0]['u.username']
                barbara_name = barbara_users[0]['u.username']
                
                print(f"Szukam ścieżki między: {rafal_name} -> {barbara_name}")
                
                # Znajdź najkrótszą ścieżkę
                result = session.run(
                    """
                    MATCH (start:User {username: $rafal_name}), (end:User {username: $barbara_name})
                    MATCH path = shortestPath((start)-[:KNOWS*]-(end))
                    RETURN [node in nodes(path) | node.username] as path_names
                    """,
                    rafal_name=rafal_name,
                    barbara_name=barbara_name
                )
                
                paths = list(result)
                
                if paths:
                    path_names = paths[0]['path_names']
                    print(f"✅ Znaleziona najkrótsza ścieżka: {' -> '.join(path_names)}")
                    return path_names
                else:
                    print("❌ Nie znaleziono ścieżki między użytkownikami")
                    return None
                    
        except Exception as e:
            print(f"❌ Błąd podczas szukania ścieżki: {e}")
            return None
    
    def send_answer_to_centrala(self, path_names):
        """Wysyła odpowiedź do centrali"""
        print("\n=== WYSYŁANIE ODPOWIEDZI DO CENTRALI ===")
        
        # Przekształć listę imion w string oddzielony przecinkami
        answer = ",".join(path_names)
        
        payload = {
            "task": "connections",
            "apikey": self.centrala_api_key,
            "answer": answer
        }
        
        print(f"Wysyłam odpowiedź: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        try:
            response = requests.post(self.centrala_url, json=payload)
            response.raise_for_status()
            result = response.json()
            print(f"Odpowiedź z centrali: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
        except requests.exceptions.RequestException as e:
            print(f"Błąd podczas wysyłania odpowiedzi: {e}")
            return None
    
    def solve(self):
        """Główna metoda rozwiązująca zadanie"""
        print("=== ROZPOCZYNAM ROZWIĄZYWANIE ZADANIA CONNECTIONS ===")
        
        # 1. Połącz się z Neo4j
        if not self.connect_to_neo4j():
            return False
        
        # 2. Spróbuj załadować dane z plików lokalnych
        users, connections = self.load_data_locally()
        
        # 3. Jeśli nie ma lokalnych danych, pobierz z MySQL
        if not users or not connections:
            print("\n=== POBIERANIE DANYCH Z MYSQL ===")
            users = self.fetch_users_data()
            if not users:
                return False
            
            connections = self.fetch_connections_data()
            if not connections:
                return False
            
            # Zapisz dane lokalnie
            self.save_data_locally(users, connections)
        
        # 4. Wyczyść i załaduj dane do Neo4j
        if not self.clear_neo4j_database():
            return False
        
        if not self.load_users_to_neo4j(users):
            return False
        
        if not self.load_connections_to_neo4j(connections):
            return False
        
        # 5. Znajdź najkrótszą ścieżkę
        path_names = self.find_shortest_path()
        if not path_names:
            return False
        
        # 6. Wyślij odpowiedź do centrali
        result = self.send_answer_to_centrala(path_names)
        if result:
            print("✅ Zadanie zakończone pomyślnie!")
            return True
        else:
            print("❌ Błąd podczas wysyłania odpowiedzi")
            return False
    
    def __del__(self):
        """Zamyka połączenie z Neo4j"""
        if self.neo4j_driver:
            self.neo4j_driver.close()

def main():
    try:
        solver = ConnectionsTaskSolver()
        success = solver.solve()
        
        if success:
            print("\n🎉 Zadanie connections zostało rozwiązane pomyślnie!")
        else:
            print("\n💥 Wystąpił błąd podczas rozwiązywania zadania")
            sys.exit(1)
            
    except Exception as e:
        print(f"Błąd krytyczny: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 