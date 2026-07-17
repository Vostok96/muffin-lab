#!/bin/bash
# MUFFIN Frontend start script
cd "$(dirname "$0")"
echo "=== MUFFIN Frontend ==="
echo "API:  http://127.0.0.1:8000/api/v1"
echo "Web:  http://127.0.0.1:8877/MUFFIN/"
echo "Login: http://127.0.0.1:8877/MUFFIN/Login/Index"
echo ""
python3 -u server.py
