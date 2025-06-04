#!/usr/bin/env python3
"""
Neo4j Setup Helper - Lesson 15
Pomocniczy skrypt do uruchomienia Neo4j w Docker
"""

import subprocess
import sys
import time
import requests

def check_docker():
    """Sprawdza czy Docker jest dostępny"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker jest dostępny")
            return True
        else:
            print("❌ Docker nie jest dostępny")
            return False
    except FileNotFoundError:
        print("❌ Docker nie jest zainstalowany")
        return False

def check_neo4j_running():
    """Sprawdza czy Neo4j już działa"""
    try:
        response = requests.get("http://localhost:7474", timeout=5)
        if response.status_code == 200:
            print("✅ Neo4j już działa na porcie 7474")
            return True
    except:
        pass
    return False

def start_neo4j_docker():
    """Uruchamia Neo4j w Docker"""
    print("🚀 Uruchamiam Neo4j w Docker...")
    
    # Sprawdź czy kontener już istnieje
    try:
        result = subprocess.run(['docker', 'ps', '-a', '--filter', 'name=neo4j-connections'], 
                              capture_output=True, text=True)
        if 'neo4j-connections' in result.stdout:
            print("📦 Kontener neo4j-connections już istnieje, uruchamiam...")
            subprocess.run(['docker', 'start', 'neo4j-connections'])
        else:
            print("📦 Tworzę nowy kontener Neo4j...")
            cmd = [
                'docker', 'run',
                '--name', 'neo4j-connections',
                '-p', '7474:7474',
                '-p', '7687:7687',
                '-d',
                '--env', 'NEO4J_AUTH=neo4j/password',
                '--env', 'NEO4J_PLUGINS=["apoc"]',
                'neo4j:latest'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Błąd podczas uruchamiania Neo4j: {result.stderr}")
                return False
    except Exception as e:
        print(f"❌ Błąd: {e}")
        return False
    
    print("⏳ Czekam na uruchomienie Neo4j...")
    for i in range(30):  # Czekaj maksymalnie 30 sekund
        try:
            response = requests.get("http://localhost:7474", timeout=2)
            if response.status_code == 200:
                print("✅ Neo4j jest gotowy!")
                return True
        except:
            pass
        time.sleep(1)
        print(f"   Próba {i+1}/30...")
    
    print("❌ Neo4j nie uruchomił się w czasie")
    return False

def stop_neo4j_docker():
    """Zatrzymuje Neo4j w Docker"""
    print("🛑 Zatrzymuję Neo4j...")
    try:
        subprocess.run(['docker', 'stop', 'neo4j-connections'])
        print("✅ Neo4j zatrzymany")
    except Exception as e:
        print(f"❌ Błąd podczas zatrzymywania: {e}")

def remove_neo4j_docker():
    """Usuwa kontener Neo4j"""
    print("🗑️ Usuwam kontener Neo4j...")
    try:
        subprocess.run(['docker', 'stop', 'neo4j-connections'])
        subprocess.run(['docker', 'rm', 'neo4j-connections'])
        print("✅ Kontener usunięty")
    except Exception as e:
        print(f"❌ Błąd podczas usuwania: {e}")

def show_neo4j_info():
    """Pokazuje informacje o Neo4j"""
    print("\n" + "="*50)
    print("📊 INFORMACJE O NEO4J")
    print("="*50)
    print("🌐 Neo4j Browser: http://localhost:7474")
    print("🔌 Bolt URI: bolt://localhost:7687")
    print("👤 Użytkownik: neo4j")
    print("🔑 Hasło: password")
    print("="*50)

def main():
    print("🔧 Neo4j Setup Helper dla Lesson 15")
    print("="*40)
    
    if len(sys.argv) < 2:
        print("Użycie:")
        print("  python setup_neo4j.py start   - Uruchom Neo4j")
        print("  python setup_neo4j.py stop    - Zatrzymaj Neo4j")
        print("  python setup_neo4j.py remove  - Usuń kontener Neo4j")
        print("  python setup_neo4j.py status  - Sprawdź status")
        return
    
    command = sys.argv[1].lower()
    
    if command == "start":
        if not check_docker():
            print("Zainstaluj Docker Desktop: https://www.docker.com/products/docker-desktop")
            return
        
        if check_neo4j_running():
            show_neo4j_info()
            return
        
        if start_neo4j_docker():
            show_neo4j_info()
            print("\n🎉 Neo4j jest gotowy do użycia!")
            print("💡 Możesz teraz uruchomić: python connections_task.py")
        else:
            print("\n💥 Nie udało się uruchomić Neo4j")
    
    elif command == "stop":
        stop_neo4j_docker()
    
    elif command == "remove":
        remove_neo4j_docker()
    
    elif command == "status":
        if check_neo4j_running():
            print("✅ Neo4j działa")
            show_neo4j_info()
        else:
            print("❌ Neo4j nie działa")
    
    else:
        print(f"❌ Nieznana komenda: {command}")

if __name__ == "__main__":
    main() 