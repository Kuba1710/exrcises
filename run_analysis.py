import os
import subprocess
import sys

def run_command(command):
    """Run a command and print the output"""
    print(f"Running: {command}")
    process = subprocess.run(command, shell=True, capture_output=True, text=True)
    print(process.stdout)
    if process.stderr:
        print(f"Errors: {process.stderr}")
    return process.returncode

def main():
    # Ensure we have the necessary directories
    os.makedirs("transcripts", exist_ok=True)
    
    # Run the transcription script
    transcription_result = run_command("python3 transcript_audio.py")
    if transcription_result != 0:
        print("Transcription failed. Please check the errors above.")
        return
    
    # Run the analysis script
    analysis_result = run_command("python3 analyze_transcripts.py")
    if analysis_result != 0:
        print("Analysis failed. Please check the errors above.")
        return
    
    print("Analysis complete!")

if __name__ == "__main__":
    main() 