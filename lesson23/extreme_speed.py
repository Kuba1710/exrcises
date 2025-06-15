import asyncio
import aiohttp
import time
import os
import openai
from concurrent.futures import ThreadPoolExecutor

class ExtremeSpeedSolver:
    def __init__(self):
        self.api_url = "https://rafal.ag3nts.org/b46c3"
        self.password = "NONOMNISMORIAR"
        
        api_key = os.getenv('OPENAI_API_KEY', '').strip()
        if not api_key:
            raise ValueError("Set OPENAI_API_KEY environment variable")
        
        self.client = openai.OpenAI(api_key=api_key)
        
        # Cache dla promptów - optymalizacja zgodnie ze wskazówkami
        self.prompt_cache = {}
    
    def ultra_fast_llm(self, task: str, data: str) -> str:
        """Najszybsze możliwe wywołanie LLM"""
        # Precyzyjny prompt dla pełnych odpowiedzi
        prompt_key = f"{task[:20]}_{str(data)[:20]}"  # Cache key
        
        if prompt_key in self.prompt_cache:
            return self.prompt_cache[prompt_key]
        
        # Prompt z instrukcją pełnych odpowiedzi
        prompt = f"Task: {task}\nData: {data}\nReturn complete answers in Polish, each on new line with number:"
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,  # Zwiększone dla pełnych odpowiedzi
                temperature=0,
                stream=False
            )
            result = response.choices[0].message.content.strip()
            self.prompt_cache[prompt_key] = result
            return result
        except:
            # Fallback - zwróć pierwsze słowo z danych
            fallback = str(data).split()[0] if str(data).split() else "tak"
            self.prompt_cache[prompt_key] = fallback
            return fallback
    
    async def api_call(self, session, data):
        """Szybkie wywołanie API"""
        async with session.post(self.api_url, json=data) as response:
            return await response.json()
    
    async def get_data(self, session, url):
        """Szybkie pobieranie danych"""
        async with session.get(url) as response:
            return await response.json()
    
    async def run(self):
        """Ultra-szybkie wykonanie"""
        start = time.time()
        
        # Najbardziej agresywne timeouty
        timeout = aiohttp.ClientTimeout(total=20, connect=2)
        connector = aiohttp.TCPConnector(limit=20)
        
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            # 1. Hasło
            hash_resp = await self.api_call(session, {"password": self.password})
            hash_val = hash_resp.get('message', '')
            
            # 2. Hash -> URLs
            urls_resp = await self.api_call(session, {"sign": hash_val})
            message_data = urls_resp.get('message', {})
            challenges = message_data.get('challenges', [])
            signature = message_data.get('signature', '')  # Zapisz signature
            timestamp = message_data.get('timestamp', 0)   # Zapisz timestamp
            
            if len(challenges) < 2:
                raise ValueError("No URLs received")
                
            url0, url1 = challenges[0], challenges[1]
            
            # 3. Równoległe pobieranie
            data0, data1 = await asyncio.gather(
                self.get_data(session, url0),
                self.get_data(session, url1)
            )
            
            # 4. Równoległe LLM
            with ThreadPoolExecutor(max_workers=2) as executor:
                f0 = executor.submit(self.ultra_fast_llm, 
                                   data0.get('task', ''), 
                                   str(data0.get('data', '')))
                f1 = executor.submit(self.ultra_fast_llm, 
                                   data1.get('task', ''), 
                                   str(data1.get('data', '')))
                
                r0, r1 = f0.result(), f1.result()
            
            # 5. Odpowiedź - najprostsza struktura
            final = await self.api_call(session, {
                "answer": [r0, r1], 
                "signature": signature, 
                "timestamp": timestamp,
                "apikey": os.getenv('CENTRALA_API_KEY')
            })
            
            elapsed = time.time() - start
            print(f"Time: {elapsed:.2f}s {'✅' if elapsed <= 6 else '❌'}")
            print(f"Result: {final}")
            
            return final

if __name__ == "__main__":
    solver = ExtremeSpeedSolver()
    asyncio.run(solver.run()) 