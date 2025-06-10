import os
import json
import requests
import fitz  # PyMuPDF
from PIL import Image
import io
from openai import OpenAI
from dotenv import load_dotenv
import base64

# Load environment variables
load_dotenv('../.env')

class NotesAnalyzer:
    def __init__(self):
        self.personal_api_key = os.getenv('CENTRALA_API_KEY')
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Debug: Check if API keys are loaded
        if not self.personal_api_key:
            print("ERROR: PERSONAL_API_KEY not found!")
            print(f"Current working directory: {os.getcwd()}")
            print("Please check if .env file exists and contains PERSONAL_API_KEY")
            exit(1)
        
        print(f"API Key loaded: {self.personal_api_key[:10]}...")
        
        self.centrala_url = "https://c3ntrala.ag3nts.org"
        self.pdf_url = "https://c3ntrala.ag3nts.org/dane/notatnik-rafala.pdf"
        self.questions_url = f"{self.centrala_url}/data/{self.personal_api_key}/notes.json"
        self.submit_url = f"{self.centrala_url}/report"
        
    def download_pdf(self):
        """Download PDF from the URL"""
        print("Downloading PDF...")
        response = requests.get(self.pdf_url)
        response.raise_for_status()
        return response.content
    
    def get_questions(self):
        """Get questions from the API"""
        print("Fetching questions...")
        response = requests.get(self.questions_url)
        response.raise_for_status()
        return response.json()
    
    def extract_text_from_pdf(self, pdf_content):
        """Extract text from pages 1-18 of PDF"""
        print("Extracting text from PDF pages 1-18...")
        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
        
        extracted_text = ""
        for page_num in range(min(18, pdf_document.page_count)):  # Pages 1-18 (0-indexed: 0-17)
            page = pdf_document.load_page(page_num)  # Fixed: use load_page instead of page_num
            text = page.get_text()
            extracted_text += f"\n--- Page {page_num + 1} ---\n{text}\n"
        
        pdf_document.close()
        return extracted_text
    
    def extract_page_19_as_image(self, pdf_content):
        """Extract page 19 as image for OCR using PyMuPDF"""
        print("Extracting page 19 as image...")
        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
        
        # Check if page 19 exists (0-indexed: page 18)
        if pdf_document.page_count <= 18:
            raise Exception("PDF doesn't have page 19")
        
        # Get page 19 (0-indexed: page 18)
        page = pdf_document.load_page(18)
        
        # Convert page to image (pixmap)
        # Use high resolution for better OCR
        mat = fitz.Matrix(3.0, 3.0)  # 3x zoom for better quality
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        # Convert to base64 for OpenAI API
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Encode to base64
        img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
        
        pdf_document.close()
        return img_base64
    
    def ocr_page_19(self, image_base64, full_context=""):
        """Use OpenAI Vision API to read text from page 19 image"""
        print("Performing OCR on page 19...")
        
        # Prepare context information
        context_info = ""
        if full_context:
            context_info = f"""
KONTEKST CAŁEGO NOTATNIKA:
{full_context}

UWAGA: Analizujesz ostatnią stronę (19) tego notatnika. Użyj kontekstu aby lepiej zrozumieć fragmenty tekstu, obrazy, szkice lub symbole na tej stronie.
"""
        
        # Try multiple approaches to OCR with context
        approaches = [
            f"""{context_info}
Na tym obrazie jest ostatnia strona notatnika Rafała. Opisz dokładnie wszystko co widzisz - tekst, daty, nazwy miejscowości, szkice, mapy, symbole. 

Szczególnie szukaj:
1. Nazw miejsc gdzie Rafał chce się dostać 
2. Dat i odniesień czasowych
3. Szkiców, map lub symboli
4. Fragmentów tekstu które mogą wskazywać na miejsce docelowe

Wypisz wszystko co widzisz, nawet jeśli jest nieczytelne.""",

            f"""{context_info}
Analizuj ten obraz strony notatnika. Z kontekstu wiesz że Rafał planuje podróż. Co widzisz na tej stronie co może wskazywać na miejsce docelowe? Czy są jakieś szkice, mapy, nazwy miejsc napisane odręcznie?""",

            f"""{context_info}
This is the last page of Rafał's notebook. Based on the context, he's planning a journey. What do you see on this page - text, place names, sketches, maps, symbols? Focus on any destination information.""",

            f"""{context_info}
Na tej stronie notatnika może być kluczowa informacja o miejscu gdzie chce pojechać Rafał. Przeczytaj dokładnie wszystkie fragmenty tekstu i opisz wszystkie rysunki, szkice lub symbole. Pamiętaj że może to nie być zwykły tekst ale obrazek czy mapa."""
        ]
        
        for i, prompt in enumerate(approaches):
            try:
                print(f"OCR attempt {i+1}/4 with context-aware prompt...")
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{image_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=1500,
                    temperature=0.1
                )
                
                ocr_text = response.choices[0].message.content
                print(f"OCR attempt {i+1} result: {ocr_text}")
                
                # If we get a refusal, try next approach
                if any(refusal in ocr_text.lower() for refusal in ["sorry", "can't", "unable", "nie mogę"]):
                    print(f"OCR attempt {i+1} refused, trying next approach...")
                    continue
                else:
                    print(f"OCR attempt {i+1} succeeded!")
                    return ocr_text
                    
            except Exception as e:
                print(f"Error during OCR attempt {i+1}: {e}")
                continue
        
        print("All OCR attempts failed")
        return "Błąd OCR - nie udało się odczytać strony 19 żadną metodą"
    
    def prepare_context(self, text_pages_1_18, ocr_page_19):
        """Prepare full context from notebook"""
        context = f"""
NOTATNIK RAFAŁA - PEŁNA TREŚĆ

=== STRONY 1-18 ===
{text_pages_1_18}

=== STRONA 19 (OCR) ===
{ocr_page_19}

UWAGA: Strona 19 została przetworzona przez OCR i może zawierać błędy transkrypcji.
"""
        return context
    
    def answer_question(self, question, context, previous_attempts=None):
        """Answer a single question using the context"""
        print(f"Answering question: {question}")
        
        attempt_info = ""
        if previous_attempts:
            attempt_info = f"""
UWAGA: Poprzednie próby odpowiedzi na to pytanie:
{previous_attempts}

Unikaj tych błędnych odpowiedzi i weź pod uwagę podpowiedzi.
"""
        
        # Special handling for question 01 about the year
        if "Do którego roku przeniósł się" in question:
            prompt = f"""
Masz dostęp do pełnej treści notatnika Rafała. Odpowiedz na pytanie w sposób zwięzły i precyzyjny.

{attempt_info}

PYTANIE: {question}

KONTEKST (notatnik Rafała):
{context}

KLUCZOWE INFORMACJE DO ANALIZY:
1. Na stronie 1: "nie mogę uwierzyć, że jestem w 20... roku" (rok ocenzurowany)
2. Na stronie 4: "Dlaczego Adam wybrał akurat ten rok? Według jego wyliczeń, wtedy powinniśmy rozpocząć pracę nad technologią LLM"
3. Na stronie 5: "No i powstało GPT-2. Słyszałem w wiadomościach, a to wszystko dzięki badaniom, które dostarczyłem"
4. Na stronie 8: "Czekają mnie dwa lata bardzo intensywnej nauki"
5. Na stronie 12: "On mówił, że po 2024 roku tak będzie wyglądać codzienność" - 2024 to przyszłość względem roku Rafała
6. Na stronie 19: "Data: 2236" (może być błędny OCR)
7. Historyczny fakt: GPT-2 zostało opublikowane w lutym 2019
8. Na stronie 10: "Który mamy rok? When am I?" - Rafał nie wie w którym roku jest

ANALIZA:
- Adam wybrał rok do rozpoczęcia prac nad LLM
- Te prace doprowadziły do powstania GPT-2 
- Rafał pomógł dostarczając badania
- GPT-2 powstało w rzeczywistości w 2019
- Ale może Adam wybrał wcześniejszy rok, żeby rozpocząć prace?
- Może to nie jest rok w formacie YYYY?
- Może to rok z przeszłości (przed naszą erą)?
- Uwzględnij odwołania do wydarzeń i wszystkie fakty

BŁĘDNE PRÓBY: {previous_attempts if previous_attempts else "Brak"}

INSTRUKCJE:
- Uwzględnij wszystkie fakty podane w tekście, w szczególności odwołania do wydarzeń
- Zastanów się czy to może być rok przed naszą erą, rok w innym formacie, czy coś innego
- Może odpowiedź nie jest liczbą?
- Przeanalizuj logicznie wszystkie wskazówki

ODPOWIEDŹ (tylko konkretny rok lub inna odpowiedź):
"""
        else:
            prompt = f"""
Masz dostęp do pełnej treści notatnika Rafała. Odpowiedz na pytanie w sposób zwięzły i precyzyjny.

{attempt_info}

PYTANIE: {question}

KONTEKST (notatnik Rafała):
{context}

INSTRUKCJE:
- Odpowiedz tylko konkretną informacją, bez dodatkowych słów
- Jeśli pytanie dotyczy daty, odpowiedz w formacie YYYY-MM-DD
- Jeśli pytanie dotyczy miejscowości, podaj dokładną nazwę
- Jeśli trzeba coś obliczyć na podstawie danych z notatnika, zrób to
- Pamiętaj, że strona 19 była przetworzona przez OCR i może zawierać błędy - skup się na logice i kontekście

ODPOWIEDŹ:
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Jesteś ekspertem w analizie dokumentów. Odpowiadasz zwięźle i precyzyjnie na podstawie podanego kontekstu."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            answer = response.choices[0].message.content.strip()
            print(f"Answer: {answer}")
            return answer
            
        except Exception as e:
            print(f"Error answering question: {e}")
            return "Error"
    
    def submit_answers(self, answers):
        """Submit answers to the API"""
        print("Submitting answers...")
        
        payload = {
            "task": "notes",
            "apikey": self.personal_api_key,
            "answer": answers
        }
        
        try:
            response = requests.post(self.submit_url, json=payload)
            result = response.json()
            print(f"Submission result: {result}")
            return result
            
        except Exception as e:
            print(f"Error submitting answers: {e}")
            return {"error": str(e)}
    
    def run_with_iterations(self):
        """Main execution function with iterative improvements"""
        print("Starting Notes Analyzer...")
        
        # Download PDF and questions
        pdf_content = self.download_pdf()
        questions = self.get_questions()
        
        print(f"Questions received: {questions}")
        
        # Extract text from pages 1-18
        text_pages_1_18 = self.extract_text_from_pdf(pdf_content)
        
        # Extract and OCR page 19 WITH CONTEXT from pages 1-18
        page_19_image = self.extract_page_19_as_image(pdf_content)
        ocr_page_19 = self.ocr_page_19(page_19_image, text_pages_1_18)
        
        # Prepare full context
        context = self.prepare_context(text_pages_1_18, ocr_page_19)
        
        # Save context to file for debugging
        with open('context.txt', 'w', encoding='utf-8') as f:
            f.write(context)
        print("Context saved to context.txt")
        
        # Track attempts for each question
        question_attempts = {}
        
        max_iterations = 5
        for iteration in range(max_iterations):
            print(f"\n=== ITERATION {iteration + 1} ===")
            
            # Answer questions
            answers = {}
            for question_id, question_text in questions.items():
                previous_attempts = question_attempts.get(question_id, "")
                if previous_attempts:
                    print(f"Previous attempts for question {question_id}: {previous_attempts}")
                answer = self.answer_question(question_text, context, previous_attempts)
                answers[question_id] = answer
            
            print(f"All answers for iteration {iteration + 1}: {answers}")
            
            # Submit answers
            result = self.submit_answers(answers)
            print(f"Submission result: {result}")
            
            # Check if successful (code 0 or positive message)
            if result.get('code') == 0:
                print("SUCCESS! All answers correct.")
                return result
            
            # Parse error message and extract which question failed
            error_message = result.get('message', '')
            hint = result.get('hint', '')
            debug_info = result.get('debug', '')
            
            print(f"Error message: {error_message}")
            print(f"Hint: {hint}")
            print(f"Debug info: {debug_info}")
            
            # Parse different types of error messages
            failed_question = None
            sent_answer = ""
            
            # Try to extract question number from various error message formats
            import re
            
            # Format: "Answer for question 01 is incorrect"
            question_match = re.search(r'question (\d+)', error_message)
            if question_match:
                failed_question = question_match.group(1).zfill(2)
            
            # Extract sent answer from debug info
            if debug_info and 'You sent:' in debug_info:
                sent_answer = debug_info.replace('You sent: ', '').strip()
            elif debug_info:
                sent_answer = debug_info.strip()
            
            # If we identified a failed question, record the attempt
            if failed_question:
                attempt_record = f"""
POPRZEDNIA BŁĘDNA PRÓBA:
- Pytanie: {questions.get(failed_question, 'Unknown')}
- Twoja odpowiedź: {sent_answer}
- Błąd: {error_message}
- Podpowiedź: {hint}

"""
                if failed_question in question_attempts:
                    question_attempts[failed_question] += attempt_record
                else:
                    question_attempts[failed_question] = attempt_record
                
                print(f"Recorded failed attempt for question {failed_question}")
            else:
                # If we couldn't parse the specific question, it might be a general error
                # Try to find patterns or assume it's question 01 if unclear
                print("Could not identify specific failed question, assuming general error")
                
                # Add error info to all questions that might be wrong
                for q_id in questions.keys():
                    attempt_record = f"""
POPRZEDNIA OGÓLNA BŁĘDNA PRÓBA:
- Błąd: {error_message}
- Podpowiedź: {hint}
- Debug: {debug_info}

"""
                    if q_id in question_attempts:
                        question_attempts[q_id] += attempt_record
                    else:
                        question_attempts[q_id] = attempt_record
            
            # If last iteration, break
            if iteration == max_iterations - 1:
                print("Maximum iterations reached.")
                break
        
        return result
    
    def run(self):
        """Simple run for backward compatibility"""
        return self.run_with_iterations()

if __name__ == "__main__":
    analyzer = NotesAnalyzer()
    result = analyzer.run()
    print(f"\nFinal result: {result}") 