#!/bin/bash

# Complete Ubuntu Setup Script for Ollama RTX 5090 Deployment
# This script will set up a fresh Ubuntu 24.04 system with everything needed to run Ollama

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"; }
warn() { echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"; }
error() { echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"; exit 1; }
info() { echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"; }

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    error "This script should not be run as root. Please run as a regular user with sudo privileges."
fi

# Check Ubuntu version
check_ubuntu() {
    log "Checking Ubuntu version..."
    if ! lsb_release -d | grep -q "Ubuntu 24.04"; then
        warn "This script is optimized for Ubuntu 24.04 LTS. Current version:"
        lsb_release -d
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        log "✓ Ubuntu 24.04 LTS detected"
    fi
}

# Update system
update_system() {
    log "Updating system packages..."
    sudo apt update
    sudo apt upgrade -y
    sudo apt autoremove -y
}

# Install essential tools
install_essentials() {
    log "Installing essential tools..."
    sudo apt install -y \
        curl \
        wget \
        git \
        vim \
        htop \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release \
        python3 \
        python3-pip \
        python3-venv
}

# Install Docker
install_docker() {
    log "Installing Docker..."
    
    # Remove old versions
    sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # Add Docker's official GPG key
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Add Docker repository
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
    # Start and enable Docker
    sudo systemctl start docker
    sudo systemctl enable docker
    
    log "✓ Docker installed successfully"
}

# Install NVIDIA drivers (open source)
install_nvidia_driver() {
    log "Installing NVIDIA driver (open source version 575)..."
    
    # Check if NVIDIA GPU is present
    if ! lspci | grep -i nvidia > /dev/null; then
        error "No NVIDIA GPU detected. This script requires an NVIDIA GPU."
    fi
    
    log "✓ NVIDIA GPU detected"
    
    # Remove existing proprietary drivers
    sudo apt remove --purge -y nvidia-* libnvidia-* 2>/dev/null || true
    
    # Install open source NVIDIA driver
    sudo apt update
    sudo apt install -y \
        nvidia-driver-575-open \
        nvidia-settings
    
    log "✓ NVIDIA driver installed"
    log "⚠️  A reboot will be required after this script completes"
}

# Install NVIDIA Container Toolkit
install_nvidia_container_toolkit() {
    log "Installing NVIDIA Container Toolkit..."
    
    # Add NVIDIA Container Toolkit repository
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    
    curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    
    # Install NVIDIA Container Toolkit
    sudo apt update
    sudo apt install -y nvidia-container-toolkit
    
    # Configure Docker to use NVIDIA runtime
    sudo nvidia-ctk runtime configure --runtime=docker
    sudo systemctl restart docker
    
    log "✓ NVIDIA Container Toolkit installed and configured"
}

# Download Ollama deployment
setup_ollama_deployment() {
    log "Setting up Ollama RTX 5090 deployment..."
    
    # Create directory if it doesn't exist
    if [ ! -d "/home/$USER/ollama-rtx5090" ]; then
        error "Ollama deployment directory not found. Please ensure you have the ollama-rtx5090 directory with all files."
    fi
    
    cd "/home/$USER/ollama-rtx5090"
    
    # Make scripts executable
    chmod +x *.sh 2>/dev/null || true
    chmod +x *.py 2>/dev/null || true
    
    log "✓ Ollama deployment ready"
}

# Test installations
test_setup() {
    log "Testing installations..."
    
    # Test Docker
    if docker --version > /dev/null 2>&1; then
        log "✓ Docker: $(docker --version)"
    else
        warn "✗ Docker not working"
    fi
    
    # Test Docker Compose
    if docker compose version > /dev/null 2>&1; then
        log "✓ Docker Compose: $(docker compose version | head -1)"
    else
        warn "✗ Docker Compose not working"
    fi
    
    # Test NVIDIA driver (will only work after reboot)
    if nvidia-smi > /dev/null 2>&1; then
        log "✓ NVIDIA driver working"
        nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
    else
        warn "✗ NVIDIA driver not working (this is expected before reboot)"
    fi
    
    # Test NVIDIA Container Toolkit
    if nvidia-container-toolkit --version > /dev/null 2>&1; then
        log "✓ NVIDIA Container Toolkit: $(nvidia-container-toolkit --version | head -1)"
    else
        warn "✗ NVIDIA Container Toolkit not working"
    fi
}

# Main execution
main() {
    log "🚀 Setting up Ubuntu for Ollama RTX 5090 deployment"
    log "=================================================="
    
    check_ubuntu
    update_system
    install_essentials
    install_docker
    install_nvidia_driver
    install_nvidia_container_toolkit
    setup_ollama_deployment
    test_setup
    
    log "=================================================="
    log "✅ Ubuntu setup completed!"
    log ""
    log "🔄 IMPORTANT: You must reboot to complete NVIDIA driver installation"
    log ""
    log "After reboot:"
    log "1. Test NVIDIA: nvidia-smi"
    log "2. Test Docker + NVIDIA: docker run --rm --runtime=nvidia --gpus all nvidia/cuda:11.0-base nvidia-smi"
    log "3. Deploy Ollama: cd ~/ollama-rtx5090 && ./run.sh"
    log ""
    log "🎯 Your system will be ready to run Ollama with RTX 5090 optimization!"
    
    read -p "Reboot now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo reboot
    else
        log "Remember to reboot before running Ollama!"
    fi
}

# Run main function
main "$@"