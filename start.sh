#!/bin/bash

echo "🚀 Starting Ollama server for RTX 5090..."
echo "📊 Model: Will pull qwen3:30b-a3b-instruct-2507-q4_K_M on first run"
echo "🔌 OpenAI API compatible endpoints will be available"

# Configure Ollama to listen on all interfaces for Docker port mapping
export OLLAMA_HOST=0.0.0.0:11434

# Force 48/49 GPU layers (override automatic calculation) - MAXIMUM GPU USAGE
export OLLAMA_GPU_LAYERS=48
export OLLAMA_MAX_VRAM=32607000000
export OLLAMA_GPU_MEMORY_UTILIZATION=0.99
export CUDA_MEMORY_FRACTION=0.99

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

# Pull the models (this will happen on first run)
echo "📥 Pulling models (this may take a while on first run)..."
ollama pull qwen3:30b-a3b-instruct-2507-q4_K_M
echo "📥 Pulling gpt-oss-20b (OpenAI's open-weight reasoning model)..."
ollama pull hf.co/unsloth/gpt-oss-20b-GGUF:Q4_K_M

# Create 128K context version optimized for full GPU layer utilization
if ! ollama list | grep -q "qwen3:200k"; then
    echo "🔧 Creating 128K context version (optimized for all 49 GPU layers)..."
    echo "FROM qwen3:30b-a3b-instruct-2507-q4_K_M" > /tmp/Modelfile.200k
    echo "PARAMETER num_ctx 200000" >> /tmp/Modelfile.200k
    echo "PARAMETER num_gpu 999" >> /tmp/Modelfile.200k

    ollama create qwen3:200k -f /tmp/Modelfile.200k
fi

# Create optimized GPT-OSS version with high reasoning level
if ! ollama list | grep -q "gpt-oss:reasoning"; then
    echo "🔧 Creating GPT-OSS reasoning version (optimized for RTX 5090)..."
    echo "FROM hf.co/unsloth/gpt-oss-20b-GGUF:Q4_K_M" > /tmp/Modelfile.gpt-oss
    echo "PARAMETER num_ctx 128000" >> /tmp/Modelfile.gpt-oss
    echo "PARAMETER num_gpu 999" >> /tmp/Modelfile.gpt-oss
    echo "SYSTEM You are a helpful assistant. Use high-level reasoning for complex tasks. Reasoning: high" >> /tmp/Modelfile.gpt-oss
    echo "TEMPLATE \"{{ .System }}{{ .Prompt }}\"" >> /tmp/Modelfile.gpt-oss

    ollama create gpt-oss:reasoning -f /tmp/Modelfile.gpt-oss
fi

echo "✅ Ollama server ready with multiple models (optimized for RTX 5090)!"
echo "🔗 Ollama API endpoint: http://localhost:11434/api/"
echo "🔗 OpenAI compatible endpoint: http://localhost:11434/v1/"
echo ""
echo "📝 Available models:"
echo "   • qwen3:30b-a3b-instruct-2507-q4_K_M - Base Qwen3 30B model"
echo "   • qwen3:200k - Qwen3 with 200K context window"
echo "   • hf.co/unsloth/gpt-oss-20b-GGUF:Q4_K_M - OpenAI's open-weight reasoning model (21B params)"
echo "   • gpt-oss:reasoning - GPT-OSS optimized with high reasoning level"

# Keep the container running
wait $OLLAMA_PID