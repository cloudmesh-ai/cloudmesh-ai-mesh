#!/bin/bash

PROXY_URL="http://localhost:4000"

echo "=== 1. Testing LiteLLM Model List ==="
curl -s -X GET "$PROXY_URL/v1/models"
echo -e "\n"

echo "=== 2. Testing Chat Completion for: qwen2.5-32b ==="
curl -s -X POST "$PROXY_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-32b",
    "messages": [
      {"role": "user", "content": "hello"}
    ]
  }'
echo -e "\n"