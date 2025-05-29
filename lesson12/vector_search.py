import os
import requests
import zipfile
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
import openai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Load environment variables
load_dotenv()

class VectorSearchTask:
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.centrala_api_key = os.getenv('CENTRALA_API_KEY')
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        if not self.centrala_api_key:
            raise ValueError("CENTRALA_API_KEY not found in environment variables")
            
        # Initialize OpenAI client
        openai.api_key = self.openai_api_key
        
        # Initialize Qdrant client (local instance)
        self.qdrant_client = QdrantClient("localhost", port=6333)
        
        # Configuration
        self.collection_name = "weapons_reports"
        self.embedding_model = "text-embedding-3-large"
        self.embedding_dimensions = 3072  # text-embedding-3-large dimensions
        
        # Paths
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
    def download_and_extract_data(self):
        """Download and extract the data archives"""
        print("1. Downloading and extracting data...")
        
        # Download main archive
        main_archive_url = "https://c3ntrala.ag3nts.org/dane/pliki_z_fabryki.zip"
        main_archive_path = self.data_dir / "pliki_z_fabryki.zip"
        
        print(f"Downloading {main_archive_url}...")
        response = requests.get(main_archive_url)
        response.raise_for_status()
        
        with open(main_archive_path, 'wb') as f:
            f.write(response.content)
        
        # Extract main archive
        print("Extracting main archive...")
        with zipfile.ZipFile(main_archive_path, 'r') as zip_ref:
            zip_ref.extractall(self.data_dir)
        
        # Extract encrypted weapons_tests.zip with password
        weapons_archive_path = self.data_dir / "weapons_tests.zip"
        if not weapons_archive_path.exists():
            raise FileNotFoundError("weapons_tests.zip not found in extracted files")
        
        print("Extracting weapons_tests.zip with password...")
        with zipfile.ZipFile(weapons_archive_path, 'r') as zip_ref:
            zip_ref.extractall(self.data_dir / "weapons_tests", pwd=b"1670")
        
        # Debug: Show extracted directory structure
        weapons_tests_dir = self.data_dir / "weapons_tests"
        print(f"Contents of {weapons_tests_dir}:")
        for item in weapons_tests_dir.rglob("*"):
            if item.is_file():
                print(f"  File: {item.relative_to(weapons_tests_dir)}")
            elif item.is_dir():
                print(f"  Dir:  {item.relative_to(weapons_tests_dir)}/")
        
        print("Data extraction completed!")
        
    def setup_vector_database(self):
        """Setup Qdrant collection for reports"""
        print("2. Setting up vector database...")
        
        # Delete collection if it exists
        try:
            self.qdrant_client.delete_collection(self.collection_name)
            print(f"Deleted existing collection: {self.collection_name}")
        except Exception:
            pass
        
        # Create new collection
        self.qdrant_client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.embedding_dimensions,
                distance=Distance.COSINE
            )
        )
        print(f"Created collection: {self.collection_name} with {self.embedding_dimensions} dimensions")
        
    def extract_date_from_filename(self, filename: str) -> str:
        """Extract date from filename and convert to YYYY-MM-DD format"""
        print(f"    Extracting date from filename: {filename}")
        
        # Pattern to match date in filename like 2024-02-21_XR-5_report.txt
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD format
            r'(\d{4}_\d{2}_\d{2})',  # YYYY_MM_DD format
            r'(\d{2}-\d{2}-\d{4})',  # DD-MM-YYYY format
            r'(\d{2}_\d{2}_\d{4})',  # DD_MM_YYYY format
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, filename)
            if match:
                date_str = match.group(1)
                print(f"    Found date string: {date_str}")
                
                # Convert to YYYY-MM-DD format if needed
                if '_' in date_str:
                    date_str = date_str.replace('_', '-')
                
                # Handle DD-MM-YYYY format
                if len(date_str.split('-')[0]) == 2:
                    parts = date_str.split('-')
                    date_str = f"{parts[2]}-{parts[1]}-{parts[0]}"
                
                print(f"    Normalized date: {date_str}")
                return date_str
        
        raise ValueError(f"Could not extract date from filename: {filename}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for given text using OpenAI"""
        try:
            response = openai.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise
    
    def index_reports(self):
        """Index all reports in the vector database"""
        print("3. Indexing reports...")
        
        # Look for txt files in the do-not-share subdirectory
        reports_dir = self.data_dir / "weapons_tests" / "do-not-share"
        
        # If do-not-share doesn't exist, try the main weapons_tests directory
        if not reports_dir.exists():
            reports_dir = self.data_dir / "weapons_tests"
        
        txt_files = list(reports_dir.glob("*.txt"))
        
        # If no files found in main directory, try searching recursively
        if not txt_files:
            weapons_tests_dir = self.data_dir / "weapons_tests"
            txt_files = list(weapons_tests_dir.rglob("*.txt"))
        
        if not txt_files:
            raise FileNotFoundError("No .txt files found in weapons_tests directory or subdirectories")
        
        print(f"Found {len(txt_files)} report files")
        
        points = []
        
        for i, txt_file in enumerate(txt_files):
            print(f"Processing {txt_file.name} ({i+1}/{len(txt_files)})...")
            
            # Extract date from filename
            try:
                report_date = self.extract_date_from_filename(txt_file.name)
                print(f"  Extracted date: {report_date}")
            except ValueError as e:
                print(f"  Warning: {e}")
                continue
            
            # Read report content
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"  Content length: {len(content)} characters")
                
                if not content.strip():
                    print(f"  Warning: Empty content in {txt_file.name}")
                    continue
                    
            except Exception as e:
                print(f"  Error reading file {txt_file.name}: {e}")
                continue
            
            # Generate embedding
            try:
                print(f"  Generating embedding...")
                embedding = self.generate_embedding(content)
                print(f"  Embedding generated with {len(embedding)} dimensions")
            except Exception as e:
                print(f"  Error generating embedding for {txt_file.name}: {e}")
                continue
            
            # Create point for Qdrant
            point = PointStruct(
                id=i,
                vector=embedding,
                payload={
                    "date": report_date,
                    "filename": txt_file.name,
                    "content": content
                }
            )
            points.append(point)
            print(f"  Point created successfully")
        
        if not points:
            raise ValueError("No valid points were created from the report files")
        
        print(f"Created {len(points)} valid points, uploading to Qdrant...")
        
        # Upload points to Qdrant
        try:
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            print(f"Indexed {len(points)} reports successfully!")
        except Exception as e:
            print(f"Error uploading to Qdrant: {e}")
            raise
    
    def search_for_theft_report(self) -> str:
        """Search for report mentioning prototype weapon theft"""
        print("4. Searching for theft report...")
        
        # The question to search for
        question = "W raporcie, z którego dnia znajduje się wzmianka o kradzieży prototypu broni?"
        
        # Generate embedding for the question
        question_embedding = self.generate_embedding(question)
        
        # Search in Qdrant
        search_results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=question_embedding,
            limit=1
        )
        
        if not search_results:
            raise ValueError("No search results found")
        
        # Get the date from the most relevant result
        best_match = search_results[0]
        report_date = best_match.payload["date"]
        
        print(f"Found theft report from date: {report_date}")
        print(f"Filename: {best_match.payload['filename']}")
        print(f"Score: {best_match.score}")
        
        return report_date
    
    def send_answer(self, answer_date: str):
        """Send the answer to centrala"""
        print("5. Sending answer to centrala...")
        
        answer_payload = {
            "task": "wektory",
            "apikey": self.centrala_api_key,
            "answer": answer_date
        }
        
        response = requests.post(
            "https://centrala.ag3nts.org/report",
            json=answer_payload
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")
        
        return response
    
    def run(self):
        """Run the complete task"""
        try:
            # Step 1: Download and extract data
            self.download_and_extract_data()
            
            # Step 2: Setup vector database
            self.setup_vector_database()
            
            # Step 3: Index reports
            self.index_reports()
            
            # Step 4: Search for theft report
            theft_date = self.search_for_theft_report()
            
            # Step 5: Send answer
            response = self.send_answer(theft_date)
            
            print("\nTask completed successfully!")
            return theft_date, response
            
        except Exception as e:
            print(f"Error during task execution: {e}")
            raise

def main():
    """Main function to run the vector search task"""
    print("Starting Vector Search Task...")
    print("=" * 50)
    
    # Check if Qdrant is running
    try:
        client = QdrantClient("localhost", port=6333)
        client.get_collections()
        print("✓ Qdrant is running")
    except Exception as e:
        print("✗ Qdrant is not running. Please start Qdrant first:")
        print("  docker run -p 6333:6333 qdrant/qdrant")
        return
    
    # Run the task
    task = VectorSearchTask()
    result = task.run()
    
    print("=" * 50)
    print("Task completed!")

if __name__ == "__main__":
    main() 