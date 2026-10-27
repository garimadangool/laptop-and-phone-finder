#!/bin/bash
# Start both API and UI servers
cd /home/garimadangol/garima

echo "Starting API on port 8000..."
nohup python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 > /tmp/api.log 2>&1 &
echo "API PID: $!"

echo "Starting UI on port 8501..."
nohup streamlit run ui/app.py --server.port 8501 --server.headless true > /tmp/ui.log 2>&1 &
echo "UI PID: $!"

sleep 3

echo ""
echo "============================================"
echo "  LAPTOP RECOMMENDATION SYSTEM - RUNNING"
echo "============================================"
echo ""
echo "  API:  http://localhost:8000/docs"
echo "  UI:   http://localhost:8501"
echo ""
echo "  Logs:"
echo "    API: /tmp/api.log"
echo "    UI:  /tmp/ui.log"
echo "============================================"
