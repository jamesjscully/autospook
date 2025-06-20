# Docker Setup for AutoSpook Deployment

## Issue: Docker Daemon Not Running

The deployment failed because Docker daemon is not running. Here are solutions:

## Solution 1: Start Docker (Recommended)

```bash
# Start Docker daemon (requires password)
sudo systemctl start docker

# Enable Docker to start on boot
sudo systemctl enable docker

# Verify Docker is running
docker ps
```

## Solution 2: Alternative Docker Start Methods

If systemctl doesn't work, try:

```bash
# Start Docker daemon directly
sudo dockerd &

# Or use service command
sudo service docker start
```

## Solution 3: Check Docker Status

```bash
# Check if Docker is running
sudo systemctl status docker

# Check Docker daemon logs if issues persist
sudo journalctl -u docker.service
```

## After Starting Docker

Once Docker is running, retry the deployment:

```bash
# Test Docker is working
docker --version
docker ps

# Then deploy
make deploy-test
```

## Verify Docker Setup

```bash
# Check user is in docker group (should show 'docker')
groups $USER

# Test Docker without sudo (after daemon is running)
docker run hello-world
```

## Troubleshooting

If you get permission errors after starting Docker:

```bash
# Add user to docker group (if not already done)
sudo usermod -aG docker $USER

# Log out and back in, or run:
newgrp docker
```

## Production Deployment Flow

1. **Start Docker**: `sudo systemctl start docker`
2. **Add API keys**: Edit `.env.production`
3. **Test deploy**: `make deploy-test`
4. **Production deploy**: `make deploy`
5. **Generate token**: `make generate-token NAME=admin`

The Docker issue is the only blocker - everything else is ready for deployment!