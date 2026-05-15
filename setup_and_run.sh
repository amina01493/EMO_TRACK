#!/bin/bash

# EMO_TRACK Setup & Run Script for macOS/Linux

echo "🛡️ Starting EMO_TRACK Ecosystem Setup..."

# Check for Python
if ! command -v python3 &> /dev/null
then
    echo "❌ Python3 is not installed. Please install it from python.org"
    exit
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔄 Activating environment..."
source .venv/bin/activate

# Install requirements
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run the app
echo "🚀 Launching EMO_TRACK Server..."
python3 app.py
