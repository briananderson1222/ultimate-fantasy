#!/bin/bash

# Ultimate Fantasy Platform - Dynamic Status Script
# This script provides real-time status of all platform components

set -e

# Parse arguments
SHOW_TMUX_COMMANDS=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --tmux)
            SHOW_TMUX_COMMANDS=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

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

# Find project root (directory containing docker-compose.yml)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Check if we're in the right directory
if [ ! -f "$PROJECT_ROOT/docker-compose.yml" ]; then
    color_echo "$RED" "❌ Cannot find project root directory"
    exit 1
fi

# Change to project root
cd "$PROJECT_ROOT"

# Header
color_echo "$CYAN" "🎉 Ultimate Fantasy Platform - Live Status"
echo "=========================================="
color_echo "$BLUE" "📊 System Status: $(date)"
echo ""

# Check services
color_echo "$YELLOW" "🔍 Service Status:"

# Backend status
if curl -s http://localhost:8000/health 2>/dev/null >/dev/null; then
    color_echo "$GREEN" "   ✅ Backend (port 8000) - Running"
else
    color_echo "$RED" "   ❌ Backend (port 8000) - Down"
fi

# Frontend status
if curl -s http://localhost:3000 2>/dev/null >/dev/null; then
    color_echo "$GREEN" "   ✅ Frontend (port 3000) - Running"
else
    color_echo "$RED" "   ❌ Frontend (port 3000) - Down"
fi

# Database status
if command -v docker &> /dev/null && (command -v docker-compose &> /dev/null || docker compose version &> /dev/null 2>&1); then
    if docker compose ps | grep -q "Up"; then
        color_echo "$GREEN" "   ✅ PostgreSQL (Docker) - Running"
    else
        color_echo "$RED" "   ❌ PostgreSQL (Docker) - Down"
    fi
else
    color_echo "$YELLOW" "   ⚠️  PostgreSQL (Docker) - Not available (using SQLite)"
fi

# Mobile status
if curl -s http://localhost:19006 2>/dev/null >/dev/null || curl -s http://localhost:8081 2>/dev/null >/dev/null; then
    color_echo "$GREEN" "   ✅ Mobile Dev Server - Running"
else
    color_echo "$YELLOW" "   ⚠️  Mobile Dev Server - Not started"
fi

# Landing page status
if curl -s http://localhost:3001 2>/dev/null >/dev/null; then
    color_echo "$GREEN" "   ✅ Landing Page (port 3001) - Running"
else
    color_echo "$YELLOW" "   ⚠️  Landing Page - Not started"
fi

echo ""

# Database connection info
color_echo "$PURPLE" "🗄️ Database Configuration:"
if [ -n "$DATABASE_URL" ]; then
    if [[ "$DATABASE_URL" == postgresql* ]]; then
        color_echo "$BLUE" "   📊 Using: PostgreSQL"
    else
        color_echo "$BLUE" "   📊 Using: SQLite"
    fi
    color_echo "$BLUE" "   🔗 URL: $DATABASE_URL"
else
    color_echo "$YELLOW" "   ⚠️  DATABASE_URL not set"
fi

echo ""

# Recent activity/logs
color_echo "$CYAN" "📋 Recent Activity:"
if [ -f "/tmp/ultimate-fantasy.log" ]; then
    tail -5 /tmp/ultimate-fantasy.log 2>/dev/null || echo "   No recent logs"
else
    echo "   No log file found"
fi

echo ""

# System info
color_echo "$GREEN" "💻 System Info:"
echo "   📁 Directory: $(pwd)"
echo "   🐳 Docker: $(command -v docker >/dev/null 2>&1 && echo 'Available' || echo 'Not available')"
echo "   🐍 Python: $(python3 --version 2>/dev/null || echo 'Not available')"
echo "   📦 Node.js: $(node --version 2>/dev/null || echo 'Not available')"

echo ""

# Quick actions
color_echo "$YELLOW" "🚀 Quick Actions:"
echo "   📱 Attach to tmux: ./scripts/attach-tmux.sh"
echo "   🛑 Stop all: ./scripts/stop-tmux.sh"
echo "   🔍 View logs: docker compose logs -f (if using Docker)"
echo "   📊 API Docs: http://localhost:8000/docs"
echo "   🌐 Frontend: http://localhost:3000"

 echo ""

# Tmux navigation commands (only when --tmux flag is used)
if [ "$SHOW_TMUX_COMMANDS" = "true" ]; then
    color_echo "$CYAN" "🖥️ Tmux Navigation:"
    echo "   Ctrl+B, 1-6: Switch to window by number"
    echo "   Ctrl+B, n:   Next window"
    echo "   Ctrl+B, p:   Previous window"
    echo "   Ctrl+B, d:   Detach from session"
    echo "   Ctrl+B, c:   Create new window"
    echo "   Ctrl+B, [:   Enter copy mode"
    echo "   Ctrl+B, \$:   Rename current window"
    echo ""
fi

 color_echo "$GREEN" "✅ Status check complete!"