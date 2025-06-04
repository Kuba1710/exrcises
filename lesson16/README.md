# Photos Task - Barbara Description Generator

This script analyzes damaged photos from centrala to create a detailed description of Barbara.

## Features

- Communicates with centrala's photo repair automaton
- Uses OpenAI Vision API to analyze photo quality
- Automatically suggests and applies photo repair operations (REPAIR, BRIGHTEN, DARKEN)
- Creates detailed description of Barbara in Polish
- Handles multiple iterations of photo processing

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure the `.env` file in the parent directory contains:
```
CENTRALA_API_KEY=your_centrala_api_key
OPENAI_API_KEY=your_openai_api_key
```

## Usage

Run the script:
```bash
python photos_task.py
```

## How it works

1. **Initialization**: Sends "START" command to centrala to get initial photos
2. **Photo Analysis**: Uses OpenAI Vision to analyze each photo's quality
3. **Photo Repair**: Sends appropriate repair commands (REPAIR/BRIGHTEN/DARKEN) to automaton
4. **Iteration**: Repeats repair process up to 3 times per photo for optimal quality
5. **Description Generation**: Creates detailed Polish description of Barbara
6. **Final Submission**: Sends the description back to centrala

## Available Operations

- `REPAIR FILENAME` - Fixes noise, glitches, and artifacts
- `BRIGHTEN FILENAME` - Lightens dark photos
- `DARKEN FILENAME` - Darkens overexposed photos

## Output

The script will:
- Show progress of photo processing
- Display quality assessments and suggested operations
- Generate and display Barbara's description
- Report final submission status to centrala 