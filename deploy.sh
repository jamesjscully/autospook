#!/bin/bash

# AutoSpook Cloud Run Deployment Script
set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"we-relate-1"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="autospook"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Deploying AutoSpook to Google Cloud Run"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"

# Check if required environment variables are set
if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "your-project-id" ]; then
    echo "❌ Error: PROJECT_ID environment variable must be set"
    echo "   export PROJECT_ID=your-google-cloud-project-id"
    exit 1
fi

# Check if required tools are installed
command -v gcloud >/dev/null 2>&1 || { echo "❌ Error: gcloud CLI is required but not installed."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Error: Docker is required but not installed."; exit 1; }

# Authenticate with Google Cloud
echo "🔐 Authenticating with Google Cloud..."
gcloud auth configure-docker

# Build and push Docker image
echo "🐳 Building Docker image..."
docker build -t ${IMAGE_NAME}:latest .

echo "📤 Pushing image to Google Container Registry..."
docker push ${IMAGE_NAME}:latest

# Create secrets if they don't exist
echo "🔑 Creating secrets..."
gcloud secrets create autospook-secrets --data-file=.env.production --project=${PROJECT_ID} || echo "Secret already exists"

# Deploy to Cloud Run
echo "☁️ Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image=${IMAGE_NAME}:latest \
    --platform=managed \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --allow-unauthenticated \
    --set-env-vars="FLASK_ENV=production,FLASK_DEBUG=False" \
    --set-secrets="OPENAI_API_KEY=autospook-secrets:latest:openai-api-key,ANTHROPIC_API_KEY=autospook-secrets:latest:anthropic-api-key,EXA_API_KEY=autospook-secrets:latest:exa-api-key,SECRET_KEY=autospook-secrets:latest:secret-key" \
    --memory=2Gi \
    --cpu=2 \
    --timeout=3600 \
    --max-instances=10 \
    --min-instances=0 \
    --concurrency=10

echo "✅ Deployment complete!"
echo "🌐 Service URL:"
gcloud run services describe ${SERVICE_NAME} --region=${REGION} --project=${PROJECT_ID} --format="value(status.url)"