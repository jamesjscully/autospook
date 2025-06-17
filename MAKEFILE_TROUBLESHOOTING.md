# Makefile Troubleshooting Guide

## Fixed Issues

### ✅ Infinite Loop Problem (RESOLVED)
**Issue**: `make dev` would hang in an infinite loop and couldn't be terminated.

**Root Cause**: The `_dev-parallel` target was using `tail -f` and complex shell traps that created blocking operations.

**Solution**: Removed blocking operations and simplified process management:
- Removed `tail -f .backend.log` 
- Removed complex trap handling
- Simplified background process management
- Added proper error handling with `-` prefix

### ✅ Stop Command Issues (RESOLVED)
**Issue**: `make stop` would get terminated and not complete properly.

**Root Cause**: Process kill commands were failing and causing the entire target to fail.

**Solution**: Added error-tolerant commands:
- Used `-` prefix to ignore command failures
- Improved PID file cleanup
- Made all kill commands optional with proper error handling

## Current Status

### Working Commands:
```bash
make dev        # ✅ Starts services in background (no hanging)
make stop       # ✅ Properly stops all services  
make health     # ✅ Checks service status
make logs       # ✅ Shows service logs
make help       # ✅ Shows all commands
```

### Service Status:
- **Backend**: ✅ Running on http://localhost:8001
- **Frontend**: ✅ Running on http://localhost:3000  
- **Temporal**: ⚠️ Optional (requires Docker)

## Usage Workflow

### 1. Start Development:
```bash
make dev
```
This now:
- Starts services in background
- Returns control to terminal immediately
- Shows service URLs and status

### 2. Check Status:
```bash
make health     # Quick health check
make logs       # View recent logs
```

### 3. Stop Services:
```bash
make stop       # Cleanly stops everything
```

## Troubleshooting

### If Services Won't Start:
```bash
make stop       # Force stop everything
make clean      # Clean up artifacts
make dev        # Try again
```

### If Ports Are Busy:
```bash
# Check what's using the ports
lsof -i :3000
lsof -i :8001

# Kill specific processes if needed
make stop
```

### If Frontend Shows Blank Page:
1. Check if services are running: `make health`
2. Check logs for errors: `make logs`
3. Try refreshing browser or clearing cache
4. Verify API connection to backend

### If Backend API Errors:
1. Check if .env file exists with proper API keys
2. View backend logs: `make logs`
3. Test API directly: `curl http://localhost:8001/health`

## Process Management Details

The Makefile now uses proper background process management:

- **PID Files**: `.backend.pid`, `.frontend.pid`, `.worker.pid`
- **Log Files**: `.backend.log`, `.frontend.log`, `.worker.log`  
- **Clean Shutdown**: All processes killed gracefully
- **Error Tolerance**: Commands don't fail if processes don't exist

## Future Improvements

Possible enhancements:
- Add process monitoring/restart
- Better log aggregation
- Health check improvements
- Docker integration
- Production deployment targets