# Use Ubuntu 22.04 as base image for better GPU support
FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install required packages
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Create ollama user and directories with proper permissions
RUN useradd -m -u 1000 ollama && \
    mkdir -p /home/ollama/.ollama/models && \
    chown -R ollama:ollama /home/ollama/.ollama

# Copy the start script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Set up environment for GPU
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

# Expose Ollama's default port
EXPOSE 11434

# Health check to ensure service is running
HEALTHCHECK --interval=60s --timeout=30s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:11434/api/health || exit 1

# Run as ollama user for security
USER ollama

# Start the service
CMD ["/start.sh"]
