#!/bin/bash

cd ~/PAAI || exit 1
source .venv/bin/activate

echo "Starting PAAI on http://localhost:8501"
streamlit run app.py --server.port 8501
