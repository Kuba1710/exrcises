# Vector Search Task - Lesson 12

This directory contains scripts to complete the vector search task for finding weapon theft reports.

## Task Overview

The task involves:
1. Downloading and extracting encrypted archives containing weapon test reports
2. Setting up a Qdrant vector database
3. Indexing reports using OpenAI embeddings
4. Searching for reports mentioning prototype weapon theft
5. Sending the answer to centrala

## Prerequisites

1. **Docker** - Required to run Qdrant vector database
   - Install from: https://docs.docker.com/get-docker/

2. **API Keys** - Add to `../env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   CENTRALA_API_KEY=your_centrala_api_key_here
   ```

## Files

- `vector_search.py` - Main script that performs the complete task
- `setup_and_run.py` - Helper script that sets up environment and runs the task
- `README.md` - This file

## Usage

### Option 1: Automated Setup and Run (Recommended)

```bash
cd exrcises/lesson12
python setup_and_run.py
```

This script will:
- Check if Docker is installed
- Verify API keys in .env file
- Install Python dependencies
- Start Qdrant in Docker
- Run the main task
- Optionally clean up afterwards

### Option 2: Manual Setup

1. **Install dependencies:**
   ```bash
   pip install -r ../requirements.txt
   ```

2. **Start Qdrant:**
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   ```

3. **Run the task:**
   ```bash
   python vector_search.py
   ```

## How It Works

### 1. Data Download and Extraction
- Downloads `pliki_z_fabryki.zip` from centrala
- Extracts the encrypted `weapons_tests.zip` using password "1670"
- Extracts individual report files

### 2. Vector Database Setup
- Creates a Qdrant collection with 3072 dimensions (for text-embedding-3-large)
- Uses cosine distance for similarity search

### 3. Report Indexing
- Extracts dates from filenames (format: YYYY-MM-DD)
- Reads report content
- Generates embeddings using OpenAI's text-embedding-3-large
- Stores vectors with metadata (date, filename, content)

### 4. Search and Answer
- Generates embedding for the search question
- Performs vector similarity search
- Extracts date from the most relevant result
- Sends answer to centrala

## Technical Details

- **Embedding Model**: text-embedding-3-large (3072 dimensions)
- **Vector Database**: Qdrant (local Docker instance)
- **Distance Metric**: Cosine similarity
- **Search Question**: "W raporcie, z którego dnia znajduje się wzmianka o kradzieży prototypu broni?"

## Troubleshooting

### Qdrant Issues
- Ensure Docker is running
- Check if port 6333 is available
- View Qdrant logs: `docker logs qdrant-lesson12`

### API Key Issues
- Verify .env file exists in `exrcises/` directory
- Check API key format and validity

### Dimension Mismatch
- The script uses text-embedding-3-large (3072 dimensions)
- Qdrant collection is configured with matching dimensions
- If changing models, update `embedding_dimensions` in the script

## Output

The script will:
1. Download and extract data
2. Set up vector database
3. Index all reports
4. Search for theft mention
5. Display the found date and send to centrala
6. Show the response from centrala

Example output:
```
Found theft report from date: 2024-02-15
Filename: 2024-02-15_XR-7_report.txt
Score: 0.85
Response status: 200
Response content: {"message": "Correct answer!"}
``` 