#!/usr/bin/env python3
"""
Local LLM Cluster Controller
Uses SSH aliases: white (GPU node) + spark (fallback node)

SAFE MODE:
- Does NOT auto-install or modify remote systems
- Only executes explicit SSH commands
"""

import subprocess
import sys

# -----------------------------
# SSH NODES (YOUR CONFIG)
# -----------------------------
WHITE = "white"
SPARK = "spark"


# -----------------------------
# CORE SSH EXECUTOR
# -----------------------------
def ssh(host, cmd):
    print(f"\n[SSH {host}] $ {cmd}")
    result = subprocess.run(
        ["ssh", host, cmd],
        capture_output=True,
        text=True
    )

    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip())

    return result.stdout.strip()


# -----------------------------
# HEALTH CHECK
# -----------------------------
def health():
    print("\n🧪 CHECKING CLUSTER HEALTH")

    print("\n🖥️ WHITE (RTX 3090 node)")
    ssh(WHITE, "curl -s http://localhost:8000/v1/models || echo 'vLLM not running'")
    ssh(WHITE, "curl -s http://localhost:4000/health || echo 'LiteLLM not running'")

    print("\n⚡ SPARK (fallback node)")
    ssh(SPARK, "curl -s http://localhost:8080 || echo 'llama.cpp not running'")


# -----------------------------
# DEPLOY GUIDES (SAFE MODE)
# -----------------------------
def deploy_white():
    print("\n🖥️ WHITE DEPLOY INSTRUCTIONS")
    print("""
On WHITE (RTX 3090 machine), run manually:

1) Start vLLM:
   docker run --gpus all -p 8000:8000 \\
     vllm/vllm-openai:latest \\
     --model mistralai/Mistral-7B-Instruct-v0.2 \\
     --host 0.0.0.0 --port 8000

2) Start LiteLLM:
   litellm --config ~/llm/local/cluster/litellm/config.yaml --port 4000
""")


def deploy_spark():
    print("\n⚡ SPARK DEPLOY INSTRUCTIONS")
    print("""
On SPARK machine, run manually:

Start llama.cpp:

docker run -p 8080:8080 \\
  -v ~/llm/local/cluster/models:/models \\
  ghcr.io/ggerganov/llama.cpp:server \\
  -m /models/mistral.gguf \\
  --host 0.0.0.0 --port 8080
""")


# -----------------------------
# STATUS OVERVIEW
# -----------------------------
def status():
    print("\n📡 CLUSTER STATUS OVERVIEW")

    ssh(WHITE, "echo '--- WHITE ---'; hostname; uptime")
    ssh(SPARK, "echo '--- SPARK ---'; hostname; uptime")


# -----------------------------
# TEST API ENTRYPOINT
# -----------------------------
def test_api():
    print("\n🧠 TESTING LITE LLM ENTRYPOINT")

    ssh(WHITE, """
curl -s http://localhost:4000/v1/chat/completions \\
  -H 'Content-Type: application/json' \\
  -d '{
    "model": "gpu-primary",
    "messages": [{"role": "user", "content": "hello"}]
  }'
""")


# -----------------------------
# MAIN CLI
# -----------------------------
def main():
    if len(sys.argv) < 2:
        print("""
Usage:

  python cluster_agent.py health
  python cluster_agent.py status
  python cluster_agent.py deploy
  python cluster_agent.py deploy-white
  python cluster_agent.py deploy-spark
  python cluster_agent.py test
""")
        return

    cmd = sys.argv[1]

    if cmd == "health":
        health()

    elif cmd == "status":
        status()

    elif cmd == "deploy":
        deploy_white()
        deploy_spark()

    elif cmd == "deploy-white":
        deploy_white()

    elif cmd == "deploy-spark":
        deploy_spark()

    elif cmd == "test":
        test_api()

    else:
        print("Unknown command:", cmd)


if __name__ == "__main__":
    main()