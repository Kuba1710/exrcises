import os
import json
import requests
from bs4 import BeautifulSoup
import html2text
from openai import OpenAI
from dotenv import load_dotenv
from urllib.parse import urljoin, urlparse
import time

# Load environment variables
load_dotenv('../../3rd-devs/.env')

class SoftoAgent:
    def __init__(self):
        self.api_key = os.getenv('PERSONAL_API_KEY')
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.base_url = "https://softo.ag3nts.org"
        self.centrala_url = "https://c3ntrala.ag3nts.org"
        self.visited_urls = set()
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True
        
    def fetch_questions(self):
        """Fetch questions from centrala API"""
        url = f"{self.centrala_url}/data/{self.api_key}/softo.json"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching questions: {e}")
            return None
    
    def fetch_page_content(self, url):
        """Fetch and convert HTML page to markdown"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse HTML and convert to markdown
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Convert to markdown
            markdown_content = self.html_converter.handle(str(soup))
            
            # Extract links for navigation
            links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href:
                    full_url = urljoin(url, href)
                    link_text = link.get_text(strip=True)
                    if link_text and self.is_valid_link(full_url):
                        links.append({
                            'url': full_url,
                            'text': link_text
                        })
            
            return {
                'content': markdown_content,
                'links': links
            }
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def is_valid_link(self, url):
        """Check if link is valid for navigation"""
        parsed = urlparse(url)
        # Only follow links within the softo domain
        return parsed.netloc == 'softo.ag3nts.org' or parsed.netloc == ''
    
    def ask_llm_for_answer(self, page_content, question):
        """Ask LLM if the page contains answer to the question"""
        prompt = f"""
Przeanalizuj poniższą treść strony internetowej i odpowiedz, czy zawiera ona odpowiedź na podane pytanie.

PYTANIE: {question}

TREŚĆ STRONY:
{page_content}

Odpowiedz w formacie JSON:
{{
    "has_answer": true/false,
    "answer": "konkretna odpowiedź (tylko jeśli has_answer=true)" lub null,
    "reasoning": "krótkie uzasadnienie"
}}

WAŻNE: Jeśli znajdziesz odpowiedź, podaj ją w maksymalnie zwięzłej formie - tylko konkretną informację, bez dodatkowych słów.
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Jesteś ekspertem w analizie treści stron internetowych. Odpowiadasz precyzyjnie i zwięźle w formacie JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            response_text = response.choices[0].message.content
            print(f"LLM response: {response_text}")
            
            # Try to extract JSON from the response
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "{" in response_text and "}" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_text = response_text[json_start:json_end]
            else:
                json_text = response_text
            
            result = json.loads(json_text)
            return result
        except Exception as e:
            print(f"Error asking LLM for answer: {e}")
            print(f"Raw response: {response_text if 'response_text' in locals() else 'No response'}")
            return {"has_answer": False, "answer": None, "reasoning": "Error occurred"}
    
    def ask_llm_for_link(self, page_content, question, links):
        """Ask LLM which link to follow next"""
        links_text = "\n".join([f"- {link['text']}: {link['url']}" for link in links])
        
        prompt = f"""
Przeanalizuj treść strony i dostępne linki, aby wybrać najlepszy link do znalezienia odpowiedzi na pytanie.

PYTANIE: {question}

TREŚĆ STRONY:
{page_content}

DOSTĘPNE LINKI:
{links_text}

Odpowiedz w formacie JSON:
{{
    "selected_url": "URL wybranego linku",
    "reasoning": "krótkie uzasadnienie wyboru"
}}

Wybierz link, który najprawdopodobniej doprowadzi do odpowiedzi na pytanie.
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Jesteś ekspertem w nawigacji po stronach internetowych. Wybierasz najlepsze ścieżki do znalezienia informacji. Odpowiadasz w formacie JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            response_text = response.choices[0].message.content
            print(f"LLM link response: {response_text}")
            
            # Try to extract JSON from the response
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "{" in response_text and "}" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_text = response_text[json_start:json_end]
            else:
                json_text = response_text
            
            result = json.loads(json_text)
            return result.get('selected_url')
        except Exception as e:
            print(f"Error asking LLM for link: {e}")
            print(f"Raw response: {response_text if 'response_text' in locals() else 'No response'}")
            return None
    
    def search_for_answer(self, question, max_depth=5):
        """Search for answer to a specific question"""
        print(f"\nSearching for answer to: {question}")
        
        # Reset visited URLs for each question
        self.visited_urls.clear()
        current_url = self.base_url
        depth = 0
        
        while depth < max_depth:
            print(f"Depth {depth}: Visiting {current_url}")
            
            if current_url in self.visited_urls:
                print("URL already visited, stopping to avoid loop")
                break
                
            self.visited_urls.add(current_url)
            
            # Fetch page content
            page_data = self.fetch_page_content(current_url)
            if not page_data:
                print("Failed to fetch page content")
                break
            
            # Ask LLM if page contains answer
            llm_response = self.ask_llm_for_answer(page_data['content'], question)
            print(f"LLM analysis: {llm_response['reasoning']}")
            
            if llm_response['has_answer'] and llm_response['answer']:
                print(f"Found answer: {llm_response['answer']}")
                return llm_response['answer']
            
            # If no answer, ask LLM which link to follow
            if page_data['links']:
                # Filter out already visited links
                unvisited_links = [link for link in page_data['links'] if link['url'] not in self.visited_urls]
                
                if not unvisited_links:
                    print("No unvisited links available")
                    break
                
                next_url = self.ask_llm_for_link(page_data['content'], question, unvisited_links)
                if next_url:
                    current_url = next_url
                    depth += 1
                    time.sleep(1)  # Be respectful to the server
                else:
                    print("LLM couldn't select a link")
                    break
            else:
                print("No links available on page")
                break
        
        print(f"Could not find answer after {depth} steps")
        return None
    
    def submit_answers(self, answers):
        """Submit answers to centrala"""
        payload = {
            "task": "softo",
            "apikey": self.api_key,
            "answer": answers
        }
        
        try:
            response = requests.post(
                f"{self.centrala_url}/report",
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error submitting answers: {e}")
            return None
    
    def run(self):
        """Main execution method"""
        print("Starting SoftoAI information search agent...")
        
        # Fetch questions
        questions_data = self.fetch_questions()
        if not questions_data:
            print("Failed to fetch questions")
            return
        
        print(f"Fetched questions: {questions_data}")
        
        # Search for answers
        answers = {}
        for question_id, question_text in questions_data.items():
            if question_id in ['01', '02', '03']:
                print(f"\n{'='*50}")
                print(f"Processing question {question_id}: {question_text}")
                
                answer = self.search_for_answer(question_text)
                if answer:
                    answers[question_id] = answer
                    print(f"Answer for {question_id}: {answer}")
                else:
                    print(f"No answer found for question {question_id}")
                    answers[question_id] = "Nie znaleziono odpowiedzi"
        
        print(f"\n{'='*50}")
        print("Final answers:")
        for qid, ans in answers.items():
            print(f"{qid}: {ans}")
        
        # Submit answers
        if answers:
            print("\nSubmitting answers...")
            result = self.submit_answers(answers)
            if result:
                print(f"Submission result: {result}")
            else:
                print("Failed to submit answers")
        
        return answers

if __name__ == "__main__":
    agent = SoftoAgent()
    agent.run() 