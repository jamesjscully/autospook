# 🚀 AutoSpook - Ready for Google Cloud Deployment

## Current Status: ✅ DEPLOYMENT READY

All code, configuration, and deployment scripts are prepared. You just need to:

1. **Add your API keys to `.env.production`**
2. **Start Docker daemon** 
3. **Run the deployment command**

## 🔧 Pre-Deployment Setup Required

### 1. Configure API Keys
Edit `.env.production` and replace these placeholder values:

```bash
OPENAI_API_KEY=your_openai_api_key_here      # Replace with: sk-...
ANTHROPIC_API_KEY=your_anthropic_api_key_here # Replace with: sk-ant-...
EXA_API_KEY=your_exa_api_key_here            # Replace with your Exa key
SECRET_KEY=your_random_secret_key_here        # Replace with 32-char random string
```

### 2. Start Docker Daemon
```bash
sudo systemctl start docker
```

## 🚀 Deploy to Google Cloud

Once API keys are configured and Docker is running:

```bash
make deploy
```

This single command will:
- ✅ Build the Docker image with security hardening
- ✅ Push to Google Container Registry (gcr.io/we-relate-1/autospook)
- ✅ Create encrypted Google Cloud secrets for API keys
- ✅ Deploy to Cloud Run with optimized configuration
- ✅ Enable auto-scaling (0-10 instances)
- ✅ Configure 60-minute timeout for long investigations
- ✅ Set up health checks and monitoring

## 🔐 Post-Deployment Security

Generate an admin authentication token:

```bash
make generate-token NAME=admin
```

**Save the token securely** - it cannot be recovered and expires in 30 days.

## 🎯 What's Deployed

### Service Configuration
- **URL**: Will be provided after deployment (https://autospook-xyz-uc.a.run.app)
- **Region**: us-central1
- **Memory**: 2GB
- **CPU**: 2 cores
- **Authentication**: Token-based access control
- **Scaling**: 0-10 instances (auto)

### Security Features
- 🔒 Token authentication for all OSINT endpoints
- 🛡️ Security headers (CSP, HSTS, etc.)
- 🚫 Input validation and HTML sanitization
- ⚡ Rate limiting protection
- 🔐 Non-root container execution
- 📊 Comprehensive logging

### Demo-Optimized OSINT
- 📝 2-3 focused investigation topics
- ❓ 1-2 essential questions per topic  
- 🔍 1-2 targeted search queries per question
- ⚡ Faster execution, lower costs
- 📊 Cleaner, more digestible reports

## 🧪 Testing the Deployment

After deployment, test the service:

```bash
# Health check (public)
curl https://your-service-url/health

# Frontend access (public)
curl https://your-service-url/

# Authentication test (requires token)
curl -X POST https://your-service-url/auth/validate \
  -H "Content-Type: application/json" \
  -d '{"token": "your-generated-token"}'
```

## 💰 Cost Management

- **Scales to zero** when not in use (no idle costs)
- **Token expiration** prevents unauthorized access
- **Rate limiting** prevents API abuse
- **Demo optimization** reduces AI API costs

## 📊 Monitoring

- Google Cloud Run metrics and logs
- Application health checks
- Token usage tracking
- Rate limiting statistics

---

**Next Steps:**
1. Add your API keys to `.env.production`
2. Start Docker: `sudo systemctl start docker`
3. Deploy: `make deploy`
4. Generate token: `make generate-token NAME=admin`
5. Test the deployed service

The system is production-ready with enterprise-grade security and optimized for demonstration purposes.