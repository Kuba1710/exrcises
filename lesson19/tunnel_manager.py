#!/usr/bin/env python3
import subprocess
import sys
import time
import requests
import json
import os
from pathlib import Path

class TunnelManager:
    def __init__(self, port=5000):
        self.port = port
        self.tunnel_url = None
        self.tunnel_process = None
    
    def check_ngrok(self):
        """Sprawdza czy ngrok jest zainstalowany"""
        try:
            result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def install_ngrok_windows(self):
        """Instaluje ngrok na Windows"""
        print("📦 Instaluję ngrok...")
        
        # Sprawdź czy jest chocolatey
        try:
            subprocess.run(['choco', '--version'], capture_output=True, check=True)
            print("Używam chocolatey do instalacji ngrok...")
            result = subprocess.run(['choco', 'install', 'ngrok', '-y'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ ngrok zainstalowany przez chocolatey")
                return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass
        
        # Ręczna instalacja
        print("Chocolatey nie dostępne. Sprawdź instrukcje instalacji ngrok:")
        print("1. Idź na https://ngrok.com/download")
        print("2. Pobierz ngrok dla Windows")
        print("3. Rozpakuj do folderu w PATH")
        print("4. Uruchom ponownie ten skrypt")
        return False
    
    def start_ngrok(self):
        """Uruchamia ngrok tunnel"""
        if not self.check_ngrok():
            if sys.platform == 'win32':
                if not self.install_ngrok_windows():
                    return False
            else:
                print("❌ ngrok nie jest zainstalowany")
                return False
        
        print(f"🚀 Uruchamiam ngrok na porcie {self.port}...")
        
        try:
            # Uruchom ngrok w tle
            self.tunnel_process = subprocess.Popen(
                ['ngrok', 'http', str(self.port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Czekaj na uruchomienie
            time.sleep(3)
            
            # Pobierz URL z ngrok API
            tunnel_url = self.get_ngrok_url()
            if tunnel_url:
                self.tunnel_url = tunnel_url
                print(f"✅ Ngrok uruchomiony: {tunnel_url}")
                return True
            else:
                print("❌ Nie udało się pobrać URL ngrok")
                return False
                
        except Exception as e:
            print(f"❌ Błąd uruchamiania ngrok: {e}")
            return False
    
    def get_ngrok_url(self):
        """Pobiera URL tunelu z ngrok API"""
        try:
            response = requests.get('http://127.0.0.1:4040/api/tunnels')
            data = response.json()
            
            for tunnel in data['tunnels']:
                if tunnel['config']['addr'] == f'http://localhost:{self.port}':
                    return tunnel['public_url'].replace('http://', 'https://')
            return None
        except:
            return None
    
    def start_localtunnel(self):
        """Alternatywa - localtunnel przez npx"""
        print(f"🔄 Próbuję localtunnel jako alternatywę...")
        
        try:
            # Sprawdź czy jest npx/npm
            subprocess.run(['npx', '--version'], capture_output=True, check=True)
            
            print(f"🚀 Uruchamiam localtunnel na porcie {self.port}...")
            
            # Uruchom localtunnel
            self.tunnel_process = subprocess.Popen(
                ['npx', 'localtunnel', '--port', str(self.port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Czekaj na URL
            time.sleep(5)
            
            # Sprawdź output
            output = self.tunnel_process.stdout.readline()
            if 'https://' in output:
                self.tunnel_url = output.strip().split()[-1]
                print(f"✅ Localtunnel uruchomiony: {self.tunnel_url}")
                return True
            
            return False
            
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("❌ npm/npx nie dostępne")
            return False
    
    def start_cloudflared(self):
        """Alternatywa - cloudflared tunnel"""
        print(f"🔄 Próbuję cloudflared jako alternatywę...")
        
        try:
            # Sprawdź czy jest cloudflared
            subprocess.run(['cloudflared', '--version'], capture_output=True, check=True)
            
            print(f"🚀 Uruchamiam cloudflared na porcie {self.port}...")
            
            # Uruchom cloudflared
            self.tunnel_process = subprocess.Popen(
                ['cloudflared', 'tunnel', '--url', f'http://localhost:{self.port}'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Szukaj URL w output
            time.sleep(5)
            
            # Cloudflared wypisuje URL w stderr
            for _ in range(10):
                line = self.tunnel_process.stderr.readline()
                if 'https://' in line and 'trycloudflare.com' in line:
                    # Wyciągnij URL
                    self.tunnel_url = line.split('https://')[1].split()[0]
                    self.tunnel_url = f"https://{self.tunnel_url}"
                    print(f"✅ Cloudflared uruchomiony: {self.tunnel_url}")
                    return True
            
            return False
            
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("❌ cloudflared nie dostępne")
            return False
    
    def start_tunnel(self):
        """Próbuje uruchomić tunnel używając dostępnych opcji"""
        print("🌐 Uruchamiam HTTPS tunnel...")
        
        # Próbuj ngrok
        if self.start_ngrok():
            return True
        
        # Próbuj localtunnel
        if self.start_localtunnel():
            return True
        
        # Próbuj cloudflared
        if self.start_cloudflared():
            return True
        
        print("❌ Nie udało się uruchomić żadnego tunnela")
        print("📋 Opcje instalacji:")
        print("1. ngrok: https://ngrok.com/download")
        print("2. npm/npx: https://nodejs.org/")
        print("3. cloudflared: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/")
        return False
    
    def get_webhook_url(self):
        """Zwraca pełny URL webhook"""
        if self.tunnel_url:
            return f"{self.tunnel_url}/webhook"
        return None
    
    def stop_tunnel(self):
        """Zatrzymuje tunnel"""
        if self.tunnel_process:
            self.tunnel_process.terminate()
            print("🛑 Tunnel zatrzymany")

def main():
    """Główna funkcja"""
    tunnel = TunnelManager(port=5000)
    
    print("🚀 Tunnel Manager - Lesson 19 Webhook")
    print("=" * 50)
    
    # Sprawdź czy serwer działa na porcie 5000
    try:
        requests.get('http://localhost:5000/test', timeout=2)
        print("✅ Serwer webhook działa na porcie 5000")
    except:
        print("❌ Serwer webhook nie działa na porcie 5000")
        print("Uruchom najpierw: python webhook_server.py")
        return 1
    
    # Uruchom tunnel
    if tunnel.start_tunnel():
        webhook_url = tunnel.get_webhook_url()
        print(f"\n🎯 URL webhook: {webhook_url}")
        print(f"📋 Skopiuj ten URL i użyj w report_webhook.py")
        print(f"\nAby przetestować:")
        print(f"curl -X POST {webhook_url} -H 'Content-Type: application/json' -d '{{\"instruction\": \"poleciałem jedno pole w prawo\"}}'")
        
        print(f"\n⌨️  Naciśnij Enter aby zatrzymać tunnel...")
        input()
        tunnel.stop_tunnel()
    else:
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 