# Cloudmesh AI Mesh

**Quick Links:**
- [API Reference](API.md) - Full technical documentation of all modules.

Cloudmesh AI Mesh is a management layer for a local AI development cluster. The system operates entirely offline, ensuring that all data and inference remain within the local network.

## Cluster Architecture

The cluster consists of three primary components:

### 1. WHITE (Primary Compute Node)
- **Hardware**: RTX 3090 GPU, 128GB RAM.
- **Services**:
    - **vLLM**: High-performance GPU inference server.
    - **LiteLLM**: OpenAI-compatible API gateway (port 4000) that routes requests to available backends.

### 2. SPARK (Fallback Node)
- **Hardware**: CPU / Lightweight GPU.
- **Services**:
    - **llama.cpp**: Inference server (port 8080) for GGUF quantized models.
    - **Model Management**: Supports optional on-demand loading and unloading of GGUF models to optimize memory usage.

### 3. LAPTOP (Control Plane)
- **Services**:
    - **VSCode**: Development environment with AI extensions.
    - **SSH Orchestration**: Tools for managing remote nodes.
    - **AI Agent**: Python-based cluster management agent.

## API and Routing

### Core Entrypoint
All applications connect to the cluster via the LiteLLM gateway:
`http://localhost:4000/v1/chat/completions`

### Routing Logic
LiteLLM manages request distribution based on task requirements and node availability:
- **High Performance**: Requests are routed to WHITE (vLLM).
- **Fallback**: If WHITE is unavailable, requests are routed to SPARK (llama.cpp).
- **Task-Specific Routing**:
    - Coding tasks $\rightarrow$ Coding-specific models (e.g., DeepSeek Coder).
    - Reasoning tasks $\rightarrow$ Llama 3 class models.
    - Autocomplete $\rightarrow$ Small Mistral models.

## Command Line Interface

The cluster is managed via the `cmc mesh` command group.

### Available Commands

#### `cmc mesh status`
Displays the current GPU utilization and availability across all cluster nodes. It provides a table including node name, partition, state, and available vs. total GPUs.

#### `cmc mesh health`
Executes a diagnostic check of the environment, verifying:
- VPN connectivity to the HPC environment.
- SSH access to the compute nodes.
- Disk quota availability.

#### `cmc mesh info`
Displays the static configuration and architecture of the AI Mesh cluster.

## Installation and Setup

### Compute Node Setup (WHITE)

#### NVIDIA Drivers and CUDA
1. **Update System**:
   ```bash
   docker run --rm -it ubuntu:latest /bin/bash -c "apt-get update && apt-get upgrade -y"
   ```
2. **Install Drivers**:
   ```bash
   docker run --rm -it nvidia/cuda:11.0-base /bin/bash -c "nvidia-smi && apt-get update && apt-get install -y nvidia-driver-460"
   ```
3. **Install CUDA Toolkit**:
   ```bash
   docker run --rm -it nvidia/cuda:11.0-base /bin/bash -c "apt-get update && apt-get install -y nvidia-cuda-toolkit"
   ```

#### Inference Server (llama.cpp)
To avoid manual compilation, the inference server is deployed using a Docker container.

1. **Model Deployment**:
   Use `huggingface-cli` to download GGUF models to the local `~/models` directory.
2. **Execution**:
   Run the server using the pre-built Docker image:
   ```bash
   docker run -d --name llama-server \
     -v ~/models:/models \
     local/llama-cpp:latest \
     ./build/bin/llama-server \
       -m /models/qwen2.5-coder-32b-q4_k_m.gguf \
       --host 127.0.0.1 \
       --port 8080 \
       -ngl 999 \
       -c 32768
   ```

### Client Integration (LAPTOP)

#### VSCode Configuration
Install the `Continue.dev` extension and configure the model provider:
```json
{
  "models": [
    {
      "title": "Qwen Local",
      "provider": "openai",
      "model": "qwen",
      "apiBase": "http://127.0.0.1:8080/v1",
      "apiKey": "local"
    }
  ]
}
```

## Operational Constraints

- **Local Only**: No external API calls or internet-based inference are permitted.
- **Explicit Execution**: All system-level changes must be performed manually via explicit commands.
- **Node Specification**: Every command must specify the target machine (WHITE, SPARK, or LAPTOP).