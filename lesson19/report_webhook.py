import requests
import os
from dotenv import load_dotenv
from tunnel_manager import TunnelManager

# Ładowanie zmiennych środowiskowych z różnych lokalizacji
load_dotenv()  # Current directory
load_dotenv("../.env")  # Parent directory  
load_dotenv("../../3rd-devs/.env")  # 3rd-devs directory

def report_webhook_url(webhook_url):
    """
    Zgłasza URL webhook do Centrali
    """
    
    api_key = os.getenv('PERSONAL_API_KEY')
    if not api_key:
        # Spróbuj z innego klucza
        api_key = os.getenv('CENTRALA_API_KEY')
    if not api_key:
        # Hardcoded fallback (z lesson11)
        api_key = "94097678-8e03-41d2-9656-a54c7f1371c1"
    
    if not api_key:
        print("Error: API key not found in environment variables")
        print("Looking for PERSONAL_API_KEY or CENTRALA_API_KEY")
        api_key = input("Podaj klucz API dla Centrali: ")
    
    centrala_url = "https://c3ntrala.ag3nts.org/report"
    
    payload = {
        "task": "webhook",
        "apikey": api_key,
        "answer": webhook_url
    }
    
    print(f"Sending webhook URL to Centrala: {webhook_url}")
    print(f"Using API key: {api_key[:10]}...")
    
    try:
        response = requests.post(centrala_url, json=payload)
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook URL successfully reported to Centrala!")
            try:
                result = response.json()
                if 'flag' in result:
                    print(f"🎉 FLAG: {result['flag']}")
                elif 'message' in result:
                    print(f"Message: {result['message']}")
                else:
                    print("Response JSON:", result)
            except:
                print("Response text:", response.text)
        else:
            print("❌ Failed to report webhook URL")
            
    except Exception as e:
        print(f"Error reporting webhook: {e}")

def main():
    """Główna funkcja z automatycznym tunnel managerem"""
    print("🚀 Webhook Reporter with Tunnel Manager")
    print("=" * 50)
    
    # Sprawdź czy użytkownik chce podać URL ręcznie
    manual_url = input("Podaj URL webhook ręcznie (Enter = automatyczny tunnel): ").strip()
    
    if manual_url:
        if not manual_url.startswith('https://'):
            print("❌ URL musi zaczynać się od https://")
            return 1
        if not manual_url.endswith('/webhook'):
            print("⚠️  Dodaję /webhook do URL")
            manual_url = manual_url.rstrip('/') + '/webhook'
        
        report_webhook_url(manual_url)
        return 0
    
    # Automatyczny tunnel
    print("🌐 Uruchamiam automatyczny tunnel...")
    
    # Sprawdź czy serwer działa
    try:
        requests.get('http://localhost:5000/test', timeout=2)
        print("✅ Serwer webhook działa na porcie 5000")
    except:
        print("❌ Serwer webhook nie działa na porcie 5000")
        print("Uruchom najpierw: python webhook_server.py lub python simple_server.py")
        return 1
    
    # Uruchom tunnel
    tunnel = TunnelManager(port=5000)
    
    if tunnel.start_tunnel():
        webhook_url = tunnel.get_webhook_url()
        print(f"\n🎯 Automatyczny URL webhook: {webhook_url}")
        
        # Przetestuj tunnel
        try:
            test_response = requests.get(f"{tunnel.tunnel_url}/test", timeout=10)
            if test_response.status_code == 200:
                print("✅ Tunnel działa poprawnie")
            else:
                print(f"⚠️  Tunnel zwraca status {test_response.status_code}")
        except Exception as e:
            print(f"⚠️  Nie udało się przetestować tunnel: {e}")
        
        # Zgłoś do Centrali
        report_webhook_url(webhook_url)
        
        print(f"\n⌨️  Naciśnij Enter aby zatrzymać tunnel...")
        input()
        tunnel.stop_tunnel()
    else:
        print("❌ Nie udało się uruchomić tunnela")
        print("Podaj URL ręcznie:")
        manual_url = input("HTTPS URL webhook: ").strip()
        if manual_url:
            report_webhook_url(manual_url)
        return 1
    
    return 0

if __name__ == "__main__":
    main() 