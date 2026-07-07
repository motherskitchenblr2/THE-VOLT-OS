#!/bin/bash
# VOLT OS — Local Preview Script
# Starts both backend and frontend for local development

echo "⚡ VOLT OS — Starting Local Preview"
echo "=================================="

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    echo "🐳 Starting infrastructure (PostgreSQL + Redis)..."
    docker-compose up -d postgres redis
    sleep 3
fi

echo "🐍 Starting backend on http://localhost:8000"
cd backend
pip install -r requirements.txt -q 2>/dev/null
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

echo "⚛️  Starting frontend on http://localhost:3000"
cd frontend
npm install --silent 2>/dev/null
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ VOLT OS is running!"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Stopping...'" EXIT
wait
