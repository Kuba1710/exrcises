#!/usr/bin/env python3
import subprocess
import sys
import os
from pathlib import Path

def run_command(command, shell=True):
    """Uruchamia komendę i wyświetla output"""
    print(f"Wykonuję: {command}")
    try:
        result = subprocess.run(command, shell=shell, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Błąd: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False

def check_requirements():
    """Sprawdza czy wymagane pakiety są zainstalowane"""
    print("🔍 Sprawdzam wymagania...")
    
    required_packages = ["flask", "openai", "python-dotenv", "requests"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package} - zainstalowany")
        except ImportError:
            print(f"❌ {package} - BRAK")
            missing_packages.append(package)
    
    return missing_packages

def install_requirements():
    """Instaluje wymagane pakiety"""
    missing = check_requirements()
    
    if missing:
        print(f"📦 Instaluję brakujące pakiety: {', '.join(missing)}")
        
        # Spróbuj z requirements.txt
        if Path("requirements.txt").exists():
            success = run_command("pip install -r requirements.txt")
        else:
            # Instaluj pojedynczo
            success = True
            for package in missing:
                if not run_command(f"pip install {package}"):
                    success = False
                    break
        
        if success:
            print("✅ Wszystkie pakiety zainstalowane pomyślnie")
            return True
        else:
            print("❌ Błąd podczas instalacji pakietów")
            return False
    else:
        print("✅ Wszystkie wymagane pakiety są już zainstalowane")
        return True

def check_environment():
    """Sprawdza zmienne środowiskowe"""
    print("🔍 Sprawdzam zmienne środowiskowe...")
    
    # Sprawdź różne lokalizacje plików .env
    env_locations = [
        Path(".env"),
        Path("../.env"), 
    ]
    
    found_env = False
    for env_path in env_locations:
        if env_path.exists():
            print(f"✅ Znaleziono plik .env: {env_path}")
            found_env = True
            break
    
    if not found_env:
        print("⚠️  Nie znaleziono pliku .env")
        print("Będziesz musiał podać klucze API ręcznie")
    
    # Sprawdź zmienne środowiskowe
    openai_key = os.getenv('OPENAI_API_KEY')
    personal_key = os.getenv('PERSONAL_API_KEY') or os.getenv('CENTRALA_API_KEY')
    
    if openai_key:
        print(f"✅ OPENAI_API_KEY: {openai_key[:10]}...")
    else:
        print("⚠️  OPENAI_API_KEY nie znaleziony")
    
    if personal_key:
        print(f"✅ API key dla Centrali: {personal_key[:10]}...")
    else:
        print("⚠️  Klucz API dla Centrali nie znaleziony")

def main():
    """Główna funkcja setup"""
    print("🚀 Setup dla zadania Webhook - Lesson 19")
    print("=" * 50)
    
    # Sprawdź wymagania
    ##if not install_requirements():
    ##    print("❌ Nie można kontynuować bez wymaganych pakietów")
    ##    return 1
    
    # Sprawdź środowisko
    check_environment()
    
    print("\n" + "=" * 50)
    print("📋 Instrukcje uruchomienia:")
    print()
    print("1. Uruchom serwer webhook:")
    print("   python webhook_server.py")
    print()
    print("2. W nowym terminalu przetestuj lokalnie:")
    print("   python test_webhook.py")
    print()
    print("3. Wystaw serwer na świat (ngrok):")
    print("   ngrok http 5000")
    print()
    print("4. Zgłoś URL webhook do Centrali:")
    print("   python report_webhook.py")
    print()
    print("🎯 Pamiętaj: URL webhook musi mieć endpoint /webhook")
    print("   Przykład: https://abc123.ngrok.io/webhook")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 