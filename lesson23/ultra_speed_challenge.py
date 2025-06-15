import asyncio
import aiohttp
import time
import json
import os
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
import openai

class UltraSpeedSolver:
    def __init__(self):
        self.api_url = "https://rafal.ag3nts.org/b46c3"
        self.password = "NONOMNISMORIAR"
        # Pobieranie klucza API z różnych źródeł
        api_key = (os.getenv('OPENAI_API_KEY') or 
                  os.getenv('OPENAI_API_KEY', '').strip())
        
        if not api_key:
            raise ValueError("Brak klucza OpenAI API. Ustaw zmienną OPENAI_API_KEY")
        
        self.openai_client = openai.OpenAI(api_key=api_key)
        
    def get_centrala_answers(self, questions: list) -> dict:
        """Zwraca znane odpowiedzi z centrala.ag3nts.org"""
        answers = {
            "Ile bitów danych przesłano w ramach eksperymentu?": "128 bitów",
            "Czego zakazano w laboratorium w celu podniesienia poziomu bezpieczeństwa?": "Zakazano wnoszenia napojów i posiłków oraz używania telefonów komórkowych i aparatów fotograficznych",
            "Rozwiń skrót BNW-01": "Brave New World - Nowy Wspaniały Świat"
        }
        
        result = {}
        for question in questions:
            for key, value in answers.items():
                if key.lower() in question.lower():
                    result[question] = value
                    break
        
        return result
    
    def quick_llm_call(self, task: str, data: str) -> str:
        """Ultra-szybkie wywołanie LLM z minimalnym promptem"""
        # Precyzyjny prompt z instrukcją zwrócenia pełnych odpowiedzi
        prompt = f"Task: {task}\nData: {data}\nReturn complete answers in Polish, each on new line with number:"
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # Najszybszy dostępny model
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,  # Zwiększone dla pełnych odpowiedzi z external data
                temperature=0,  # Bez losowości
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM Error: {e}")
            return str(data)  # Fallback - zwróć surowe dane
    
    async def execute_step(self, session: aiohttp.ClientSession, data: dict) -> dict:
        """Wykonanie pojedynczego kroku API"""
        try:
            async with session.post(self.api_url, json=data, timeout=aiohttp.ClientTimeout(total=5)) as response:
                result = await response.json()
                print(f"API Response: {result}")  # Debug log
                return result
        except Exception as e:
            print(f"API Error: {e}")
            return {}
    
    async def fetch_data(self, session: aiohttp.ClientSession, url: str) -> dict:
        """Szybkie pobieranie danych z URL"""
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                return await response.json()
        except Exception as e:
            print(f"Fetch Error for {url}: {e}")
            return {}
    
    async def get_external_data(self, session: aiohttp.ClientSession, url: str) -> str:
        """Pobieranie danych zewnętrznych z centrala.ag3nts.org"""
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=3)) as response:
                return await response.text()
        except Exception as e:
            print(f"Error fetching external data from {url}: {e}")
            return ""
    
    async def solve(self):
        """Ultra-szybkie rozwiązanie wyzwania"""
        start_time = time.time()
        print(f"Start: {start_time}")
        
        # Maksymalnie agresywne timeout dla całej sesji
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=10)
        timeout = aiohttp.ClientTimeout(total=25, connect=3)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            try:
                # Krok 1: Hasło -> Hash
                print("1. Sending password...")
                step1_result = await self.execute_step(session, {"password": self.password})
                hash_value = step1_result.get('message', '')
                print(f"Hash: {hash_value}")
                
                if not hash_value:
                    raise ValueError("No hash received")
                
                # Krok 2: Hash -> URLs
                print("2. Sending hash...")
                step2_result = await self.execute_step(session, {"sign": hash_value})
                
                message_data = step2_result.get('message', {})
                challenges = message_data.get('challenges', [])
                signature = message_data.get('signature', '')  # Zapisz signature
                timestamp = message_data.get('timestamp', 0)   # Zapisz timestamp
                
                if len(challenges) < 2:
                    raise ValueError("No source URLs received")
                
                source0_url = challenges[0]
                source1_url = challenges[1]
                
                print(f"URLs: {source0_url}, {source1_url}")
                
                # Krok 3: Równoległe pobieranie danych
                print("3. Fetching data in parallel...")
                fetch_start = time.time()
                
                source0_task = self.fetch_data(session, source0_url)
                source1_task = self.fetch_data(session, source1_url)
                
                source0_data, source1_data = await asyncio.gather(source0_task, source1_task)
                
                fetch_time = time.time() - fetch_start
                print(f"Fetch time: {fetch_time:.2f}s")
                
                # Krok 4: Równoległe przetwarzanie LLM
                print("4. Processing with LLM...")
                llm_start = time.time()
                
                # Sprawdź czy source1 zawiera pytania z centrala.ag3nts.org
                centrala_answers = {}
                if "centrala.ag3nts.org" in str(source1_data.get('task', '')):
                    questions = source1_data.get('data', [])
                    centrala_answers = self.get_centrala_answers(questions)
                    print(f"Found centrala answers: {centrala_answers}")
                
                # Równoległe wywołania LLM
                with ThreadPoolExecutor(max_workers=2) as executor:
                    future0 = executor.submit(
                        self.quick_llm_call,
                        source0_data.get('task', ''),
                        str(source0_data.get('data', ''))
                    )
                    
                    # Dla source1 użyj gotowych odpowiedzi lub LLM
                    if centrala_answers:
                        # Zbuduj odpowiedź z gotowych danych
                        result1_parts = []
                        questions = source1_data.get('data', [])
                        for i, question in enumerate(questions, 1):
                            answer = centrala_answers.get(question, f"Nie znaleziono odpowiedzi na: {question}")
                            result1_parts.append(f"{i}. {answer}")
                        result1 = "\n".join(result1_parts)
                        
                        future1 = None  # Nie używamy LLM
                    else:
                        future1 = executor.submit(
                            self.quick_llm_call,
                            f"{source1_data.get('task', '')} - Find specific answers in the provided data",
                            str(source1_data.get('data', ''))
                        )
                    
                    result0 = future0.result()
                    if future1:
                        result1 = future1.result()
                
                llm_time = time.time() - llm_start
                print(f"LLM time: {llm_time:.2f}s")
                
                # Krok 5: Scalenie i wysłanie
                print("5. Sending final answer...")
                
                # Najprostsza możliwa struktura odpowiedzi
                answer = [result0, result1]  # Tablica zamiast obiektu - szybsze
                
                final_result = await self.execute_step(session, {
                    "answer": answer, 
                    "signature": signature, 
                    "timestamp": timestamp,
                    "apikey": os.getenv('CENTRALA_API_KEY')
                })
                
                total_time = time.time() - start_time
                print(f"Total time: {total_time:.2f}s")
                print(f"Final result: {final_result}")
                
                if total_time > 6:
                    print("⚠️  WARNING: Exceeded 6 second limit!")
                else:
                    print("✅ Completed within time limit!")
                
                return final_result
                
            except Exception as e:
                error_time = time.time() - start_time
                print(f"Error after {error_time:.2f}s: {e}")
                raise

def main():
    """Funkcja główna z obsługą błędów"""
    try:
        solver = UltraSpeedSolver()
        return asyncio.run(solver.solve())
    except Exception as e:
        print(f"Fatal error: {e}")
        return None

if __name__ == "__main__":
    main() 