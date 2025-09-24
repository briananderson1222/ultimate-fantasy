#!/bin/bash

# Ultimate Fantasy Platform - Tmux Development Environment
# Consolidated script that creates a tmux session with all application components
#
# Usage:
#   ./scripts/start-with-tmux.sh     - Create tmux session with all windows ready
#   ./scripts/attach-tmux.sh         - Attach to existing session
#   ./scripts/stop-tmux.sh           - Stop session and clean up
#
# After running this script:
#   1. Run: ./scripts/attach-tmux.sh
#   2. Switch to each window (Ctrl+B, 2-5)
#   3. Run the startup command shown in each window
#   4. Watch logs as services start

set -e

# Find project root (directory containing docker-compose.yml)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Check if we're in the right directory
if [ ! -f "$PROJECT_ROOT/docker-compose.yml" ]; then
    echo "❌ Cannot find project root directory"
    exit 1
fi

# Change to project root
cd "$PROJECT_ROOT"

SESSION_NAME="ultimate-fantasy"

# Color support detection
SUPPORTS_COLOR=0
if [ -t 1 ] && [ -z "$NO_COLOR" ]; then
    if command -v tput >/dev/null 2>&1; then
        if [ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]; then
            SUPPORTS_COLOR=1
        fi
    fi
fi

# Color codes (only if supported)
if [ "$SUPPORTS_COLOR" = "1" ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    PURPLE='\033[0;35m'
    CYAN='\033[0;36m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    PURPLE=''
    CYAN=''
    NC=''
fi

# Function for colored output
color_echo() {
    local color="$1"
    local message="$2"
    if [ "$SUPPORTS_COLOR" = "1" ]; then
        echo -e "${color}${message}${NC}"
    else
        echo "$message"
    fi
}

color_echo "$CYAN" "🚀 Ultimate Fantasy Platform - Tmux Development Environment"
echo "============================================================"

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    color_echo "$RED" "❌ tmux is not installed. Please install tmux first:"
    echo "   Ubuntu/Debian: sudo apt-get install tmux"
    echo "   macOS: brew install tmux"
    echo "   CentOS/RHEL: sudo yum install tmux"
    exit 1
fi

color_echo "$GREEN" "✅ tmux is installed: $(tmux -V)"

# Kill existing session if it exists
if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    color_echo "$YELLOW" "ℹ️  Killing existing session '$SESSION_NAME'..."
    tmux kill-session -t $SESSION_NAME 2>/dev/null || true
fi

# Create new session
color_echo "$BLUE" "📱 Creating tmux session '$SESSION_NAME'..."
tmux new-session -d -s $SESSION_NAME -n "main"

# Setup main window with status script
color_echo "$BLUE" "📊 Setting up main status window..."
 tmux send-keys -t $SESSION_NAME:main "cd $PROJECT_ROOT" Enter
 tmux send-keys -t $SESSION_NAME:main "echo '
📊 Main Status Window

🔍 This window shows real-time status of all services
📈 Auto-refreshes every 10 seconds
🖥️ Use tmux navigation commands to switch between windows

🚀 To start monitoring:
   1. This window will auto-refresh status
   2. Switch to other windows (Ctrl+B, 2-6) to start services
   3. Return here to monitor overall health
  '" C-m
  tmux send-keys -t $SESSION_NAME:main "watch -n 10 './scripts/status.sh --tmux'" C-m

# Database window (Window #2)
color_echo "$BLUE" "🗄️ Creating database window..."
tmux new-window -t $SESSION_NAME -n "database"
sleep 1
tmux send-keys -t $SESSION_NAME:database "cd $PROJECT_ROOT" C-m
tmux send-keys -t $SESSION_NAME:database "echo '
🗄️ Database Management Window

📊 Database Operations:
   PostgreSQL (Docker):
   - Monitor logs: docker compose logs -f db
   - Check status: docker compose ps
   - Restart DB: docker compose restart db
   - Database shell: docker exec -it ultimate-fantasy-db psql -U postgres

   SQLite (Fallback):
   - Database file: ultimate_fantasy.db (in project root)
   - Run migrations: cd apps/api && uv run alembic upgrade head
   - Database shell: uv run python -c \"from src.database import engine; ...\"
   - Check file: ls -la ultimate_fantasy.db

   Universal Commands:
   - Test connection: uv run python -c \"from src.database import engine; print('✅ Connected')\"
   - Run migrations: cd apps/api && uv run alembic upgrade head
   - View schema: uv run python -c \"from src.models import *; print('Schema loaded')\"
   - Database info: uv run python -c \"from src.database import engine; print(f'Engine: {engine.url}')\"
   - Create backup: cp ultimate_fantasy.db ultimate_fantasy_$(date +%Y%m%d_%H%M%S).db

   Quick SQLite Commands (when using SQLite):
   - Check DB file: ls -la ultimate_fantasy.db
   - DB file size: du -h ultimate_fantasy.db
   - Backup DB: cp ultimate_fantasy.db backup_$(date +%s).db
   - SQLite shell: sqlite3 ultimate_fantasy.db
   - Show tables: sqlite3 ultimate_fantasy.db '.tables'
   - Schema info: sqlite3 ultimate_fantasy.db '.schema'
'" C-m

 # Setup database in database window
 color_echo "$BLUE" "🐳 Setting up database..."
 if command -v docker &> /dev/null && (command -v docker-compose &> /dev/null || docker compose version &> /dev/null 2>&1); then
     color_echo "$GREEN" "📦 Starting PostgreSQL with Docker..."
      tmux send-keys -t $SESSION_NAME:database "docker compose -f docker-compose.dev.yml up -d --remove-orphans" C-m
      tmux send-keys -t $SESSION_NAME:database "echo '⏳ Waiting for database to be ready...'" C-m
      tmux send-keys -t $SESSION_NAME:database "sleep 5" C-m
     export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/ultimate_fantasy"

      # Test PostgreSQL connection and fallback to SQLite if needed
      color_echo "$BLUE" "🔍 Testing PostgreSQL connection..."
      tmux send-keys -t $SESSION_NAME:database "echo 'Testing PostgreSQL connection...'" C-m
      tmux send-keys -t $SESSION_NAME:database "if ! uv run python -c \"import os; from sqlalchemy import create_engine, text; database_url = os.getenv('DATABASE_URL'); engine = create_engine(database_url, future=True); conn = engine.connect(); conn.execute(text('SELECT 1')); print('✅ PostgreSQL connection successful')\" 2>/dev/null; then" C-m
      tmux send-keys -t $SESSION_NAME:database "  echo '🔄 Switching to SQLite fallback...'" C-m
      tmux send-keys -t $SESSION_NAME:database "  export DATABASE_URL=\"sqlite+pysqlite:///ultimate_fantasy.db\"" C-m
      tmux send-keys -t $SESSION_NAME:database "  echo '✅ Using SQLite database'" C-m
      tmux send-keys -t $SESSION_NAME:database "else" C-m
      tmux send-keys -t $SESSION_NAME:database "  echo '✅ Using PostgreSQL database'" C-m
      tmux send-keys -t $SESSION_NAME:database "fi" C-m
  else
      color_echo "$YELLOW" "⚠️  Docker not available. Using SQLite fallback."
      export DATABASE_URL="sqlite+pysqlite:///ultimate_fantasy.db"
      tmux send-keys -t $SESSION_NAME:database "export DATABASE_URL=\"sqlite+pysqlite:///ultimate_fantasy.db\"" C-m
      tmux send-keys -t $SESSION_NAME:database "echo '✅ Using SQLite database (see SQLite commands in database window)'" C-m
 fi

# Backend window (Window #3)
color_echo "$BLUE" "🔧 Creating backend window..."
tmux new-window -t $SESSION_NAME -n "backend"
sleep 1
tmux send-keys -t $SESSION_NAME:backend "cd $PROJECT_ROOT/apps/api" C-m
tmux send-keys -t $SESSION_NAME:backend "export DATABASE_URL=\"${DATABASE_URL:-sqlite+pysqlite:///ultimate_fantasy.db}\"" C-m
tmux send-keys -t $SESSION_NAME:backend "echo '
🔧 Backend Window Ready

📡 Starting FastAPI backend...
⚡ Port: 8000
📁 Directory: apps/api
📊 Database: Using environment DATABASE_URL
'" C-m
tmux send-keys -t $SESSION_NAME:backend "if [ ! -d '.venv' ]; then echo '📦 Installing backend dependencies...'; uv sync --all-extras; fi" C-m
tmux send-keys -t $SESSION_NAME:backend "uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000" C-m

# Frontend window (Window #4)
color_echo "$BLUE" "🎨 Creating frontend window..."
tmux new-window -t $SESSION_NAME -n "frontend"
sleep 1
tmux send-keys -t $SESSION_NAME:frontend "cd $PROJECT_ROOT/apps/web" C-m
tmux send-keys -t $SESSION_NAME:frontend "export NEXT_PUBLIC_API_BASE_URL='http://localhost:8000'" C-m
tmux send-keys -t $SESSION_NAME:frontend "echo '
🎨 Frontend Window Ready

🚀 Starting Next.js frontend...
⚡ Port: 3000
📁 Directory: apps/web
🔗 API URL: http://localhost:8000
'" C-m

tmux send-keys -t $SESSION_NAME:frontend "npm run dev -- --port 3000" C-m

# Mobile window (Window #5)
color_echo "$BLUE" "📱 Creating mobile window..."
tmux new-window -t $SESSION_NAME -n "mobile"
sleep 1
tmux send-keys -t $SESSION_NAME:mobile "cd $PROJECT_ROOT/apps/mobile" C-m
tmux send-keys -t $SESSION_NAME:mobile "echo '
📱 Mobile Window Ready

📱 Starting Expo mobile app...
⚡ Framework: React Native/Expo
📁 Directory: apps/mobile
🔗 Metro bundler: http://localhost:19006
🔗 Dev server: http://localhost:8081 (if different)
'" C-m
tmux send-keys -t $SESSION_NAME:mobile "npm start" C-m

# Landing page window (Window #6)
color_echo "$BLUE" "🌐 Creating landing page window..."
tmux new-window -t $SESSION_NAME -n "landing"
sleep 1
tmux send-keys -t $SESSION_NAME:landing "cd $PROJECT_ROOT/apps/landing" C-m
tmux send-keys -t $SESSION_NAME:landing "echo '
🌐 Landing Page Window Ready

🌐 Starting landing page server...
⚡ Port: 3001
📁 Directory: apps/landing
📄 Serving static files
'" C-m
tmux send-keys -t $SESSION_NAME:landing "python3 -m http.server 3001" C-m

# Setup main window with instructions
 tmux select-window -t $SESSION_NAME:main
 tmux send-keys -t $SESSION_NAME:main "echo '
🎉 Ultimate Fantasy Platform - Tmux Session Ready!
==================================================

📋 Available Windows:
   1. main     - Live status dashboard (auto-refreshing)
   2. database - Database monitoring & management
   3. backend  - FastAPI backend (port 8000)
   4. frontend - Next.js frontend (port 3000)
   5. mobile   - Expo mobile app
   6. landing  - Static landing page (port 3001)

 🚀 Services starting automatically:
    1. Window 1: Status updates automatically every 10 seconds
    2. Window 2: Database setup and monitoring (check here first)
    3. Windows 3-6: Services start automatically after brief delays
    4. Switch to windows to monitor startup progress and logs

💡 Tmux Commands:
   Ctrl+B, 1-6: Switch to window by number
   Ctrl+B, n:   Next window
   Ctrl+B, p:   Previous window
   Ctrl+B, c:   Create new window
   Ctrl+B, d:   Detach from session
   Ctrl+B, [:   Enter copy mode
   Ctrl+B, \$:   Rename current window

📱 To attach later: ./scripts/attach-tmux.sh
🛑 To stop all: ./scripts/stop-tmux.sh

 ✅ Ready! Database window (2) will show setup progress.
 '" C-m

# Show summary
echo
color_echo "$GREEN" "✅ Tmux session '$SESSION_NAME' created successfully!"
echo
color_echo "$CYAN" "🎯 Next steps:"
if [ "$SUPPORTS_COLOR" = "1" ]; then
    echo -e "   1. Attach to session: ${YELLOW}./scripts/attach-tmux.sh${NC}"
    echo -e "   2. Window 1: Status updates automatically every 10 seconds"
    echo -e "   3. Window 2: Check database setup progress"
     echo -e "   4. Windows 3-6: Services start automatically - switch to monitor progress"
 else
     echo "   1. Attach to session: ./scripts/attach-tmux.sh"
     echo "   2. Window 1: Status updates automatically every 10 seconds"
     echo "   3. Window 2: Check database setup progress"
     echo "   4. Windows 3-6: Services start automatically - switch to monitor progress"
fi
echo "   5. Watch the logs as services start"
echo
color_echo "$PURPLE" "📊 Services will be available at:"
echo "   Frontend:     http://localhost:3000"
echo "   Backend:      http://localhost:8000"
echo "   API Docs:     http://localhost:8000/docs"
echo "   Landing Page: http://localhost:3001"
echo "   Mobile:       Use Expo Go app to scan QR code"
echo
color_echo "$YELLOW" "💡 Tip: Use Ctrl+B, D to detach and keep services running"