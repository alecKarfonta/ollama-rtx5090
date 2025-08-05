#!/bin/bash

# Ollama RTX 5090 Deployment Script

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"; }
info() { echo -e "${BLUE}[INFO] $1${NC}"; }
warn() { echo -e "${YELLOW}[WARN] $1${NC}"; }
error() { echo -e "${RED}[ERROR] $1${NC}"; }

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    error "docker-compose.yml not found. Run this script from the ollama-rtx5090 directory."
    exit 1
fi

# Check for NVIDIA GPU
if ! nvidia-smi > /dev/null 2>&1; then
    error "NVIDIA GPU not detected. Please install NVIDIA drivers."
    exit 1
fi

# Check Docker
if ! docker --version > /dev/null 2>&1; then
    error "Docker not found. Please install Docker."
    exit 1
fi

# Check NVIDIA Container Toolkit
if ! nvidia-container-toolkit --version > /dev/null 2>&1; then
    error "NVIDIA Container Toolkit not working. Please install and configure it."
    exit 1
fi

log "Starting Ollama RTX 5090 deployment..."

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    log "Creating .env file from template..."
    cp .env.example .env
    info "Please edit .env file if you need to customize settings"
fi

# Build and start services
log "Building and starting Ollama container..."
docker compose up -d --build

# Wait for service to be ready
log "Waiting for Ollama to be ready..."
for i in {1..60}; do
    if curl -s http://localhost:11434/api/health > /dev/null 2>&1; then
        log "✅ Ollama is ready!"
        break
    fi
    if [ $i -eq 60 ]; then
        error "Timeout waiting for Ollama to start"
        docker compose logs ollama
        exit 1
    fi
    sleep 2
done

# Show status
log "Checking service status..."
docker compose ps

# Test basic functionality
log "Testing API endpoints..."

# Test Ollama native API
if curl -s http://localhost:11434/api/version > /dev/null; then
    log "✅ Ollama native API working"
else
    warn "❌ Ollama native API not responding"
fi

# Test OpenAI compatible API
if curl -s http://localhost:11434/v1/models > /dev/null; then
    log "✅ OpenAI compatible API working"
else
    warn "❌ OpenAI compatible API not responding"
fi

# Show available models
log "Available models:"
curl -s http://localhost:11434/api/tags | python3 -m json.tool 2>/dev/null || echo "No models available yet"

log "🚀 Ollama RTX 5090 deployment complete!"
echo
info "API Endpoints:"
echo "  Ollama API:  http://localhost:11434/api/"
echo "  OpenAI API:  http://localhost:11434/v1/"
echo
info "Test commands:"
echo "  curl http://localhost:11434/api/version"
echo "  curl http://localhost:11434/v1/models"
echo "  python3 test_ollama.py"
echo "  python3 test_large_context.py"
echo
info "Monitor with:"
echo "  docker compose logs -f ollama"
echo "  nvidia-smi"