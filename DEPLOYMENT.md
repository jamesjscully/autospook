# AutoSpook Deployment Guide

## Security Checklist ✅

Before deploying to production, ensure you've completed these security steps:

### Critical Security Issues Fixed:
- ✅ **API Keys**: Moved to secure environment variables (no longer in repository)
- ✅ **Input Validation**: Added strict input validation and sanitization
- ✅ **XSS Protection**: Implemented HTML sanitization and escaping
- ✅ **Error Handling**: Secure error messages (no sensitive info disclosure)
- ✅ **Security Headers**: Added CSP, HSTS, and other security headers
- ✅ **Debug Mode**: Disabled in production
- ✅ **Rate Limiting**: Built-in API rate limiting protection

## Prerequisites

1. **Google Cloud Platform Account**
2. **Docker installed locally**
3. **Google Cloud SDK (gcloud CLI)**
4. **API Keys**: OpenAI, Anthropic, Exa

## Quick Deploy to Google Cloud Run

### 1. Setup Environment
```bash
# Clone and navigate to project
git clone <repository-url>
cd autospook2

# Set your Google Cloud project
export PROJECT_ID=your-google-cloud-project-id
export REGION=us-central1
```

### 2. Configure API Keys
```bash
# Copy template and configure
cp .env.production.example .env.production

# Edit with your actual API keys
nano .env.production
```

### 3. Setup Google Cloud
```bash
# Authenticate and configure
gcloud auth login
gcloud config set project $PROJECT_ID

# Enable required services
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Configure Docker for GCR
gcloud auth configure-docker
```

### 4. Deploy
```bash
# Build, push, and deploy in one command
make deploy
```

## Development Workflow

### Local Development
```bash
# Install dependencies
make install

# Generate BAML client
make baml-generate

# Run development server
make dev
```

### Docker Development
```bash
# Build container
make docker-build

# Test container locally
make docker-test

# Run container locally
make docker-run
```

### Security Testing
```bash
# Run security scans
make security-check

# Run application tests
make test
```

## Available Make Commands

### Development
- `make install` - Install Python dependencies
- `make dev` - Run development server with hot reload
- `make baml-generate` - Regenerate BAML client code
- `make clean` - Clean Python cache files

### Security & Testing
- `make security-check` - Run security vulnerability scans
- `make test` - Run application tests

### Docker
- `make docker-build` - Build Docker container
- `make docker-run` - Run container locally (port 8080)
- `make docker-test` - Test container functionality
- `make docker-push` - Push to Google Container Registry

### Deployment
- `make deploy` - Deploy to Google Cloud Run
- `make logs` - View Cloud Run logs
- `make setup-gcp` - Show GCP setup instructions

## Production Configuration

### Environment Variables Required:
```bash
OPENAI_API_KEY=sk-...        # OpenAI API key
ANTHROPIC_API_KEY=sk-ant-... # Anthropic API key  
EXA_API_KEY=...              # Exa Search API key
SECRET_KEY=...               # Strong random secret (32+ chars)
FLASK_ENV=production
FLASK_DEBUG=False
```

### Resource Allocation:
- **CPU**: 2 vCPU
- **Memory**: 2GB RAM
- **Timeout**: 3600 seconds (1 hour)
- **Concurrency**: 10 requests per instance
- **Scaling**: 0-10 instances

## Security Features

### Input Validation
- Maximum input lengths enforced
- Character allowlist validation
- HTML sanitization with bleach

### Security Headers
- Content Security Policy (CSP)
- HTTP Strict Transport Security (HSTS)
- X-Frame-Options
- X-Content-Type-Options

### API Protection
- Rate limiting per provider
- Exponential backoff
- Request timeout protection

### Container Security
- Non-root user execution
- Minimal attack surface
- Security scanning in CI/CD

## Monitoring and Maintenance

### Health Checks
- Startup probe: 60 seconds
- Liveness probe: 30 second intervals
- Readiness probe: HTTP GET /

### Logging
- Structured JSON logging
- Security event logging
- Error tracking and alerting

### Updates
```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Rebuild and deploy
make docker-build
make deploy
```

## Troubleshooting

### Common Issues:

1. **API Key Errors**
   - Verify `.env.production` file exists
   - Check API key validity
   - Ensure secrets are created in Google Cloud

2. **Memory Issues**
   - Increase Cloud Run memory allocation
   - Check for memory leaks in investigations

3. **Timeout Errors**
   - Increase Cloud Run timeout (max 3600s)
   - Optimize AI model selection
   - Implement better rate limiting

4. **Permission Errors**
   - Verify Google Cloud IAM permissions
   - Check service account configuration

### Debug Commands:
```bash
# View logs
make logs

# Test container locally
make docker-run

# Check security issues
make security-check
```

## Cost Optimization

### API Usage:
- **OpenAI**: ~$0.01-0.10 per investigation
- **Anthropic**: ~$0.01-0.05 per investigation
- **Exa**: ~$0.001 per search query

### Cloud Run Costs:
- **CPU**: $0.0000024 per vCPU-second
- **Memory**: $0.0000025 per GB-second
- **Requests**: $0.0000004 per request

### Estimated Monthly Costs:
- **Low usage** (100 investigations): ~$5-15
- **Medium usage** (1000 investigations): ~$50-150
- **High usage** (10000 investigations): ~$500-1500

## Security Considerations

### Data Handling:
- No persistent storage of investigation data
- Transient processing only
- API keys secured with Google Secret Manager

### Network Security:
- HTTPS enforced
- Private Google networks
- No public database exposure

### Compliance:
- Designed for legitimate OSINT research
- Respects API terms of service
- Implements rate limiting to prevent abuse

### Legal Notice:
AutoSpook is intended for legitimate security research and due diligence purposes only. Users are responsible for ensuring compliance with applicable laws and regulations.