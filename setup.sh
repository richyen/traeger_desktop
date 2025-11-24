#!/bin/bash
# Quick setup script for the Traeger Grill Controller

echo "=================================="
echo "Traeger Grill Controller Setup"
echo "=================================="
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Make sure you have traeger_mitmproxy.flows in this directory"
echo "2. Run: python extract_token.py"
echo "3. Then use: python traeger_cli.py --help"
echo ""
echo "To activate the environment in the future:"
echo "  source venv/bin/activate"
echo ""
