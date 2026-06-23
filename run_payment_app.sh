#!/bin/bash

cd ~/PAAI || exit 1

echo "Starting PAAI Payment Reminder Agent..."
source .venv/bin/activate

echo "Virtual environment activated."
echo "Running Payment app on http://localhost:8502"

streamlit run payment_app.py --server.port 8502
