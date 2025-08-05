# 🚀 Ollama RTX 5090 - Quick Start

Get your Qwen3 30B model running with OpenAI API compatibility in minutes!

## One-Command Deploy

```bash
cd ~/ollama-rtx5090
./run.sh
```

That's it! The script will:
- Build the optimized Docker container
- Start Ollama with RTX 5090 settings
- Pull the Qwen3 30B model
- Create the 262K context version
- Test all endpoints

## Quick Test

```bash
# Test the deployment
python3 test-api.py

# Or manual test
curl http://localhost:11434/v1/models
```

## Use with OpenAI Python Client

```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

response = client.chat.completions.create(
    model="qwen3:262k",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

## What You Get

- **Qwen3 30B Model**: Latest instruction-tuned model
- **262K Context**: Massive context window for large documents
- **RTX 5090 Optimized**: 98% VRAM usage, all layers on GPU
- **OpenAI Compatible**: Drop-in replacement for OpenAI API
- **Fast Loading**: Models cached in ~/.ollama

## Endpoints

- **OpenAI API**: `http://localhost:11434/v1/`
- **Ollama API**: `http://localhost:11434/api/`
- **Health**: `http://localhost:11434/api/health`

## Monitoring

```bash
# Watch GPU usage
watch nvidia-smi

# Container logs
docker compose logs -f ollama
```

## Stop/Start

```bash
# Stop
docker compose down

# Start
docker compose up -d

# Rebuild
docker compose up -d --build
```

That's it! You now have a production-ready Ollama deployment optimized for your RTX 5090.