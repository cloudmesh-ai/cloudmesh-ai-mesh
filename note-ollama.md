# Using Ollama for Local LLM Development

## Overview
Ollama is a tool that can be used for embeddings and RAG (Retrieval-Augmented Generation) tasks. It offers an alternative to using llama.cpp server mode, providing additional functionality and flexibility.

## Installation and Setup

### 1. Install Ollama
To install Ollama, you can follow these steps:

1. **Update System:**
    ```bash
    sudo apt update
    sudo apt upgrade -y
    ```

2. **Install Ollama CLI:**
    ```bash
    curl -sSf https://get.ollama.com | sh
    ```

3. **Verify Installation:**
    ```bash
    ollama --version
    ```

### 2. Configure Ollama for Local Use

1. **Create a Configuration File:**
    ```bash
    mkdir -p ~/ollama/config
    nano ~/ollama/config/config.yaml
    ```
    Add the following configuration:
    ```yaml
    models:
      - name: qwen2.5-coder
        path: ~/models/qwen2.5-coder-32b-q4_k_m.gguf
    ```

2. **Run Ollama Server:**
    ```bash
    ollama serve --config ~/ollama/config/config.yaml
    ```

## API Endpoints

### 1. Chat Completions
```bash
curl http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "messages": [
      {
        "role": "user",
        "content": "Write a Rust HTTP server"
      }
    ],
    "temperature": 0.2
  }'
```

### 2. Completions
```bash
curl http://127.0.0.1:8080/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "prompt": "Write a Rust HTTP server",
    "temperature": 0.2
  }'
```

### 3. Embeddings
```bash
curl http://127.0.0.1:8080/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "input": ["Write a Rust HTTP server"]
  }'