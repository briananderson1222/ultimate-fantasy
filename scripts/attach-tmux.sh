#!/bin/bash

# Ultimate Fantasy Platform - Tmux Attach Script
# This script attaches to the existing tmux session

# Find project root (directory containing docker-compose.yml)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT"

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
    CYAN='\033[0;36m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
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

SESSION_NAME="ultimate-fantasy"

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo -e "${RED}❌ tmux is not installed. Please install tmux first:${NC}"
    echo "   Ubuntu/Debian: sudo apt-get install tmux"
    echo "   macOS: brew install tmux"
    echo "   CentOS/RHEL: sudo yum install tmux"
    exit 1
fi

# Check if session exists
if ! tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo -e "${RED}❌ No tmux session named '$SESSION_NAME' found.${NC}"
    echo -e "${YELLOW}💡 Start a new session with: ./scripts/start-with-tmux.sh${NC}"
    exit 1
fi

echo -e "${CYAN}🔗 Attaching to tmux session '$SESSION_NAME'...${NC}"
echo -e "${YELLOW}💡 Use Ctrl+B, D to detach (keep session running)${NC}"
echo -e "${YELLOW}💡 Use Ctrl+B, 1-5 or Ctrl+B, n/p to switch between windows${NC}"
echo

# Attach to session
tmux attach-session -t $SESSION_NAME