import os
import json
import requests
from pathlib import Path
import openai
from dotenv import load_dotenv

# Load API key from environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("Please ensure your OPENAI_API_KEY is set in the .env file")
    exit(1)

openai.api_key = api_key

def transcribe_audio(file_path):
    """Transcribe an audio file using OpenAI Whisper"""
    print(f"Transcribing {file_path}...")
    
    try:
        with open(file_path, "rb") as audio_file:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="pl"
            )
        return transcript.text
    except Exception as e:
        print(f"Error transcribing {file_path}: {e}")
        return None

def main():
    # Directory containing audio files
    audio_dir = Path("audio")
    output_dir = Path("transcripts")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all audio files
    audio_files = [f for f in audio_dir.glob("*.m4a")]
    
    all_transcripts = {}
    
    # Transcribe each audio file
    for audio_file in audio_files:
        transcript = transcribe_audio(audio_file)
        if transcript:
            # Save individual transcript
            output_file = output_dir / f"{audio_file.stem}.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(transcript)
            
            # Add to collection
            all_transcripts[audio_file.stem] = transcript
    
    # Save combined transcripts
    with open(output_dir / "all_transcripts.txt", "w", encoding="utf-8") as f:
        for name, transcript in all_transcripts.items():
            f.write(f"--- {name} ---\n\n")
            f.write(transcript)
            f.write("\n\n")
    
    # Save as JSON as well
    with open(output_dir / "all_transcripts.json", "w", encoding="utf-8") as f:
        json.dump(all_transcripts, f, ensure_ascii=False, indent=2)
    
    print(f"Transcripts saved to {output_dir}")

if __name__ == "__main__":
    main() 