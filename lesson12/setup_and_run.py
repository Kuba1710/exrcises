#!/usr/bin/env python3
"""
Setup and run script for the vector search task.
This script helps with setting up Qdrant and running the main task.
"""

import subprocess
import sys
import time
import requests
from pathlib import Path

def check_docker():
    """Check if Docker is installed and running"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Docker is installed")
            return True
        else:
            print("✗ Docker is not installed")
            return False
    except FileNotFoundError:
        print("✗ Docker is not installed")
        return False

def start_qdrant():
    """Start Qdrant using Docker"""
    print("Starting Qdrant...")
    
    # Check if Qdrant container is already running
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        if 'qdrant/qdrant' in result.stdout:
            print("✓ Qdrant is already running")
            return True
    except:
        pass
    
    # Start Qdrant container
    try:
        subprocess.run([
            'docker', 'run', '-d', 
            '--name', 'qdrant-lesson12',
            '-p', '6333:6333',
            'qdrant/qdrant'
        ], check=True)
        
        print("Qdrant container started. Waiting for it to be ready...")
        
        # Wait for Qdrant to be ready
        for i in range(30):  # Wait up to 30 seconds
            try:
                response = requests.get('http://localhost:6333/collections')
                if response.status_code == 200:
                    print("✓ Qdrant is ready!")
                    return True
            except:
                pass
            time.sleep(1)
            print(f"Waiting... ({i+1}/30)")
        
        print("✗ Qdrant failed to start within 30 seconds")
        return False
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to start Qdrant: {e}")
        return False

def check_env_file():
    """Check if .env file exists and has required keys"""
    env_path = Path('../.env')
    if not env_path.exists():
        print("✗ .env file not found")
        print("Please create a .env file in the exercises directory with:")
        print("OPENAI_API_KEY=your_openai_api_key")
        print("CENTRALA_API_KEY=your_centrala_api_key")
        return False
    
    with open(env_path, 'r') as f:
        content = f.read()
    
    if 'OPENAI_API_KEY=' not in content or 'CENTRALA_API_KEY=' not in content:
        print("✗ .env file missing required API keys")
        print("Please add to .env file:")
        print("OPENAI_API_KEY=your_openai_api_key")
        print("CENTRALA_API_KEY=your_centrala_api_key")
        return False
    
    print("✓ .env file found with API keys")
    return True

def run_main_task():
    """Run the main vector search task"""
    print("\nRunning the vector search task...")
    try:
        subprocess.run([sys.executable, 'vector_search.py'], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Task failed: {e}")
        return False

def cleanup():
    """Stop and remove Qdrant container"""
    print("\nCleaning up...")
    try:
        subprocess.run(['docker', 'stop', 'qdrant-lesson12'], capture_output=True)
        subprocess.run(['docker', 'rm', 'qdrant-lesson12'], capture_output=True)
        print("✓ Qdrant container cleaned up")
    except:
        pass

def main():
    """Main setup and run function"""
    print("Vector Search Task Setup")
    print("=" * 40)
    
    # Check prerequisites
    if not check_docker():
        print("\nPlease install Docker first:")
        print("https://docs.docker.com/get-docker/")
        return
    
    if not check_env_file():
        return
    
    # Start Qdrant
    if not start_qdrant():
        return
    
    try:
        # Run the main task
        success = run_main_task()
        
        if success:
            print("\n" + "=" * 40)
            print("✓ Task completed successfully!")
        else:
            print("\n" + "=" * 40)
            print("✗ Task failed")
            
    except KeyboardInterrupt:
        print("\nTask interrupted by user")
    
    # Ask if user wants to keep Qdrant running
    try:
        keep_running = input("\nKeep Qdrant running? (y/N): ").lower().strip()
        if keep_running != 'y':
            cleanup()
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main() 