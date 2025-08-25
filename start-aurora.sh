#!/bin/bash

echo "🚀 Starting Aurora Life OS..."

# Kill existing processes
echo "Stopping existing servers..."
pkill -f "uvicorn.*aurora" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
sleep 2

# Start backend
echo "Starting backend server..."
cd "/Users/royantony/auroyra life os/backend"
python3 start_server.py &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"

# Wait for backend to start
sleep 3

# Start frontend
echo "Starting frontend server..."
cd "/Users/royantony/auroyra life os/frontend"
npm run dev &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"

# Wait for frontend to start
sleep 5

echo ""
echo "✅ Aurora Life OS is starting up!"
echo ""
echo "📱 Frontend (React App): http://localhost:5173 (or next available port)"
echo "🔧 Backend API: http://localhost:8001"
echo "📊 API Docs: http://localhost:8001/docs"
echo ""
echo "🔍 Check status:"
echo "   Frontend: curl -I http://localhost:5173"
echo "   Backend:  curl -s http://localhost:8001/health"
echo ""
echo "💾 Database backups available in: backend/backups/"
echo "   Latest backup: current_state_$(date +%Y%m%d)_*.json"
echo "   Restore with: cd backend && python3 backup_database.py restore <filename>"
echo ""
echo "🛑 To stop servers:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Opening Aurora Life OS in your browser..."
sleep 3
open http://localhost:5173

# Keep script running
echo "Press Ctrl+C to stop all servers"
wait