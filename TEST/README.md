# Local LiteLLM + Ollama Proxy on macOS

A minimal setup to run **LiteLLM** via Docker on macOS, connecting to a local **Ollama** instance (`qwen2.5:32b`) on port `4000` without authentication.

## Prerequisites
- Local Ollama running on port `11434` with your model pulled (e.g., `qwen2.5:32b`).
- Docker installed.

## Files

### 1. `litellm_config.yaml`
```yaml
model_list:
  - model_name: ollama-model
    litellm_params:
      model: ollama/qwen2.5:32b
      api_base: [http://host.docker.internal:11434](http://host.docker.internal:11434)

```

### 2. Start the Docker Container

```bash
docker run -d \
  --name litellm-proxy \
  -p 4000:4000 \
  --add-host=host.docker.internal:host-gateway \
  -v $(pwd)/litellm_config.yaml:/app/litellm_config.yaml \
  -e CONFIG_FILE_PATH=/app/litellm_config.yaml \
  ghcr.io/berriai/litellm:v1.89.4

```

### 3. Test Script (`test_litellm.sh`)

```bash
#!/bin/bash

PROXY_URL="http://localhost:4000"

echo "=== 1. Testing LiteLLM / Ollama Model List ==="
curl -s -X GET "$PROXY_URL/v1/models"
echo ""

echo "=== 2. Testing Chat Completion ('hello') ==="
curl -s -X POST "$PROXY_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ollama-model",
    "messages": [
      {"role": "user", "content": "hello"}
    ]
  }'
echo ""

```

Run the test:

```bash
chmod +x test_litellm.sh
./test_litellm.sh

```

```

```