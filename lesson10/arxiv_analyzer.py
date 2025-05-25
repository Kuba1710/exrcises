import requests
import json
import os
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
import base64
from io import BytesIO
from dotenv import load_dotenv
import openai
from bs4 import BeautifulSoup
import markdownify

# Load environment variables
load_dotenv()

class ArxivAnalyzer:
    def __init__(self):
        self.api_key = os.getenv('API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-4o')
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=self.openai_api_key)
        
        # URLs
        self.article_url = "https://c3ntrala.ag3nts.org/dane/arxiv-draft.html"
        self.questions_url = f"https://c3ntrala.ag3nts.org/data/{self.api_key}/arxiv.txt"
        self.submit_url = "https://c3ntrala.ag3nts.org/report"
        
        # Cache directories
        self.cache_dir = Path("arxiv_cache")
        self.images_dir = self.cache_dir / "images"
        self.audio_dir = self.cache_dir / "audio"
        self.transcripts_dir = self.cache_dir / "transcripts"
        self.descriptions_dir = self.cache_dir / "descriptions"
        
        # Create cache directories
        for dir_path in [self.cache_dir, self.images_dir, self.audio_dir, 
                        self.transcripts_dir, self.descriptions_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def download_file(self, url, local_path):
        """Download a file from URL to local path"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Downloaded: {url} -> {local_path}")
            return True
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return False
    
    def download_article(self):
        """Download and parse the HTML article"""
        print("Downloading article...")
        response = requests.get(self.article_url)
        response.raise_for_status()
        
        # Save raw HTML
        html_path = self.cache_dir / "article.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        return response.text
    
    def extract_media_urls(self, html_content, base_url):
        """Extract image and audio URLs from HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        images = []
        audio_files = []
        
        # Find images
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                full_url = urljoin(base_url, src)
                alt_text = img.get('alt', '')
                # Get caption from surrounding elements
                caption = ""
                if img.parent and img.parent.name in ['figure', 'div']:
                    caption_elem = img.parent.find(['figcaption', 'caption', 'p'])
                    if caption_elem:
                        caption = caption_elem.get_text().strip()
                
                images.append({
                    'url': full_url,
                    'filename': os.path.basename(urlparse(src).path),
                    'alt': alt_text,
                    'caption': caption
                })
        
        # Find audio files
        for audio in soup.find_all(['audio', 'source']):
            src = audio.get('src')
            if src and src.endswith('.mp3'):
                full_url = urljoin(base_url, src)
                audio_files.append({
                    'url': full_url,
                    'filename': os.path.basename(urlparse(src).path)
                })
        
        # Also check for direct links to audio files
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and href.endswith('.mp3'):
                full_url = urljoin(base_url, href)
                audio_files.append({
                    'url': full_url,
                    'filename': os.path.basename(urlparse(href).path)
                })
        
        return images, audio_files
    
    def convert_html_to_markdown(self, html_content):
        """Convert HTML to clean markdown"""
        # Use markdownify to convert HTML to markdown
        markdown_content = markdownify.markdownify(html_content, heading_style="ATX")
        
        # Clean up the markdown
        # Remove excessive whitespace
        markdown_content = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown_content)
        
        return markdown_content.strip()
    
    def describe_image(self, image_path, context=""):
        """Use OpenAI Vision to describe an image"""
        try:
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            prompt = f"""Describe this image in detail, focusing on:
1. What is shown in the image
2. Any text visible in the image
3. Scientific or technical content if present
4. How it relates to the context: {context}

Provide a comprehensive but concise description."""
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error describing image {image_path}: {e}")
            return f"[Error describing image: {e}]"
    
    def transcribe_audio(self, audio_path):
        """Transcribe audio file using OpenAI Whisper API"""
        try:
            with open(audio_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            return transcript.text
        except Exception as e:
            print(f"Error transcribing audio {audio_path}: {e}")
            return f"[Error transcribing audio: {e}]"
    
    def process_media(self, images, audio_files):
        """Download and process all media files"""
        image_descriptions = {}
        audio_transcripts = {}
        
        # Process images
        print("Processing images...")
        for img in images:
            filename = img['filename']
            if not filename:
                continue
                
            local_path = self.images_dir / filename
            desc_path = self.descriptions_dir / f"{filename}.txt"
            
            # Check if description already exists
            if desc_path.exists():
                with open(desc_path, 'r', encoding='utf-8') as f:
                    description = f.read()
                print(f"Using cached description for {filename}")
            else:
                # Download image if not exists
                if not local_path.exists():
                    if not self.download_file(img['url'], local_path):
                        continue
                
                # Generate description
                context = f"Alt text: {img['alt']}. Caption: {img['caption']}"
                description = self.describe_image(local_path, context)
                
                # Cache description
                with open(desc_path, 'w', encoding='utf-8') as f:
                    f.write(description)
                
                print(f"Generated description for {filename}")
            
            image_descriptions[filename] = {
                'description': description,
                'alt': img['alt'],
                'caption': img['caption']
            }
        
        # Process audio files
        print("Processing audio files...")
        for audio in audio_files:
            filename = audio['filename']
            if not filename:
                continue
                
            local_path = self.audio_dir / filename
            transcript_path = self.transcripts_dir / f"{filename}.txt"
            
            # Check if transcript already exists
            if transcript_path.exists():
                with open(transcript_path, 'r', encoding='utf-8') as f:
                    transcript = f.read()
                print(f"Using cached transcript for {filename}")
            else:
                # Download audio if not exists
                if not local_path.exists():
                    if not self.download_file(audio['url'], local_path):
                        continue
                
                # Generate transcript
                transcript = self.transcribe_audio(local_path)
                
                # Cache transcript
                with open(transcript_path, 'w', encoding='utf-8') as f:
                    f.write(transcript)
                
                print(f"Generated transcript for {filename}")
            
            audio_transcripts[filename] = transcript
        
        return image_descriptions, audio_transcripts
    
    def create_consolidated_markdown(self, html_content, image_descriptions, audio_transcripts):
        """Create a consolidated markdown file with all content"""
        # Convert HTML to markdown
        markdown_content = self.convert_html_to_markdown(html_content)
        
        # Replace image references with descriptions
        for filename, img_data in image_descriptions.items():
            # Find image references in markdown
            img_pattern = rf'!\[.*?\]\([^)]*{re.escape(filename)}[^)]*\)'
            replacement = f"""
**[IMAGE: {filename}]**
Alt text: {img_data['alt']}
Caption: {img_data['caption']}
Description: {img_data['description']}
"""
            markdown_content = re.sub(img_pattern, replacement, markdown_content)
        
        # Add audio transcripts
        if audio_transcripts:
            markdown_content += "\n\n## Audio Transcripts\n\n"
            for filename, transcript in audio_transcripts.items():
                markdown_content += f"**[AUDIO: {filename}]**\n{transcript}\n\n"
        
        # Save consolidated markdown
        consolidated_path = self.cache_dir / "consolidated_article.md"
        with open(consolidated_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"Created consolidated markdown: {consolidated_path}")
        return markdown_content
    
    def get_questions(self):
        """Download questions from Centrala"""
        print("Downloading questions...")
        response = requests.get(self.questions_url)
        response.raise_for_status()
        
        questions_text = response.text.strip()
        
        # Save questions
        questions_path = self.cache_dir / "questions.txt"
        with open(questions_path, 'w', encoding='utf-8') as f:
            f.write(questions_text)
        
        # Parse questions (assuming they're numbered)
        questions = {}
        lines = questions_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and re.match(r'^\d+', line):
                # Extract question number and text
                match = re.match(r'^(\d+)\.?\s*(.+)', line)
                if match:
                    num = match.group(1).zfill(2)  # Pad with zero if needed
                    question = match.group(2)
                    questions[num] = question
        
        return questions
    
    def answer_questions(self, questions, article_content):
        """Use LLM to answer questions based on the article content"""
        answers = {}
        
        # Previous wrong answers to avoid repeating
        wrong_answers = {
            "03": "Co Bomba chciał znaleźć w Grudziądzu?"
        }
        
        system_prompt = """You are an expert at analyzing scientific articles and answering questions based on their content.
You have access to the full article content including text, image descriptions, and audio transcripts.
Provide concise, accurate answers based strictly on the information provided in the article.
Each answer should be a single sentence that directly addresses the question.
Pay special attention to audio transcripts as they may contain crucial information."""
        
        for question_num, question in questions.items():
            print(f"Answering question {question_num}: {question}")
            
            user_prompt = f"""Based on the following article content, answer this question in one sentence:

Question: {question}

Article content:
{article_content}

Answer:"""
            
            # Add feedback for previously wrong answers
            if question_num in wrong_answers:
                user_prompt += f"""

Note: The previous answer "{wrong_answers[question_num]}" was incorrect. 
Please provide a different, more specific answer based on the article content, especially the audio transcripts."""
            
            try:
                response = self.client.chat.completions.create(
                    model=self.openai_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=150,
                    temperature=0.1
                )
                
                answer = response.choices[0].message.content.strip()
                answers[question_num] = answer
                print(f"Answer {question_num}: {answer}")
                
            except Exception as e:
                print(f"Error answering question {question_num}: {e}")
                answers[question_num] = f"Error generating answer: {e}"
        
        return answers
    
    def submit_answers(self, answers):
        """Submit answers to Centrala"""
        payload = {
            "task": "arxiv",
            "apikey": self.api_key,
            "answer": answers
        }
        
        print("Submitting answers...")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(self.submit_url, json=payload)
        
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text}")
        
        return response
    
    def run(self):
        """Main execution flow"""
        try:
            # Step 1: Download article
            html_content = self.download_article()
            
            # Step 2: Extract media URLs
            images, audio_files = self.extract_media_urls(html_content, self.article_url)
            print(f"Found {len(images)} images and {len(audio_files)} audio files")
            
            # Step 3: Process media
            image_descriptions, audio_transcripts = self.process_media(images, audio_files)
            
            # Step 4: Create consolidated content
            consolidated_content = self.create_consolidated_markdown(
                html_content, image_descriptions, audio_transcripts
            )
            
            # Step 5: Get questions
            questions = self.get_questions()
            print(f"Found {len(questions)} questions")
            
            # Step 6: Answer questions
            answers = self.answer_questions(questions, consolidated_content)
            
            # Step 7: Submit answers
            response = self.submit_answers(answers)
            
            return response
            
        except Exception as e:
            print(f"Error in main execution: {e}")
            raise

def main():
    analyzer = ArxivAnalyzer()
    response = analyzer.run()
    
    if response.status_code == 200:
        print("✅ Task completed successfully!")
    else:
        print("❌ Task failed!")

if __name__ == "__main__":
    main() 