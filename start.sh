#!/bin/bash

# 1. Update system & Install Python/Pip (Optional, assuming Ubuntu/Debian)
# sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv

# 2. Setup Virtual Environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# 3. Activate Virtual Environment
source venv/bin/activate

# 4. Install Dependencies
echo "Installing requirements..."
pip install -r requirements.txt

# 5. Run Bot
echo "Starting Upbit Grid Trading Bot..."
# Run with nohup to keep running after logout (Simple background run)
# nohup python3 main.py > logs/output.log 2>&1 &
# But for interactive start:
python3 main.py
