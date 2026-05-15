# I have a NVIDIA Spark and a desktop with 128GB and an RTX 3090

I want to use this setup to run local LLMs for code development. Below is a detailed installation manual for setting up the system without using any paid models, ensuring everything runs locally in user mode.

## Setup Overview
With a desktop that has **128GB RAM + RTX 3090 (24GB VRAM)** plus an **NVIDIA Spark**, you can build a very capable fully-local coding assistant stack without paying for APIs. 

### Core Components:
- **Inference engine:** [llama.cpp](https://github.com/ggml-org/llama.cpp?utm_source=chatgpt.com) or [vLLM](https://github.com/vllm-project/vllm?utm_source=chatgpt.com)
- **Model manager/UI:** [Open WebUI](https://openwebui.com?utm_source=chatgpt.com)
- **IDE integration:** [Continue.dev](https://continue.dev?utm_source=chatgpt.com)
- **Embeddings/RAG:** [Ollama](https://ollama.com?utm_source=chatgpt.com) or llama.cpp server mode
- **Coding models:**
  - [Qwen]{.underline} Qwen2.5-Coder
  - [DeepSeek]{.underline} DeepSeek-Coder-V2
  - [Meta]{.underline} Llama 3.1 Instruct
  - [Mistral AI]{.underline} Codestral

You specifically said:
- No paid models
- Everything local
- No daemon/system service
- Usermode only

So this guide avoids Docker services, systemd daemons, cloud APIs, and paid inference.

## Recommended Architecture
Your hardware is ideal for this split:

| Machine          | Role                                                   |
|------------------|--------------------------------------------------------|
| RTX 3090 desktop | Main inference server                                  |
| NVIDIA Spark     | Secondary node / experimentation / embeddings / agents |

Main development workflow:
```         
VSCode / Neovim
        ↓
Continue.dev extension
        ↓
OpenAI-compatible local API
        ↓
llama.cpp server OR vLLM
        ↓
Local GGUF / AWQ models
```

## Best Models For Your Hardware

### Best Overall Coding Model

#### Qwen2.5-Coder 32B Instruct (Q4_K_M)

Runs extremely well on a 3090 with partial GPU offload.

Excellent at:
- Python
- Rust
- C++
- Typescript
- Refactoring
- Debugging
- Agents/tools

Recommended GGUF:
- Q4_K_M
- Q5_K_M if speed acceptable

Model source: [Qwen2.5-Coder on HuggingFace](https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct-GGUF?utm_source=chatgpt.com)

## Faster Secondary Model

#### DeepSeek-Coder-V2 Lite

Great autocomplete speed.

[DeepSeek Coder models](https://huggingface.co/deepseek-ai?utm_source=chatgpt.com)

## Massive Context Option

#### Llama 3.1 70B Q4

Possible because you have 128GB RAM.
Not super fast, but very usable.

## OS Recommendations
Best:
- Ubuntu 24.04 LTS

Second best:
- Arch Linux

Avoid Windows for primary inference if possible. You *can* use WSL2, but native Linux is much better for CUDA stability and performance.

## INSTALLATION GUIDE

### PART 1 — NVIDIA Drivers + CUDA

#### 1. Update System
```         
sudo apt update
sudo apt upgrade -y
```

#### 2. Install NVIDIA Drivers
Check GPU:
```         
lspci | grep -i nvidia
```
Install recommended drivers:
```         
sudo ubuntu-drivers autoinstall
```
Reboot.

Verify:
```         
nvidia-smi
```
You should see:
- RTX 3090
- VRAM
- Driver version

### PART 2 — Install CUDA Toolkit

#### Install CUDA
[CUDA Toolkit](https://developer.nvidia.com/cuda-downloads?utm_source=chatgpt.com)

For Ubuntu:
```         
sudo apt install nvidia-cuda-toolkit -y
```
Verify:
```         
nvcc --version
```

### PART 3 — Install llama.cpp

This is the most important component.

#### Clone
```         
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
```

#### Build With CUDA
```         
cmake -B build \
-DGGML_CUDA=ON
cmake --build build -j
```
Verify:
```         
./build/bin/llama-cli --help
```

### PART 4 — Download Models

Create model directory:
```         
mkdir -p ~/models
cd ~/models
```
Install huggingface downloader:
```         
pip install -U huggingface_hub
```

#### Download Qwen2.5-Coder
Example:
```         
huggingface-cli download \
Qwen/Qwen2.5-Coder-32B-Instruct-GGUF \
--include "*Q4_K_M.gguf*" \
--local-dir .
```

### PART 5 — Run Inference Server (USERMODE ONLY)

NO daemon.
NO system service.
Manual terminal launch only.

#### Launch llama.cpp OpenAI-Compatible Server
```         
cd ~/llama.cpp

./build/bin/llama-server \
  -m ~/models/qwen2.5-coder-32b-q4_k_m.gguf \
  --host 127.0.0.1 \
  --port 8080 \
  -ngl 999 \
  -c 32768
```
Explanation:

| Option   | Meaning                            |
|----------|------------------------------------|
| -m       | model                              |
| --host   | localhost only                     |
| --port   | API port                           |
| -ngl 999 | offload all layers possible to GPU |
| -c 32768 | 32k context                        |

### IMPORTANT API ROUTES
llama.cpp exposes OpenAI-compatible routes.

These are the routes you integrate into programs.

#### Base URL
```         
http://127.0.0.1:8080
```

#### ROUTE: Chat Completions
```         
POST /v1/chat/completions
```
Equivalent to OpenAI API.
Example:
```         
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

#### ROUTE: Completions
```         
POST /v1/completions
```
Legacy completion endpoint.

#### ROUTE: Embeddings
```         
POST /v1/embeddings
```
Useful for:
- Semantic search
- RAG
- Codebase indexing

#### ROUTE: Health
```         
GET /health
```

#### ROUTE: Tokenize
```         
POST /tokenize
```

### PART 6 — VSCode Integration

Install: [Continue.dev](https://continue.dev?utm_source=chatgpt.com)

#### Continue Config
Config file:
```         
~/.continue/config.json
```
Example:
```         
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
Now:
- Autocomplete
- Inline edits
- Codebase chat
- Refactors
- All local.

### PART 7 — Open WebUI (Optional)

This gives you ChatGPT-style local UI.
[Open WebUI GitHub](https://github.com/open-webui/open-webui?utm_source=chatgpt.com)
Since you do NOT want daemons:
Run manually:
```         
python -m venv venv
source venv/bin/activate

pip install open-webui
```
Launch:
```         
open-webui serve
```
Then connect:
- API URL: `http://127.0.0.1:8080`

### PART 8 — Better Performance

#### Recommended Runtime Flags
For 3090:
```         
--flash-attn
```
and
```         
--cache-type-k q8_0
--cache-type-v q8_0
```
Example:
```         
./build/bin/llama-server \
  -m model.gguf \
  -ngl 999 \
  --flash-attn \
  --cache-type-k q8_0 \
  --cache-type-v q8_0
```

### PART 9 — Multi-GPU / NVIDIA Spark Usage

If Spark has CUDA capability:
- Dedicate Spark to embeddings
- Run smaller agent models
- Run code search
- Run speech/TTS locally

Useful split:

| Device | Task                     |
|--------|--------------------------|
| 3090   | main coding LLM          |
| Spark  | embeddings / agent loops |

### PART 10 — Advanced Setup (Recommended)

Once basics work:
Install:
- [Aider](https://github.com/Aider-AI/aider?utm_source=chatgpt.com)
- [OpenHands](https://github.com/All-Hands-AI/OpenHands?utm_source=chatgpt.com)
- [TabbyML](https://tabby.tabbyml.com?utm_source=chatgpt.com)

These all support local OpenAI-compatible endpoints.

### Aider Configuration
```         
pip install aider-chat
```
Run:
```         
aider \
  --model openai/qwen \
  --openai-api-base http://127.0.0.1:8080/v1 \
  --openai-api-key local
```
This gives you:
- Repository-aware edits
- Autonomous refactoring
- Local coding agent

### Recommended Final Stack
#### Minimal Stable Setup
```         
llama.cpp
+
Qwen2.5-Coder 32B
+
Continue.dev
+
VSCode
```

#### Best Power User Setup
```         
llama.cpp
+
Open WebUI
+
Aider
+
Continue.dev
+
Qwen2.5-Coder 32B
+
DeepSeek Coder Lite
```

### Expected Performance
On RTX 3090:

| Model  | Speed        |
|--------|--------------|
| 7B     | 80–140 tok/s |
| 14B    | 40–70 tok/s  |
| 32B Q4 | 18–35 tok/s  |
| 70B Q4 | 5–10 tok/s   |

### What NOT To Use
Avoid:
- Ollama for serious tuning/control
- Docker-first setups
- systemd services
- Cloud relay UIs
- Electron-heavy wrappers

llama.cpp directly is cleaner and faster.

### Recommended Directory Layout
```         
~/ai/
├── llama.cpp/
├── models/
├── embeddings/
├── projects/
├── scripts/
└── logs/
```

### Useful Launch Script
```         
#!/bin/bash

MODEL=~/models/qwen2.5-coder-32b-q4_k_m.gguf

~/llama.cpp/build/bin/llama-server \
  -m $MODEL \
  -ngl 999 \
  --host 127.0.0.1 \
  --port 8080 \
  --flash-attn \
  -c 32768
```
Run manually whenever needed:
```         
bash start-llm.sh
```
Still usermode only. No daemon.

### PART 10 — SPARK NODE

#### On spark

Create Docker network:
```         
docker network create ai-stack
```

### Embedding Server
Run:
```         
docker run -d \
  --name embeddings \
  --gpus all \
  --network ai-stack \
  -p 8090:80 \
  ghcr.io/huggingface/text-embeddings-inference:cuda-latest \
  --model-id BAAI/bge-large-en-v1.5
```

### QDRANT VECTOR DB
```         
docker run -d \
  --name qdrant \
  --network ai-stack \
  -p 6333:6333 \
  -v ~/ai-stack/data/qdrant:/qdrant/storage \
  qdrant/qdrant
```

### Spark APIs

Embeddings:
```         
http://spark:8090/embed
```
Qdrant:
```         
http://spark:6333
```

### PART 11 — CONTINUE.DEV

Install:
- VSCode
- Continue extension

[Continue.dev Docs](https://docs.continue.dev?utm_source=chatgpt.com)

#### Continue Config
```         
{
  "models": [
    {
      "title": "Local Qwen",
      "provider": "openai",
      "model": "qwen",
      "apiBase": "http://white:4000/v1",
      "apiKey": "local"
    }
  ]
}
```

### PART 12 — AIDER

Install on laptop:
```         
pip install aider-chat
```
Run:
```         
aider \
  --model openai/qwen \
  --openai-api-base http://white:4000/v1 \
  --openai-api-key local
```

### PART 13 — USEFUL COMMANDS

#### SSH
```         
ssh white
ssh spark
```

#### Check containers
```         
docker ps
```

#### Logs
```         
docker logs llama-qwen
```

#### Restart stack
```         
docker compose restart
```

#### Stop stack
```         
docker compose down
```

### FINAL ENDPOINTS

| Service    | URL                       |
|------------|---------------------------|
| LiteLLM    | `http://white:4000/v1`    |
| llama.cpp  | `http://white:8080`       |
| llama-swap | `http://white:8082`       |
| Open WebUI | `http://white:3000`       |
| embeddings | `http://spark:8090/embed` |
| qdrant     | `http://spark:6333`       |

### RECOMMENDED NEXT STEPS

After stable deployment:
- [TabbyML](https://tabby.tabbyml.com?utm_source=chatgpt.com)
- [OpenHands](https://github.com/All-Hands-AI/OpenHands?utm_source=chatgpt.com)
- [Langfuse](https://langfuse.com?utm_source=chatgpt.com)
- [SearXNG](https://github.com/searxng/searxng?utm_source=chatgpt.com)

But get the core inference stable FIRST.

I created a downloadable control-plane package for your laptop that includes:
- Deployment scripts
- Cluster control scripts
- Docker Compose files
- LiteLLM config
- Orchestration wrapper (`ai`)
- Separate configs for `white` and `spark`

Download it here: Download the llm-local control package

After extracting on your laptop:
```         
unzip llm-local-control.zip
cd llm-local-control
```
Recommended destination:
```         
mv llm-local-control ~/llm-local
```
Then deploy:
```         
cd ~/llm-local
./control/deploy.sh
```
Then start the cluster:
```         
./control/start-all.sh
```
Or use the unified command:
```         
./control/ai start
```
Useful commands:
```         
./control/ai status
./control/ai logs white llama-qwen
./control/ai restart white llama-qwen
./control/ai stop
```
Also add that I can call the `ai` command directly without specifying the path.

After moving the package to:
```         
~/llm-local
```
Add the control directory to your shell `PATH`.