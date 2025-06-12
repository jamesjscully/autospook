# AutoSpook OSINT System Integration Guide

This guide walks you through running the complete integrated AutoSpook OSINT system with all components working together.

## Architecture Overview

The integrated system consists of:

1. **Frontend (React)**: User interface at `http://localhost:5173`
2. **Backend API (FastAPI)**: OSINT-specific endpoints at `http://localhost:8000`
3. **LangGraph Server**: Multi-agent orchestration at `http://localhost:2024`
4. **PostgreSQL**: Persistent storage for investigations
5. **Redis**: Caching and real-time pub/sub

## Prerequisites

- Python 3.8+
- Node.js 18+ and npm
- Docker and Docker Compose (recommended)
- API Keys for:
  - Anthropic (Claude)
  - OpenAI (GPT-4)
  - Google Gemini
  - Google Search API

## Quick Start

### 1. Clone and Setup

```bash
cd ~/code/autospook
```

### 2. Setup Environment Variables

```bash
cd backend
cp env.example .env
# Edit .env with your actual API keys
nano .env
```

Required API keys:
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `GOOGLE_SEARCH_API_KEY`
- `GOOGLE_CSE_ID`
- `ENABLE_PHOENIX` (optional, enables Arize Phoenix tracing)

### 3. Start Data Layer

```bash
# From project root
docker-compose up -d osint-postgres osint-redis

# Verify services
docker-compose ps
```

### 4. Install Backend Dependencies

```bash
cd backend
pip install -e .
```

### 5. Run Database Tests

```bash
cd backend
python test_database.py
```

Expected output:
```
✓ PostgreSQL connected
✓ Redis connected
✓ All tests passed!
```

### 6. Start Backend Services

#### Option A: Integrated Startup (Recommended)

```bash
cd backend
python start_integrated.py
```

This will:
- Check database connections
- Verify environment variables
- Start LangGraph server on port 2024
- Start OSINT API on port 8000

#### Option B: Manual Startup

Terminal 1 - LangGraph Server:
```bash
cd backend
langgraph dev --port 2024
```

Terminal 2 - OSINT API:
```bash
cd backend
uvicorn src.api.osint_api:app --reload --port 8000
```

### 7. Start Frontend

In a new terminal:
```bash
cd frontend
npm install  # If not done already
npm run dev
```

## Accessing the System

Once all services are running:

- **Frontend UI**: http://localhost:5173
- **OSINT API Docs**: http://localhost:8000/docs
- **LangGraph Studio**: http://localhost:2024/studio
- **LangGraph API**: http://localhost:2024/docs

## Testing the Integration

### 1. Basic Health Check

```bash
# Check OSINT API
curl http://localhost:8000/health

# Check LangGraph
curl http://localhost:2024/health
```

### 2. Start an Investigation via UI

1. Open http://localhost:5173
2. Enter query: "Ali Khaledi Nasab"
3. Select focus areas and settings
4. Click "Start Investigation"
5. Watch real-time progress updates

### 3. Start an Investigation via API

```bash
curl -X POST http://localhost:8000/api/investigations \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Ali Khaledi Nasab",
    "max_retrievals": 12,
    "focus_areas": ["web", "social"]
  }'
```

### 4. Monitor Investigation

```bash
# Get status
curl http://localhost:8000/api/investigations/{investigation_id}

# Get entities
curl http://localhost:8000/api/investigations/{investigation_id}/entities

# Get sources
curl http://localhost:8000/api/investigations/{investigation_id}/sources

# Get report (when complete)
curl http://localhost:8000/api/investigations/{investigation_id}/report
```

## Data Flow

1. **User submits query** → Frontend
2. **Frontend calls API** → POST /api/investigations
3. **API creates investigation** → Database
4. **API starts OSINT graph** → Background task
5. **Graph runs agents** → Query Analysis → Planning → Retrieval → Pivot → Synthesis → Judge
6. **Each agent persists data** → Database via Memory Manager
7. **Updates published** → Redis pub/sub
8. **WebSocket forwards updates** → Frontend
9. **Frontend displays progress** → Real-time UI updates
10. **Final report stored** → Database
11. **User views report** → Frontend

## Architecture Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│  OSINT API  │────▶│  LangGraph  │
│  (React)    │◀────│  (FastAPI)  │◀────│   Server    │
└─────────────┘     └─────────────┘     └─────────────┘
       ▲                    │                    │
       │                    ▼                    ▼
       │            ┌─────────────┐     ┌─────────────┐
       │            │ PostgreSQL  │     │    Redis    │
       └────────────│  Database   │◀────│  Pub/Sub   │
     WebSocket      └─────────────┘     └─────────────┘
```

## Common Issues & Solutions

### Database Connection Failed

```bash
# Check if services are running
docker-compose ps

# Check logs
docker-compose logs osint-postgres
docker-compose logs osint-redis

# Restart services
docker-compose restart osint-postgres osint-redis
```

### Missing API Keys

```bash
# Verify .env file
cat backend/.env | grep API_KEY

# Source environment
cd backend
source .env  # or use direnv
```

### Port Already in Use

```bash
# Find process using port
lsof -i :2024  # or :8000, :5173

# Kill process
kill -9 <PID>
```

### Frontend Can't Connect to Backend

Check CORS settings and ensure backend is running on expected ports.

## Production Deployment

### Using Docker Compose

```bash
# Build and run all services
docker-compose up -d

# Scale retrieval workers
docker-compose scale osint-worker=3
```

### Environment Variables for Production

```env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:pass@db-host:5432/osint_db
REDIS_URL=redis://redis-host:6379
ALLOWED_ORIGINS=https://your-domain.com
```

### Security Considerations

1. Use strong database passwords
2. Enable SSL/TLS for all connections
3. Implement API authentication
4. Rate limit API endpoints
5. Encrypt sensitive data at rest
6. Regular security audits

## Monitoring

### Check System Health

```bash
# Database stats
docker exec -it osint-postgres psql -U osint_user -d osint_db -c "
  SELECT 
    COUNT(*) as investigations,
    SUM(sources_count) as total_sources,
    SUM(entities_count) as total_entities
  FROM investigations;
"

# Redis memory
docker exec -it osint-redis redis-cli info memory
```

### View Logs

```bash
# Backend logs
docker-compose logs -f osint-backend

# Frontend logs
npm run dev  # Shows in terminal

# Database logs
docker-compose logs -f osint-postgres
```

## Backup & Recovery

### Backup Database

```bash
# Create backup
docker exec osint-postgres pg_dump -U osint_user osint_db > backup_$(date +%Y%m%d).sql

# Backup Redis
docker exec osint-redis redis-cli BGSAVE
```

### Restore Database

```bash
# Restore from backup
docker exec -i osint-postgres psql -U osint_user osint_db < backup_20240101.sql
```

## Development Tips

### Hot Reloading

- Frontend: Automatic with Vite
- Backend API: Use `--reload` flag with uvicorn
- LangGraph: Restart required for graph changes

### Testing Individual Components

```bash
# Test database layer
python backend/test_database.py

# Test OSINT graph
python backend/test_osint_simple.py

# Test API endpoints
curl -X GET http://localhost:8000/docs
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export DEBUG=true

# Run with verbose output
python start_integrated.py
```

## Support

For issues:
1. Check logs for errors
2. Verify all services are running
3. Ensure API keys are valid
4. Test database connectivity
5. Review this guide

Happy investigating with AutoSpook! 🕵️‍♂️ 