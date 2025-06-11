# AutoSpook OSINT Quick Start

Welcome to AutoSpook! This guide will get you up and running in minutes.

## Prerequisites

- Python 3.8+ (for backend)
- Node.js 18+ (for frontend)
- Git

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/autospook.git
   cd autospook
   ```

2. **Install backend dependencies:**
   ```bash
   cd backend
   pip install -e .
   cd ..
   ```

3. **Install frontend dependencies:**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

## Running the Development Environment

### Quick Start (Recommended)

Run both frontend and backend with a single command:

```bash
python dev_launch.py
```

This will:
- Start the backend API on http://localhost:8000
- Start the frontend on http://localhost:5173 (or next available port)
- Show combined logs in a single terminal
- Test both services and display access URLs

### Manual Start

If you prefer to run services separately:

**Backend:**
```bash
cd backend
python -m uvicorn simple_api:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
```bash
cd frontend
npm run dev
```

## Testing the Application

1. **Open the application:**
   - Visit http://localhost:5173/app/
   - You'll see the AutoSpook OSINT Dashboard

2. **Run a test investigation:**
   - Enter query: "Ali Khaledi Nasab"
   - Click "Start Investigation"
   - Watch as mock entities, sources, and analysis appear
   - View the generated report when complete

3. **API Endpoints:**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - Direct API: http://localhost:8000/api/investigations

## Project Structure

```
autospook/
├── backend/
│   ├── simple_api.py          # Development API server
│   ├── src/                   # Full OSINT agent implementation
│   │   ├── agent/            # Multi-agent workflow
│   │   ├── api/              # Production API layer
│   │   ├── database/         # Data persistence
│   │   └── service/          # LangGraph integration
│   └── tests/                # Backend tests
├── frontend/
│   ├── src/                  # React application
│   │   ├── app/              # Main app components
│   │   ├── components/       # UI components
│   │   └── contexts/         # React contexts
│   └── public/               # Static assets
├── tests/                    # Integration tests
├── dev_launch.py            # Development launcher
└── run_tests.py             # Test runner
```

## Development Modes

### Simple Development Mode (Default)
- Uses `simple_api.py` with mock data
- No external dependencies required
- Perfect for frontend development and testing

### Full Integration Mode
- Requires PostgreSQL, Redis, and API keys
- Uses complete multi-agent workflow
- See `INTEGRATION_GUIDE.md` for setup

## Testing

Run the test suite:

```bash
python run_tests.py
```

This runs:
- Backend API tests
- Frontend integration tests  
- Development launcher tests

## Troubleshooting

### Port Conflicts
The launcher automatically detects available ports. If you see port conflict errors:
- Stop other services using ports 8000 or 5173
- The launcher will find alternative ports and display them

### Dependencies Issues
```bash
# Backend dependencies
cd backend && pip install -e .

# Frontend dependencies  
cd frontend && npm install
```

### Can't Access Application
1. Check if services are running: http://localhost:8000/health
2. Check the launcher output for actual ports used
3. Try manually starting services as described above

## Next Steps

- **Customize the UI**: Modify components in `frontend/src/components/`
- **Add real integrations**: Configure API keys and use full agent workflow
- **Extend agents**: Add new specialized agents in `backend/src/agent/`
- **Deploy**: Use `docker-compose.yml` for production deployment

## Support

- 📖 **Documentation**: See `INTEGRATION_GUIDE.md` for advanced setup
- 🧪 **Testing**: See `TESTING.md` for test documentation
- 📝 **Issues**: Create GitHub issues for bugs or feature requests

Happy investigating! 🕵️‍♂️ 