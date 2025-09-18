#!/bin/bash

# Frontend für lokale Entwicklung mit echtem Backend
echo "🎨 Starte Frontend (Lokale Entwicklung)"
echo "🔗 Backend: http://localhost:8000"
echo "🌐 Frontend: http://localhost:3000"
echo ""

cd frontend

# Check if backend is running
if ! curl -s http://localhost:8000/api/teams > /dev/null 2>&1; then
    echo "⚠️  Backend nicht erreichbar!"
    echo "💡 Starte zuerst das Backend:"
    echo "   ./start_local_real.sh"
    echo ""
    echo "❓ Trotzdem fortfahren? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Set environment for local development
export VITE_API_URL=http://localhost:8000
echo "🔧 API URL: $VITE_API_URL"

# Start frontend
npm run dev
