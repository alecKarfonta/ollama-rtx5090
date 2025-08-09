# Ollama RTX 5090 Deployment

Standalone Ollama deployment optimized for RTX 5090 with OpenAI API compatibility.

## Quick Start

```bash
# Build and start
docker compose up -d --build

# Check status
docker compose ps
docker compose logs ollama

# Test API
curl http://localhost:11434/api/version
curl http://localhost:11434/v1/models
```

## Features

- **RTX 5090 Optimized**: 98% VRAM utilization, all layers on GPU
- **OpenAI API Compatible**: Works with OpenAI clients at `/v1/` endpoints
- **262K Context**: Qwen3 30B model with extended context length
- **Multiple Models**: Support for different context lengths
- **Persistent Storage**: Models cached in Docker volume `ollama_models`

## Models Available

After startup, the following models will be available:

1. **qwen3:200k** - Qwen3 30B with 200K context (primary model)
2. **qwen3:30b-a3b-instruct-2507-q4_K_M** - Base Qwen3 model
3. **hf.co/unsloth/gpt-oss-20b-GGUF:Q4_K_M** - OpenAI's open-weight reasoning model (21B params)
4. **gpt-oss:reasoning** - GPT-OSS optimized with high reasoning level
5. **qwen2.5-coder:14b-instruct-q4_K_M** - For coding tasks (optional)

## API Endpoints

### Ollama Native API
- **Health**: `GET http://localhost:11434/api/health`
- **Models**: `GET http://localhost:11434/api/tags`
- **Generate**: `POST http://localhost:11434/api/generate`
- **Chat**: `POST http://localhost:11434/api/chat`

### OpenAI Compatible API
- **Models**: `GET http://localhost:11434/v1/models`
- **Chat Completions**: `POST http://localhost:11434/v1/chat/completions`
- **Completions**: `POST http://localhost:11434/v1/completions`

## Usage Examples

### OpenAI Python Client
```python
import openai

# Configure client
client = openai.OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"  # Required but can be anything
)

# Chat completion with GPT-OSS reasoning model
response = client.chat.completions.create(
    model="gpt-oss:reasoning",
    messages=[
        {"role": "user", "content": "Hello! Write a simple hello world in Python and explain the reasoning behind your approach."}
    ],
    max_tokens=150
)

print(response.choices[0].message.content)
```

### cURL Examples
```bash
# List models
curl http://localhost:11434/v1/models

# Chat completion with GPT-OSS
curl -X POST http://localhost:11434/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "gpt-oss:reasoning",
        "messages": [
            {"role": "user", "content": "Solve this problem step by step: What is 15% of 240?"}
        ],
        "max_tokens": 200
    }'
```

## Model Caching & Storage

Models are automatically cached in a persistent Docker volume to avoid repeated downloads:

- **Storage Location**: Docker volume `ollama_models` 
- **Automatic Caching**: Models download once, persist across container restarts
- **Space Usage**: Large models (~12-30GB each) are cached locally

### Managing Model Cache
```bash
# View cached models and storage usage
docker compose exec ollama ollama list
docker system df -v

# Check specific volume usage
docker volume inspect ollama-rtx5090_ollama_models

# Backup models (optional)
docker run --rm -v ollama-rtx5090_ollama_models:/source -v /backup:/backup alpine tar czf /backup/ollama-models.tar.gz -C /source .

# Restore models (optional)  
docker run --rm -v ollama-rtx5090_ollama_models:/target -v /backup:/backup alpine tar xzf /backup/ollama-models.tar.gz -C /target
```

### Model Storage Benefits
- ✅ **No Re-downloads**: Models persist across container restarts
- ✅ **Fast Startup**: Skip download time on subsequent runs  
- ✅ **Space Efficient**: Each model downloaded only once
- ✅ **Version Control**: Keeps specific model versions cached

## Testing Scripts

- **`test_ollama.py`** - Comprehensive API testing
- **`test_large_context.py`** - Large context window testing

Run tests:
```bash
python3 test_ollama.py
python3 test_large_context.py
```

## Performance Tuning

The deployment is optimized for RTX 5090:

- **Memory**: Uses 98% of 32GB VRAM
- **KV Cache**: Quantized to q8_0 for speed
- **Flash Attention**: Enabled for better performance
- **GPU Layers**: All 999 layers forced to GPU
- **Single User**: Optimized for single concurrent user

## Monitoring

### GPU Usage Monitoring
**btop with GPU Support:**
```bash
# Launch btop with GPU monitoring
./launch-btop-gpu.sh

# In btop, press '5' to show/hide RTX 5090 monitoring
# Shows: GPU utilization, power draw, VRAM usage, temperature
```

**Alternative GPU monitoring:**
```bash
# NVIDIA system management interface
nvidia-smi
watch -n 1 nvidia-smi

# nvtop - dedicated GPU monitoring tool
nvtop
```

**Container logs:**
```bash
docker compose logs -f ollama
```

## Dynamic Fan Control

This deployment includes **intelligent chassis fan control** that automatically adjusts fan speeds based on **GPU power consumption** with temperature safety override.

### Features
- **Power-Based Scaling**: Immediate response to GPU load changes via power monitoring
- **Temperature Safety**: Emergency override at 70°C+ GPU temperature
- **Real-time Monitoring**: Updates every 5 seconds  
- **Responsive Control**: More immediate than temperature-based systems
- **Automatic Restoration**: Returns to motherboard control on service stop

### Power-Based Response Zones
- **Under 30W**: 💤 Minimum fans (30%) - Idle/sleep
- **30-149W**: 📈 Scale 30-40% - Light usage
- **150-299W**: ⚠️ Scale 40-60% - Medium load
- **300-449W**: 🚀 Scale 60-80% - Heavy load  
- **450-549W**: ⚡ Scale 80-100% - High power
- **550W+**: ⚡ Maximum fans (100%) - Peak performance
- **70°C+**: 🔥 **Temperature override** (100%) - Emergency cooling

### Service Management
```bash
# Check fan controller status
sudo systemctl status gpu-fan-controller.service

# View live fan control logs
sudo journalctl -u gpu-fan-controller.service -f

# Stop fan controller (returns to auto control)
sudo systemctl stop gpu-fan-controller.service

# Restart fan controller
sudo systemctl restart gpu-fan-controller.service
```

### Manual Fan Control
```bash
# Set all chassis fans to 90%
for i in {1..7}; do 
  echo 1 | sudo tee /sys/class/hwmon/hwmon4/pwm${i}_enable > /dev/null
  echo 230 | sudo tee /sys/class/hwmon/hwmon4/pwm${i} > /dev/null
done

# Return to automatic motherboard control
for i in {1..7}; do 
  echo 5 | sudo tee /sys/class/hwmon/hwmon4/pwm${i}_enable > /dev/null
done

# Check current fan speeds
sensors | grep fan
```

## Troubleshooting

### GPU Not Detected
```bash
# Check NVIDIA runtime
docker run --rm --runtime=nvidia --gpus all nvidia/cuda:11.0-base nvidia-smi

# Check container toolkit
nvidia-container-toolkit --version
```

### Out of Memory
- Reduce `OLLAMA_MAX_VRAM` value
- Reduce `GPU_MEMORY_UTILIZATION` 
- Use a smaller model or lower quantization

### Model Loading Issues
```bash
# Check available space in Docker volume
docker system df -v

# Clear model cache
docker compose down
docker volume rm ollama-rtx5090_ollama_models
docker compose up -d
```

## GPT-OSS-20B Model Card

**GPT-OSS-20B** is OpenAI's open-weight model designed for powerful reasoning, agentic tasks, and versatile developer use cases.

### Model Details
- **Parameters**: 21B total (3.6B active parameters)
- **Architecture**: Mixture-of-Experts (MoE) with native MXFP4 quantization
- **License**: Apache 2.0 (permissive, commercial-friendly)
- **Training**: Harmony response format (required for proper operation)
- **Context Length**: Up to 200K tokens (in our optimized version)

### Key Features
- **🧠 Configurable Reasoning**: Adjustable effort levels (low/medium/high)
- **🔍 Chain-of-Thought**: Full access to reasoning process for debugging
- **🛠️ Agentic Capabilities**: Native function calling, web browsing, code execution
- **⚡ RTX 5090 Optimized**: Runs efficiently within 16GB VRAM
- **🎯 Fine-tunable**: Full parameter customization for specialized use cases

### Reasoning Levels
Set reasoning level in system prompts:
- **Low**: `"Reasoning: low"` - Fast responses for general dialogue
- **Medium**: `"Reasoning: medium"` - Balanced speed and detail  
- **High**: `"Reasoning: high"` - Deep, detailed analysis (default in gpt-oss:reasoning)

### Available Variants
1. **gpt-oss:20b** - Base model from Ollama registry
2. **gpt-oss:reasoning** - Our optimized version with:
   - High reasoning level enabled by default
   - 200K context window
   - All GPU layers for maximum performance
   - RTX 5090 optimized parameters

### Use Cases
- **Complex Problem Solving**: Mathematical, logical, and analytical tasks
- **Code Generation**: With reasoning explanations
- **Research & Analysis**: Deep investigation of topics
- **Educational Content**: Step-by-step explanations
- **Agentic Applications**: Tool use and multi-step workflows

### Performance Characteristics
- **Memory Usage**: ~12-16GB VRAM (Q4_K_M quantization)
- **Speed**: Faster than larger models, optimized for real-time use
- **Quality**: High reasoning capability with transparency

### Source & Downloads
- **Original Model**: [openai/gpt-oss-20b](https://huggingface.co/openai/gpt-oss-20b)
- **GGUF Quantized**: [unsloth/gpt-oss-20b-GGUF](https://huggingface.co/unsloth/gpt-oss-20b-GGUF)
- **Ollama Command**: `ollama run hf.co/unsloth/gpt-oss-20b-GGUF:Q4_K_M`

## Model Configurations

### qwen3:200k (Primary)
- **Base**: qwen3:30b-a3b-instruct-2507-q4_K_M
- **Context**: 200,000 tokens
- **Quantization**: Q4_K_M
- **VRAM**: ~30GB

### hf.co/unsloth/gpt-oss-20b-GGUF:Q4_K_M (OpenAI Reasoning)
- **Base**: OpenAI's gpt-oss-20b from Unsloth GGUF repository
- **Parameters**: 21B total (3.6B active)
- **Context**: Default context window
- **Quantization**: Q4_K_M (GGUF)
- **VRAM**: ~12-16GB

### gpt-oss:reasoning (Optimized)
- **Base**: hf.co/unsloth/gpt-oss-20b-GGUF:Q4_K_M
- **Context**: 200,000 tokens
- **Reasoning Level**: High (configured in system prompt)
- **GPU Layers**: All layers on GPU
- **VRAM**: ~12-16GB

### Alternative Models
Edit `start.sh` to pull additional models:
```bash
# For smaller memory usage
ollama pull qwen2.5:7b-instruct-q4_K_M

# For coding tasks  
ollama pull qwen2.5-coder:14b-instruct-q4_K_M

# For larger reasoning tasks (if you have more VRAM)
ollama pull gpt-oss:120b

# Other reasoning models
ollama pull llama3.3:70b-instruct-q4_K_M
```

## Security Notes

- **Local only**: Binds to all interfaces but should be behind firewall
- **No authentication**: Consider adding reverse proxy with auth for production
- **File access**: Container has access to `~/.ollama` directory

## Next Steps

1. **Add Authentication**: Use Caddy or nginx for API key auth
2. **Add Monitoring**: Prometheus metrics for GPU/model usage
3. **Load Balancing**: Multiple instances for high availability
4. **Custom Models**: Add your own fine-tuned models