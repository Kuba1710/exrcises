#!/usr/bin/env python3
"""
Speed Challenge Runner - Lesson 23
Uruchamia różne wersje rozwiązania wyzwania szybkości
"""

import os
import sys
import time
import asyncio
from dotenv import load_dotenv
load_dotenv('../.env')

def check_api_key():
    """Sprawdza czy klucz API jest ustawiony"""
    api_key = os.getenv('OPENAI_API_KEY', '').strip()
    if not api_key:
        print("❌ Brak klucza OpenAI API!")
        print("Ustaw zmienną środowiskową:")
        print("PowerShell: $env:OPENAI_API_KEY='sk-twoj-klucz'")
        print("Linux/Mac: export OPENAI_API_KEY='sk-twoj-klucz'")
        return False
    
    print(f"✅ Klucz API ustawiony: {api_key[:20]}...")
    return True

def run_version(version_name, module_name):
    """Uruchamia wybraną wersję skryptu"""
    print(f"\n{'='*50}")
    print(f"🚀 Uruchamiam: {version_name}")
    print(f"{'='*50}")
    
    start_time = time.time()
    
    try:
        if module_name == "speed_challenge":
            from speed_challenge import main
            result = asyncio.run(main())
        elif module_name == "ultra_speed_challenge":
            from ultra_speed_challenge import main
            result = main()
        elif module_name == "extreme_speed":
            from extreme_speed import ExtremeSpeedSolver
            solver = ExtremeSpeedSolver()
            result = asyncio.run(solver.run())
        
        total_time = time.time() - start_time
        
        print(f"\n🎯 Całkowity czas wykonania: {total_time:.2f} sekund")
        
        if total_time <= 6:
            print("✅ SUKCES! Zmieściłeś się w limicie 6 sekund!")
        else:
            print("❌ Przekroczenie limitu czasu (>6s)")
            
        return result, total_time
        
    except Exception as e:
        total_time = time.time() - start_time
        print(f"❌ Błąd: {e}")
        print(f"Czas do błędu: {total_time:.2f}s")
        return None, total_time

def main():
    """Główne menu"""
    print("🏃‍♂️ Speed Challenge - Lesson 23")
    print("=" * 40)
    
    if not check_api_key():
        sys.exit(1)
    
    print("\nDostępne wersje:")
    print("1. speed_challenge.py - Podstawowa wersja (pełne logi)")
    print("2. ultra_speed_challenge.py - Zoptymalizowana wersja")
    print("3. extreme_speed.py - Najszybsza wersja")
    print("4. Uruchom wszystkie i porównaj")
    print("0. Wyjście")
    
    choice = input("\nWybierz opcję (0-4): ").strip()
    
    if choice == "0":
        print("👋 Do widzenia!")
        sys.exit(0)
    
    elif choice == "1":
        run_version("Podstawowa wersja", "speed_challenge")
    
    elif choice == "2":
        run_version("Ultra-szybka wersja", "ultra_speed_challenge")
    
    elif choice == "3":
        run_version("Ekstremalna wersja", "extreme_speed")
    
    elif choice == "4":
        print("\n🏁 Porównanie wszystkich wersji:")
        results = []
        
        versions = [
            ("Podstawowa", "speed_challenge"),
            ("Ultra-szybka", "ultra_speed_challenge"),
            ("Ekstremalna", "extreme_speed")
        ]
        
        for name, module in versions:
            result, exec_time = run_version(name, module)
            results.append((name, exec_time, result is not None))
            
            # Krótka przerwa między testami
            time.sleep(2)
        
        print(f"\n{'='*60}")
        print("📊 PODSUMOWANIE WYNIKÓW:")
        print(f"{'='*60}")
        
        for name, exec_time, success in results:
            status = "✅ SUKCES" if success and exec_time <= 6 else "❌ FAILED"
            print(f"{name:15} | {exec_time:6.2f}s | {status}")
        
        # Znajdź najszybszą wersję
        successful = [(name, t) for name, t, success in results if success and t <= 6]
        if successful:
            fastest = min(successful, key=lambda x: x[1])
            print(f"\n🏆 Najszybsza wersja: {fastest[0]} ({fastest[1]:.2f}s)")
    
    else:
        print("❌ Nieprawidłowa opcja!")
        main()

if __name__ == "__main__":
    main() 