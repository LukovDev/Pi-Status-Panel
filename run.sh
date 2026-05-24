#!/bin/bash

source venv/bin/activate
python3 -m uvicorn server:app --host 0.0.0.0 --port 8888 --reload
