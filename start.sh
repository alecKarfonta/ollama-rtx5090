#!/bin/bash

echo "🚀 Starting Ollama server for RTX 5090..."
echo "📊 Model: Will pull qwen3:30b-a3b-instruct-2507-q4_K_M on first run"
echo "🔌 OpenAI API compatible endpoints will be available"

# Configure Ollama to listen on all interfaces for Docker port mapping
export OLLAMA_HOST=0.0.0.0:11434

# Force all GPU layers (override automatic calculation) - MAXIMUM GPU USAGE
export OLLAMA_GPU_LAYERS=999
export OLLAMA_MAX_VRAM=32000000000
export OLLAMA_GPU_MEMORY_UTILIZATION=0.98
export CUDA_MEMORY_FRACTION=0.98

# Start Ollama server in the background
ollama serve &
OLLAMA_PID=$!

# Wait for server to start
echo "⏳ Waiting for Ollama server to start..."
sleep 10

# Wait for the API to be ready
echo "🔍 Checking if Ollama API is ready..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/health >/dev/null 2>&1; then
        echo "✅ Ollama API is ready!"
        break
    fi
    echo "⏳ Waiting for API... ($i/30)"
    sleep 2
done

# Pull the model (this will happen on first run)
echo "📥 Pulling model (this may take a while on first run)..."
ollama pull qwen3:30b-a3b-instruct-2507-q4_K_M

# Create 262K context version if it doesn't exist
if ! ollama list | grep -q "qwen3:200k"; then
    echo "🔧 Creating 200K context version..."
    echo "FROM qwen3:30b-a3b-instruct-2507-q4_K_M" > /tmp/Modelfile.200k
    echo "PARAMETER num_ctx 200000" >> /tmp/Modelfile.200k

    ollama create qwen3:200k -f /tmp/Modelfile.200k
fi

echo "✅ Ollama server ready with Qwen3 30B A3B Instruct (200K context)!"
echo "🔗 Ollama API endpoint: http://localhost:11434/api/"
echo "🔗 OpenAI compatible endpoint: http://localhost:11434/v1/"
echo "📝 Available model name: qwen3:200k"

# Keep the container running
wait $OLLAMA_PID