# AutoSpook Google Cloud Deployment Guide

## Prerequisites

✅ Google Cloud CLI installed and configured  
✅ Docker installed and running  
✅ Required Google Cloud services enabled  

## Step 1: Configure API Keys

Edit `.env.production` and replace the placeholder values with your actual API keys:

```bash
# Required API Keys
OPENAI_API_KEY=sk-your-actual-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key-here  
EXA_API_KEY=your-actual-exa-key-here
SECRET_KEY=your-random-32-character-secret-key-here
```

**Get API Keys:**
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/
- Exa: https://dashboard.exa.ai/

## Step 2: Deploy to Google Cloud

Run the deployment command:

```bash
make deploy
```

This will:
1. Build the Docker image
2. Push to Google Container Registry
3. Create Google Cloud secrets
4. Deploy to Cloud Run
5. Provide the service URL

## Step 3: Generate Authentication Token

After deployment, generate a token for accessing the service:

```bash
make generate-token NAME=admin
```

Save the generated token securely - you'll need it to access the deployed service.

## Step 4: Test Deployment

The deployment includes a health check endpoint. Test it:

```bash
curl https://your-service-url/health
```

## Service Configuration

- **Memory**: 2GB
- **CPU**: 2 cores  
- **Timeout**: 60 minutes
- **Max Instances**: 10
- **Authentication**: Token-based
- **Region**: us-central1

## Security Features

- Token-based authentication for all OSINT routes
- Input validation and HTML sanitization
- Security headers with Flask-Talisman
- Rate limiting enabled
- Non-root container execution

## Troubleshooting

- **Build failures**: Check Docker is running
- **Permission errors**: Ensure proper Google Cloud authentication
- **API errors**: Verify API keys are correct and have sufficient credits
- **Timeout issues**: Large investigations may take several minutes

## Cost Management

- Service scales to zero when not in use
- Token expiration prevents unauthorized access
- Rate limiting prevents API abuse
- Monitor usage in Google Cloud Console