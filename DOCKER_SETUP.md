# Docker Setup for AutoSpook

AutoSpook requires Docker for running Temporal infrastructure. Here's how to set it up:

## Check Docker Status

```bash
make check-docker
```

## Start Docker

### Linux (Ubuntu/Debian)
```bash
# Start Docker daemon
sudo systemctl start docker

# Enable Docker to start on boot
sudo systemctl enable docker

# Add your user to docker group (optional, requires logout/login)
sudo usermod -aG docker $USER
```

### macOS/Windows
- Start Docker Desktop application

## Verify Docker is Running

```bash
docker info
```

## Start AutoSpook with Temporal

Once Docker is running:

```bash
make dev
```

This will:
1. Start Temporal infrastructure (PostgreSQL + Temporal Server + UI)
2. Start Temporal worker for OSINT research
3. Start AutoSpook backend API
4. Start React frontend

## Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **Temporal UI**: http://localhost:8080

## Troubleshooting

### Docker Permission Denied
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

### Docker Not Starting
```bash
sudo systemctl status docker
sudo journalctl -u docker
```

### Temporal Connection Issues
```bash
# Check if containers are running
docker ps

# Check Temporal logs
docker logs autospook-temporal-1
```