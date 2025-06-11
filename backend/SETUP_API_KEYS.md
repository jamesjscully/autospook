# AutoSpook OSINT API Key Setup Guide

## Required API Keys

To use AutoSpook's full OSINT capabilities, you need to configure API keys for the 3 different LLM providers and search services.

### 🤖 AI Model API Keys (All 3 Required)

#### 1. Anthropic API Key (Claude Models)
- **Used for**: Query Analysis, Planning, Retrieval, and Judge agents
- **Models**: Claude Sonnet 4, Claude Opus 4
- **Get from**: [Anthropic Console](https://console.anthropic.com/)
- **Environment Variable**: `ANTHROPIC_API_KEY`

#### 2. OpenAI API Key (GPT Models)  
- **Used for**: Pivot Analysis agent
- **Models**: GPT-4o
- **Get from**: [OpenAI Platform](https://platform.openai.com/api-keys)
- **Environment Variable**: `OPENAI_API_KEY`

#### 3. Google Gemini API Key (Gemini Models)
- **Used for**: Synthesis & Reporting agent
- **Models**: Gemini 1.5 Pro
- **Get from**: [Google AI Studio](https://aistudio.google.com/app/apikey)
- **Environment Variable**: `GEMINI_API_KEY`

### 🔍 Search API Keys (Required for OSINT)

#### 4. Google Custom Search API
- **Used for**: Web search capabilities across OSINT investigations
- **Setup Steps**:
  1. Get API key from [Google Developers Console](https://developers.google.com/custom-search/v1/introduction)
  2. Create Custom Search Engine at [Google CSE](https://cse.google.com/cse/)
  3. Configure to search the entire web
- **Environment Variables**: 
  - `GOOGLE_SEARCH_API_KEY`
  - `GOOGLE_CSE_ID`

### 🔧 Optional API Keys (Recommended)

#### 5. Bing Search API (Alternative web search)
- **Environment Variable**: `BING_API_KEY`

#### 6. SerpAPI (Advanced search capabilities)
- **Environment Variable**: `SERPAPI_KEY`

#### 7. LangSmith (Monitoring and debugging)
- **Get from**: [LangSmith Settings](https://smith.langchain.com/settings)
- **Environment Variable**: `LANGSMITH_API_KEY`

## Setup Instructions

### Method 1: Environment File (.env)

1. **Create your .env file**:
   ```bash
   cd backend
   cp .env.example .env
   ```

2. **Edit the .env file** with your actual API keys:
   ```bash
   # AI Model API Keys (ALL REQUIRED)
   ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
   OPENAI_API_KEY=sk-proj-xxxxx
   GEMINI_API_KEY=AIzaSyxxxxx
   
   # Search API Keys (REQUIRED)
   GOOGLE_SEARCH_API_KEY=AIzaSyxxxxx
   GOOGLE_CSE_ID=xxxxxxxxx:xxxxx
   
   # Optional but recommended
   LANGSMITH_API_KEY=ls__xxxxx
   ```

### Method 2: Environment Variables

Export directly in your shell:
```bash
export ANTHROPIC_API_KEY="sk-ant-api03-xxxxx"
export OPENAI_API_KEY="sk-proj-xxxxx"
export GEMINI_API_KEY="AIzaSyxxxxx"
export GOOGLE_SEARCH_API_KEY="AIzaSyxxxxx"
export GOOGLE_CSE_ID="xxxxxxxxx:xxxxx"
```

### Method 3: Docker Compose (Production)

Set in your `.env` file or export before running:
```bash
export ANTHROPIC_API_KEY="sk-ant-api03-xxxxx"
export OPENAI_API_KEY="sk-proj-xxxxx"
export GEMINI_API_KEY="AIzaSyxxxxx"
export GOOGLE_SEARCH_API_KEY="AIzaSyxxxxx"
export GOOGLE_CSE_ID="xxxxxxxxx:xxxxx"

docker-compose up
```

## Testing Your Setup

### 1. Test LLM Integration
```bash
cd backend
uv run python test_llm_integration.py
```

Expected output with API keys configured:
```
✅ ANTHROPIC_API_KEY configured for Claude models
✅ OPENAI_API_KEY configured for GPT models  
✅ GEMINI_API_KEY configured for Gemini models
✅ All agents created successfully
```

### 2. Test Full System
```bash
# Start with development API
uv run uvicorn simple_api:app --reload

# Or start full system with Docker
docker-compose up
```

### 3. Test Investigation
1. Open http://localhost:8000 (development) or http://localhost:8123 (docker)
2. Enter query: "Ali Khaledi Nasab"
3. Click "Start Investigation"
4. Verify agents are working and retrieving data

## Cost Considerations

### Estimated API Costs per Investigation:
- **Anthropic (Claude)**: ~$0.15-0.30 per investigation
- **OpenAI (GPT-4o)**: ~$0.10-0.20 per investigation  
- **Google (Gemini)**: ~$0.05-0.15 per investigation
- **Google Search**: ~$0.005 per query (8-12 queries per investigation)

**Total: ~$0.30-0.70 per investigation**

### Cost Optimization Tips:
1. Start with smaller `max_retrievals` values (8 instead of 12)
2. Use development mode for testing (mock responses)
3. Set rate limits to control usage
4. Monitor usage through provider dashboards

## Troubleshooting

### Common Issues:

#### "API key not configured" warnings
- Check your .env file is in the right location (`backend/.env`)
- Verify API key format (no extra spaces, quotes, etc.)
- Restart the application after changing .env

#### "Model not available" errors
- Verify you have access to the specific models
- Check your API key has sufficient credits/quota
- Some models may require special access (Claude Opus, GPT-4o)

#### "Connection refused" in tests
- Make sure Redis and PostgreSQL are running
- For Docker: run `docker-compose up`
- For development: install and start services locally

## Security Best Practices

1. **Never commit API keys to git**
   - `.env` files are gitignored
   - Use environment variables in production

2. **Rotate keys regularly**
   - Set up key rotation schedules
   - Monitor usage for anomalies

3. **Use least privilege**
   - API keys should have minimal required permissions
   - Set usage limits where possible

4. **Monitor costs and usage**
   - Set up billing alerts
   - Review usage regularly

## Need Help?

1. Check the test output: `uv run python test_llm_integration.py`
2. Review logs: `docker-compose logs autospook`
3. Verify API key permissions on provider dashboards
4. Ensure all services are running: `docker-compose ps`

Ready to start? Run: `uv run python test_llm_integration.py` to verify your setup! 