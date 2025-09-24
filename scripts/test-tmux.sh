#!/bin/bash

# Ultimate Fantasy Platform - Tmux Test Script
# This script tests if tmux is available and can create sessions

# Find project root (directory containing docker-compose.yml)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT"

echo "🧪 Testing Tmux Setup"
echo "===================="

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo "❌ tmux is not installed"
    echo ""
    echo "To install tmux:"
    echo "  Ubuntu/Debian: sudo apt-get install tmux"
    echo "  macOS: brew install tmux"
    echo "  CentOS/RHEL: sudo yum install tmux"
    exit 1
fi

echo "✅ tmux is installed: $(tmux -V)"

# Check tmux version
TMUX_VERSION=$(tmux -V | cut -d' ' -f2)
echo "✅ tmux version: $TMUX_VERSION"

# Test creating a session
SESSION_NAME="test-ultimate-fantasy"
echo ""
echo "🧪 Testing session creation..."

if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo "ℹ️  Session '$SESSION_NAME' already exists, killing it..."
    tmux kill-session -t $SESSION_NAME
fi

# Create test session
tmux new-session -d -s $SESSION_NAME -n "test-window"
tmux send-keys -t $SESSION_NAME:test-window "echo 'Hello from tmux test!'" C-m
tmux send-keys -t $SESSION_NAME:test-window "sleep 2" C-m

echo "✅ Test session created successfully"

# List sessions
echo ""
echo "📋 Current tmux sessions:"
tmux list-sessions

# Clean up test session
echo ""
echo "🧹 Cleaning up test session..."
tmux kill-session -t $SESSION_NAME
echo "✅ Test session cleaned up"

echo ""
echo "🎉 Tmux setup test completed successfully!"
echo "💡 You can now use the tmux scripts:"
echo "   ./scripts/start-with-tmux.sh  - Start all services"
echo "   ./scripts/attach-tmux.sh      - Attach to session"
echo "   ./scripts/stop-tmux.sh        - Stop all services"