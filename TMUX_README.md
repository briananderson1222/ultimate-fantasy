# Ultimate Fantasy Platform - Tmux Development Setup

This guide explains how to use the tmux-based development environment for the Ultimate Fantasy platform.

## Overview

The tmux setup provides a convenient way to manage all application components in separate terminal windows within a single tmux session. This allows you to:

- Monitor all services simultaneously
- Switch between different components easily
- Keep all processes running in the background
- Maintain separate logs for each service
- Detach and reattach to your development session

## Quick Start

### 1. Start All Services

```bash
./scripts/start-with-tmux.sh
```

This will create a new tmux session called `ultimate-fantasy` with separate windows for each component:

- **Window 1 (main)**: Live status dashboard (auto-refreshing)
- **Window 2 (database)**: Database monitoring & management
- **Window 3 (backend)**: FastAPI backend (port 8000)
- **Window 4 (frontend)**: Next.js frontend (port 3000)
- **Window 5 (mobile)**: Expo mobile app (port 19006)
- **Window 6 (landing)**: Static landing page (port 3001)

### 2. Attach to Existing Session

```bash
./scripts/attach-tmux.sh
```

### 3. Stop All Services

```bash
./scripts/stop-tmux.sh
```

## Tmux Commands

### Basic Navigation

- **Ctrl+B, 1-6**: Switch between windows (1=main, 2=database, 3=backend, 4=frontend, 5=mobile, 6=landing)
- **Ctrl+B, D**: Detach from session (processes keep running)
- **Ctrl+B, C**: Create new window
- **Ctrl+B, N/P**: Next/previous window
- **Ctrl+B, W**: Show window list

### Pane Management

- **Ctrl+B, |**: Split window horizontally
- **Ctrl+B, -**: Split window vertically
- **Ctrl+B, H/J/K/L**: Navigate between panes
- **Ctrl+B, X**: Close current pane

### Copy Mode

- **Ctrl+B, [**: Enter copy mode
- **V**: Start visual selection
- **Y**: Copy selection
- **Q**: Exit copy mode

## Window Layout

### Window 1: Main (Live Status Dashboard)

Shows real-time status of all services with auto-refresh every 10 seconds:

- **Service Health**: ✅ Running / ❌ Down status for all components
- **Database Status**: PostgreSQL/SQLite connection status
- **System Info**: Directory, Docker availability, Python/Node versions
- **Quick Actions**: Links to attach, stop, view logs, and access services
- **Recent Activity**: Latest log entries from all services
- **Tmux Navigation**: Shows tmux commands for window navigation and session management

### Window 2: Database (Monitoring & Management)

Dedicated database operations and monitoring:

- **Database Setup**: PostgreSQL with Docker or SQLite fallback
- **Migration Commands**: Run database migrations and updates
- **Connection Testing**: Test database connectivity
- **Log Monitoring**: View PostgreSQL logs (when using Docker)
- **Database Shell**: Access database for debugging and queries
- **SQLite Management**: File operations, backups, and direct SQLite access (when using SQLite)
- **Database Backups**: Create and manage database backups
- **Schema Inspection**: View database schema and table information

### Window 3: Backend

Runs the FastAPI backend with auto-reload:

```bash
cd apps/api
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Window 4: Frontend

Runs the Next.js development server:

```bash
cd apps/web
npm run dev -- --port 3000
```

### Window 5: Mobile

Runs the Expo development server:

```bash
cd apps/mobile
npm start
```

### Window 6: Landing

Serves the static landing page:

```bash
cd apps/landing
python3 -m http.server 3001
```

## Advanced Usage

### Custom Tmux Configuration

For a better tmux experience, copy the provided `.tmux.conf` to your home directory:

```bash
cp .tmux.conf ~/.tmux.conf
```

This configuration provides:

- **Ctrl+A** as prefix (instead of Ctrl+B)
- Mouse support
- Better colors and status bar
- Vim-style copy mode
- Improved key bindings

### Multiple Development Sessions

You can run multiple development sessions by specifying different session names:

```bash
# Start with custom session name
SESSION_NAME=my-dev-session ./scripts/start-with-tmux.sh

# Attach to custom session
SESSION_NAME=my-dev-session ./scripts/attach-tmux.sh
```

### Monitoring Logs

Each window shows the logs for its respective service. You can:

1. Switch to the window you want to monitor
2. Scroll up to see previous logs
3. Use copy mode (Ctrl+B, [) to search through logs

### Development Workflow

1. **Start**: `./scripts/start-with-tmux.sh`
2. **Monitor Status**: Window 1 shows live status of all services (auto-refreshing) with tmux navigation commands
3. **Check Database**: Window 2 shows database setup progress and provides management tools
4. **Develop**: Make changes in your editor
5. **Monitor Services**: Switch between windows 3-6 to see individual service logs
6. **Test**: Access services via browser/mobile
7. **Debug**: Use Window 2 for database operations and troubleshooting
8. **Stop**: `./scripts/stop-tmux.sh` when done

**💡 Tip**: The status dashboard in Window 1 shows tmux navigation commands to help you move between windows efficiently.

### Key Features of New Layout

- **Window 1**: Real-time dashboard showing health of all services with tmux navigation commands
- **Window 2**: Dedicated database monitoring and management
- **Auto-refresh**: Status updates every 10 seconds without manual intervention
- **Better Organization**: Clear separation between status, database, and services
- **Contextual Help**: Status dashboard shows relevant tmux commands when running in tmux

### SQLite Database Management

When Docker/PostgreSQL is not available, the system automatically falls back to SQLite. The database window provides comprehensive SQLite management tools:

#### SQLite File Location

- **Database file**: `ultimate_fantasy.db` (created in project root)
- **File permissions**: 644 (readable by all, writable by owner)
- **Backup location**: Same directory as main database file

#### Common SQLite Operations in Database Window

1. **Check database file**:

   ```bash
   ls -la ultimate_fantasy.db
   ```

2. **View database size**:

   ```bash
   du -h ultimate_fantasy.db
   ```

3. **Create backup**:

   ```bash
   cp ultimate_fantasy.db backup_$(date +%s).db
   ```

4. **Access SQLite shell**:

   ```bash
   sqlite3 ultimate_fantasy.db
   ```

5. **View all tables**:

   ```bash
   sqlite3 ultimate_fantasy.db '.tables'
   ```

6. **View schema**:
   ```bash
   sqlite3 ultimate_fantasy.db '.schema'
   ```

#### SQLite vs PostgreSQL

| Feature         | SQLite                    | PostgreSQL            |
| --------------- | ------------------------- | --------------------- |
| **Setup**       | File-based, no server     | Docker container      |
| **Performance** | Good for development      | Better for production |
| **Features**    | Limited advanced features | Full SQL feature set  |
| **Concurrency** | File locking              | Multi-user support    |
| **Size limit**  | ~140TB                    | Unlimited             |
| **Backup**      | Copy file                 | pg_dump commands      |

#### When to Use Each

- **Use SQLite**: Development, testing, single-user scenarios, when Docker unavailable
- **Use PostgreSQL**: Production, multi-user, complex queries, when Docker available

## Troubleshooting

### Tmux Not Installed

```bash
# Ubuntu/Debian
sudo apt-get install tmux

# macOS
brew install tmux

# CentOS/RHEL
sudo yum install tmux
```

### Session Already Exists

If you get an error about the session already existing:

```bash
# Kill existing session
./scripts/stop-tmux.sh

# Or manually kill it
tmux kill-session -t ultimate-fantasy
```

### Port Conflicts

If ports are already in use:

```bash
# Check what's using the ports
lsof -i :3000
lsof -i :8000
lsof -i :19006
lsof -i :3001

# Kill conflicting processes
kill -9 <PID>
```

### Docker Issues

If PostgreSQL doesn't start properly:

```bash
# Check Docker status
docker ps -a

# Clean up containers
docker system prune

# Restart Docker service
sudo systemctl restart docker
```

## Benefits of Tmux for Development

### Why Use Tmux?

1. **Unified Environment**: All services in one terminal session
2. **Persistent Sessions**: Detach and reattach without stopping services
3. **Resource Efficient**: Lower memory usage than multiple terminal windows
4. **Live Status Dashboard**: Real-time monitoring of all service health
5. **Dedicated Database Window**: Specialized database monitoring and management
6. **Better Organization**: Clear separation between status, database, and services
7. **Auto-Refreshing Status**: Continuous updates without manual intervention
8. **Team Development**: Consistent development environment

### Common Use Cases

- **Full-Stack Development**: Monitor frontend, backend, and database logs
- **Microservices**: Manage multiple services in separate windows
- **Database Operations**: Dedicated window for database migrations and monitoring
- **Real-time Monitoring**: Live dashboard showing health of all components
- **Testing**: Keep test runners and application logs visible
- **Debugging**: Switch between different service logs quickly
- **Demo/Showcase**: Present all running services in one session

## Comparison with Other Tools

| Tool                 | Pros                                     | Cons                              |
| -------------------- | ---------------------------------------- | --------------------------------- |
| **tmux**             | Lightweight, persistent, keyboard-driven | Learning curve, terminal-only     |
| **Terminal tabs**    | Simple, visual                           | Resource heavy, not persistent    |
| **Docker Compose**   | Service orchestration                    | Less interactive, harder to debug |
| **Process managers** | Background processes                     | Less visibility into logs         |

## Tips and Best Practices

1. **Use descriptive window names** for easy identification
2. **Monitor Window 1** for real-time status of all services
3. **Use Window 2** for database operations and monitoring
4. **Keep Windows 3-6** for individual service logs and development
5. **Use copy mode** to search through logs efficiently
6. **Detach frequently** to avoid losing work if connection drops
7. **Monitor resource usage** - tmux is lightweight but check system resources
8. **Use sessions for different projects** to keep environments separate
9. **Check Window 1 status** before starting development work
10. **Use Window 2** for database migrations and troubleshooting

## Getting Help

- **tmux man page**: `man tmux`
- **Tmux cheat sheet**: Search for "tmux cheat sheet" online
- **Project scripts**: All scripts include help and error messages
- **This documentation**: Keep this file handy for reference

---

**Happy coding with tmux! 🚀**
