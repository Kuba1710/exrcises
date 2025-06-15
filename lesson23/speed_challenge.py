import asyncio
import aiohttp
import time
import json
import os
from typing import Dict, Any
from dotenv import load_dotenv
import openai
from concurrent.futures import ThreadPoolExecutor
import threading

# Ładowanie zmiennych środowiskowych
load_dotenv()

class SpeedChallengeSolver:
    def __init__(self):
        self.api_url = "https://rafal.ag3nts.org/b46c3"
        self.password = "NONOMNISMORIAR"
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("Brak klucza OpenAI API. Ustaw zmienną OPENAI_API_KEY")
        
        self.openai_client = openai.OpenAI(api_key=api_key)
        print(f"Initialized with API key: {api_key[:20]}...")  # Debug
        
    async def send_password(self, session: aiohttp.ClientSession) -> str:
        """Krok 1: Wysyłanie hasła i otrzymywanie HASH"""
        data = {"password": self.password}
        try:
            async with session.post(self.api_url, json=data) as response:
                result = await response.json()
                print(f"Password response: {result}")  # Debug log
                return result.get('message', '')
        except Exception as e:
            print(f"Error sending password: {e}")
            return ''
    
    async def send_hash(self, session: aiohttp.ClientSession, hash_value: str) -> Dict[str, Any]:
        """Krok 2: Wysyłanie HASH i otrzymywanie zadań"""
        data = {"sign": hash_value}
        try:
            async with session.post(self.api_url, json=data) as response:
                result = await response.json()
                print(f"Hash response: {result}")  # Debug log
                return result
        except Exception as e:
            print(f"Error sending hash: {e}")
            return {}
    
    async def fetch_task_data(self, session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
        """Pobieranie danych zadania z podanego URL"""
        try:
            async with session.get(url) as response:
                result = await response.json()
                print(f"Task data from {url}: {result}")  # Debug log
                return result
        except Exception as e:
            print(f"Error fetching data from {url}: {e}")
            return {}
    
    def process_task_fast(self, task: str, data: Any) -> str:
        """Szybkie przetwarzanie zadania z zoptymalizowanym promptem"""
        # Zoptymalizowany prompt dla pełnych odpowiedzi
        prompt = f"Task: {task}\nData: {data}\nReturn complete answers in Polish, each on new line with number:"
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # Szybszy model
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,  # Zwiększone dla pełnych odpowiedzi
                temperature=0,  # Deterministyczne odpowiedzi
                stream=False
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error processing task: {e}")
            return ""
    
    async def solve_challenge(self):
        """Główna funkcja rozwiązująca wyzwanie"""
        start_time = time.time()
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            try:
                # Krok 1: Wysłanie hasła
                print("Wysyłam hasło...")
                hash_value = await self.send_password(session)
                print(f"Otrzymano hash: {hash_value}")
                
                if not hash_value:
                    raise ValueError("Nie otrzymano hash'a z serwera")
                
                # Krok 2: Wysłanie hash
                print("Wysyłam hash...")
                task_info = await self.send_hash(session, hash_value)
                print(f"Otrzymano informacje o zadaniach: {task_info}")
                
                # Sprawdź czy otrzymaliśmy błąd
                if task_info.get('code') == -301:
                    raise ValueError(f"Błąd API: {task_info.get('message', 'Unknown error')}")
                
                # Krok 3: Równoległe pobieranie danych z obu źródeł
                message_data = task_info.get('message', {})
                challenges = message_data.get('challenges', [])
                signature = message_data.get('signature', '')  # Zapisz signature
                timestamp = message_data.get('timestamp', 0)   # Zapisz timestamp
                
                if len(challenges) < 2:
                    raise ValueError("Nie otrzymano wystarczającej liczby URLs do zadań")
                    
                source0_url = challenges[0]
                source1_url = challenges[1]
                
                print("Pobieram dane z obu źródeł równolegle...")
                source0_task = self.fetch_task_data(session, source0_url)
                source1_task = self.fetch_task_data(session, source1_url)
                
                source0_data, source1_data = await asyncio.gather(source0_task, source1_task)
                
                print(f"Source0 data: {source0_data}")
                print(f"Source1 data: {source1_data}")
                
                # Krok 4: Równoległe przetwarzanie zadań
                print("Przetwarzam zadania równolegle...")
                
                # Używam ThreadPoolExecutor dla równoległego przetwarzania LLM
                with ThreadPoolExecutor(max_workers=2) as executor:
                    future0 = executor.submit(
                        self.process_task_fast, 
                        source0_data.get('task', ''), 
                        source0_data.get('data', '')
                    )
                    future1 = executor.submit(
                        self.process_task_fast, 
                        source1_data.get('task', ''), 
                        source1_data.get('data', '')
                    )
                    
                    result0 = future0.result()
                    result1 = future1.result()
                
                print(f"Result0: {result0}")
                print(f"Result1: {result1}")
                
                # Krok 5: Scalanie wyników
                combined_results = {
                    "source0": result0,
                    "source1": result1
                }
                
                # Krok 6: Wysłanie odpowiedzi
                print("Wysyłam końcową odpowiedź...")
                final_data = {
                    "answer": combined_results, 
                    "signature": signature, 
                    "timestamp": timestamp,
                    "apikey": os.getenv('CENTRALA_API_KEY')
                }
                async with session.post(self.api_url, json=final_data) as response:
                    final_result = await response.json()
                    
                end_time = time.time()
                execution_time = end_time - start_time
                
                print(f"Czas wykonania: {execution_time:.2f} sekund")
                print(f"Wynik końcowy: {final_result}")
                
                return final_result
                
            except Exception as e:
                end_time = time.time()
                execution_time = end_time - start_time
                print(f"Błąd: {e}")
                print(f"Czas wykonania przed błędem: {execution_time:.2f} sekund")
                raise

async def main():
    solver = SpeedChallengeSolver()
    return await solver.solve_challenge()

if __name__ == "__main__":
    asyncio.run(main()) 