#!/bin/bash

# Ultimate Fantasy Platform - Tmux Stop Script
# This script stops all tmux sessions and cleans up processes

# Find project root (directory containing docker-compose.yml)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT"

# Colors for output (only if terminal supports colors)
if [ -t 1 ] && [ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    CYAN=''
    NC=''
fi

SESSION_NAME="ultimate-fantasy"

echo -e "${RED}🛑 Stopping Ultimate Fantasy Platform Tmux Session${NC}"
echo "================================================="

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo -e "${RED}❌ tmux is not installed.${NC}"
    exit 1
fi

# Kill the session if it exists
if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo -e "${BLUE}🔪 Killing tmux session '$SESSION_NAME'...${NC}"
    tmux kill-session -t $SESSION_NAME
    echo -e "${GREEN}✅ Tmux session stopped${NC}"
else
    echo -e "${YELLOW}ℹ️  No tmux session '$SESSION_NAME' found${NC}"
fi

# Kill any remaining processes on our ports (cleanup)
echo -e "${BLUE}🧹 Cleaning up any remaining processes...${NC}"
pkill -f "next dev" 2>/dev/null || true
pkill -f "uvicorn.*8000" 2>/dev/null || true
pkill -f "expo.*start" 2>/dev/null || true
pkill -f "python.*http.server.*3001" 2>/dev/null || true

# Kill processes using our ports
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:19006 | xargs kill -9 2>/dev/null || true
lsof -ti:3001 | xargs kill -9 2>/dev/null || true
lsof -ti:8081 | xargs kill -9 2>/dev/null || true

# Stop Docker containers if running
if command -v docker &> /dev/null && (command -v docker-compose &> /dev/null || docker compose version &> /dev/null 2>&1); then
    echo -e "${BLUE}🐳 Stopping Docker containers...${NC}"
    docker compose -f docker-compose.dev.yml down 2>/dev/null || true
fi

echo
echo -e "${GREEN}✅ All services stopped and cleaned up!${NC}"
echo -e "${YELLOW}💡 To start again: ./scripts/start-with-tmux.sh${NC}"