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
- **Persistent Storage**: Models stored in `~/.ollama`

## Models Available

After startup, the following models will be available:

1. **qwen3:262k** - Qwen3 30B with 262K context (main model)
2. **qwen3:30b-a3b-instruct-2507-q4_K_M** - Base model
3. **qwen2.5-coder:14b-instruct-q4_K_M** - For 128K context (optional)

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

# Chat completion
response = client.chat.completions.create(
    model="qwen3:262k",
    messages=[
        {"role": "user", "content": "Hello! Write a simple hello world in Python."}
    ],
    max_tokens=150
)

print(response.choices[0].message.content)
```

### cURL Examples
```bash
# List models
curl http://localhost:11434/v1/models

# Chat completion
curl -X POST http://localhost:11434/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "qwen3:262k",
        "messages": [
            {"role": "user", "content": "Hello! Write a simple hello world in Python."}
        ],
        "max_tokens": 150
    }'
```

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

Check GPU usage:
```bash
nvidia-smi
watch -n 1 nvidia-smi
```

Check container logs:
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
# Check available space
df -h ~/.ollama

# Clear model cache
docker compose down
sudo rm -rf ~/.ollama/models/*
docker compose up -d
```

## Model Configurations

### qwen3:262k (Primary)
- **Base**: qwen3:30b-a3b-instruct-2507-q4_K_M
- **Context**: 262,000 tokens
- **Quantization**: Q4_K_M
- **VRAM**: ~30GB

### Alternative Models
Edit `start.sh` to pull different models:
```bash
# For smaller memory usage
ollama pull qwen2.5:7b-instruct-q4_K_M

# For coding tasks
ollama pull qwen2.5-coder:14b-instruct-q4_K_M
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