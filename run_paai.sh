#!/bin/bash

cd ~/PAAI || exit 1
source .venv/bin/activate

streamlit run app.py --server.port 8501
