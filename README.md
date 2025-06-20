# AutoSpook - OSINT Intelligence Gathering Service

AutoSpook is an automated Open Source Intelligence (OSINT) gathering platform that combines AI-powered analysis with real-time web search to provide comprehensive security assessments of targets.

## 🎯 Purpose

AutoSpook performs automated due diligence and security risk assessment by:

- **Contextual Analysis** - Expands user-provided context with security-focused dimensions
- **Intelligent Investigation** - Generates relevant topics and questions based on security priorities
- **Automated Research** - Conducts systematic web searches using the Exa search API
- **Risk Assessment** - Evaluates findings and provides structured security reports
- **Executive Summary** - Distills complex investigations into actionable insights

## 🏗️ Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Web Interface                        │
│                     (Flask + HTMX)                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                    Orchestrator                            │
│                 (Investigation Loop)                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
           ┌──────────┼──────────┐
           │          │          │
┌──────────▼─┐   ┌────▼────┐   ┌─▼─────────┐
│ BAML Client│   │Exa Search│   │Rate Limiter│
│ (AI Models)│   │   API    │   │  (Safety)  │
└────────────┘   └─────────┘   └───────────┘
```

### Data Flow

1. **Input** → User provides target name and context via web interface
2. **Stepback Analysis** → AI expands context with security dimensions
3. **Topic Generation** → AI identifies investigation priorities
4. **Question Formulation** → AI creates specific research questions
5. **Search Loop** → For each open question:
   - Generate search queries
   - Execute Exa searches
   - Collect evidence snippets
   - Evaluate question completion
6. **Report Generation** → AI synthesizes findings into HTML report
7. **Digest Creation** → AI extracts structured summary for UI

### AI Model Assignment Strategy

| Task Type | Model | Rationale |
|-----------|-------|-----------|
| **Strategic Analysis** | Claude Sonnet | Complex reasoning, security focus |
| **Topic/Question Generation** | GPT-4o | Strategic planning, comprehensive coverage |
| **Query Generation** | CustomFast (Round-robin) | High-volume, permissive rate limits |
| **Evidence Evaluation** | GPT-4o-mini | Cost-effective, frequent calls |
| **Report Writing** | Claude Sonnet | Superior long-form content generation |
| **Summary Extraction** | GPT-4o-mini | Structured data extraction |

## 🔧 Technical Stack

### Backend
- **Flask** - Web framework
- **BAML** - AI function orchestration and type safety
- **Python** - Core logic and integrations

### AI Providers
- **OpenAI** - GPT-4o, GPT-4o-mini models
- **Anthropic** - Claude Sonnet, Claude Haiku models

### External APIs
- **Exa Search** - Advanced web search and content retrieval

### Frontend
- **HTMX** - Dynamic UI updates
- **Tailwind CSS** - Styling and responsive design

## 📁 Project Structure

```
autospook2/
├── app.py                 # Flask web application
├── orchestrator.py        # Investigation orchestration logic
├── exa_integration.py     # Exa search API wrapper
├── rate_limiter.py        # API rate limiting utilities
├── requirements.txt       # Python dependencies
├── Makefile              # Build and run commands
├── .env                  # Environment variables (create this)
├── templates/
│   └── index.html        # Web interface
├── baml_src/             # BAML configuration
│   ├── new_prompts.baml  # Main AI functions
│   ├── clients.baml      # AI model client definitions
│   └── exa_api.baml      # Exa integration functions
└── baml_client/          # Generated BAML Python client
```

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10+
- API keys for OpenAI, Anthropic, and Exa

### Installation

1. **Clone repository**
   ```bash
   git clone <repository-url>
   cd autospook2
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv313
   source venv313/bin/activate  # Linux/Mac
   # or
   venv313\Scripts\activate     # Windows
   ```

3. **Install dependencies**
   ```bash
   make install
   ```

4. **Configure environment variables**
   Create `.env` file:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   EXA_API_KEY=your_exa_api_key_here
   ```

5. **Generate BAML client**
   ```bash
   make baml-generate
   ```

6. **Run application**
   ```bash
   make run
   ```

Visit `http://127.0.0.1:5000` to access the interface.

## 🛠️ Development Commands

```bash
make help           # Show all available commands
make install        # Install dependencies
make run           # Run production server
make dev           # Run development server
make baml-generate # Regenerate BAML client
make clean         # Clean Python cache files
make setup         # Full setup and run
```

## ⚡ Features

### Intelligent Investigation
- **Adaptive Questioning** - Dynamically generates follow-up questions based on evidence gaps
- **Convergence Detection** - Automatically stops when sufficient evidence is gathered
- **Priority-Based Research** - Focuses on security-critical questions first

### Rate Limiting & Reliability
- **Multi-Provider Rate Limiting** - Prevents API timeouts and quota exhaustion
- **Exponential Backoff** - Automatic retry with increasing delays
- **Fallback Strategies** - Round-robin and failover between AI providers

### Security Focus
- **OSINT Methodology** - Follows established intelligence gathering practices
- **Risk Assessment** - Evaluates security implications of findings
- **Evidence Validation** - Cross-references multiple sources

### User Experience
- **Real-time Updates** - HTMX-powered dynamic interface
- **Structured Output** - Organized findings with risk levels and recommendations
- **Export Ready** - Clean HTML reports for further analysis

## 🔐 Security Considerations

- **API Key Protection** - Environment variables, never committed to version control
- **Rate Limiting** - Prevents aggressive API usage that could trigger security alerts
- **Data Handling** - Transient processing, no persistent storage of sensitive data
- **Compliance Focus** - Designed for legitimate due diligence use cases

## 📊 Performance

### Typical Investigation Timeline
- **Small Target** (3-5 topics): 2-5 minutes
- **Medium Target** (5-8 topics): 5-10 minutes  
- **Large Target** (8+ topics): 10-20 minutes

### API Usage (per investigation)
- **AI Model Calls**: 50-200 requests
- **Search Queries**: 20-100 queries
- **Rate Limiting**: Keeps usage within API limits

## 🤝 Contributing

1. Follow existing code style and patterns
2. Update BAML schemas when modifying AI functions
3. Regenerate BAML client after schema changes
4. Test with rate limiting enabled
5. Document any new environment variables

## 📄 License

[Add your license information here]

## ⚠️ Disclaimer

AutoSpook is designed for legitimate security research and due diligence purposes. Users are responsible for ensuring compliance with applicable laws and regulations. Always respect privacy, terms of service, and ethical guidelines when conducting OSINT research.