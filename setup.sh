#!/bin/bash

# AgenticQuant Setup Script

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║              🤖  AgenticQuant Setup  🤖                  ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "❌ Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys!"
fi

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p workspaces
mkdir -p logs

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║              ✅  Setup Complete!  ✅                     ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys (OPENAI_API_KEY or ANTHROPIC_API_KEY)"
echo "2. Activate the virtual environment: source venv/bin/activate"
echo "3. Start the server: python main.py"
echo "4. Open browser to http://localhost:8000"
echo ""
echo "Happy analyzing! 🚀"
