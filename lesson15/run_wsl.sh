#!/bin/bash

# Script to run connections_task.py in WSL environment
# This script ensures we're using the correct Python environment

echo "🚀 Running Connections Task in WSL..."
echo "Working directory: $(pwd)"

# Change to the script directory
cd /mnt/c/Users/jakub/Desktop/AI_devs/exrcises/lesson15

# Check if required packages are available
echo "📦 Checking dependencies..."
python3 -c "import neo4j, requests, openai; print('✅ All dependencies available')" || {
    echo "❌ Missing dependencies. Installing..."
    pip install --break-system-packages neo4j requests python-dotenv openai
}

# Run the main script
echo "🔄 Starting connections task..."
python3 connections_task.py

echo "✅ Script execution completed!" 