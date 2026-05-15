import sys
import json
from cloudmesh.ai.common.io import console
from cloudmesh.ai.common.Shell import Shell

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

CONFIG = load_config()

# Configuration
NODES = {name: cfg["host"] for name, cfg in CONFIG["nodes"].items()}

def usage():
    print("Usage: python3 models.py [download|list|delete] [node] [model_id]")
    print("Nodes: white, spark, both")
    print("Example: python3 models.py download white Qwen/Qwen2.5-Coder-32B-Instruct")
    sys.exit(1)

def download_model(node, model):
    target_host = NODES.get(node)
    
    if not target_host:
        console.error(f"Invalid node: {node}")
        return False

    print(f"🚀 Downloading {model} to {target_host}...")
    
    # We execute the download inside the vLLM container to ensure it's in the right volume
    # Removed -it to avoid issues with non-interactive shells
    cmd = f"ssh {target_host} 'docker exec vllm-server huggingface-cli download {model}'"
    
    try:
        Shell.run(cmd)
        console.ok(f"Successfully downloaded {model} to {target_host}")
        return True
    except RuntimeError:
        console.error(f"Failed to download {model} to {target_host}")
        return False

def main():
    if len(sys.argv) < 4:
        usage()

    command = sys.argv[1]
    node = sys.argv[2]
    model = sys.argv[3]

    if command == "download":
        if node == "both":
            for n in NODES.keys():
                download_model(n, model)
        else:
            download_model(node, model)
    else:
        usage()

if __name__ == "__main__":
    main()