import time
import sys
import requests
import json

from cloudmesh.ai.common.io import console
from cloudmesh.ai.common.Shell import Shell

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

CONFIG = load_config()
HOST = "uva"
PORT = CONFIG["uva"]["vllm_port"]
MODEL_NAME = CONFIG["uva"]["model_name"]


def start_vllm():
    """Starts vLLM using the cmc command locally."""
    print(f"🚀 Starting vLLM: {MODEL_NAME} on port {PORT}...")
    cmd = f"cmc llm start {MODEL_NAME} --port {PORT}"
    try:
        # Execute cmc locally as it communicates with the remote node via API
        Shell.run(cmd)
        console.ok("Start command issued via cmc.")
        return True
    except RuntimeError as e:
        console.error(f"cmc command failed: {e}")
        return False


def probe_readiness():
    """Probes the vLLM service via API call to localhost using requests."""
    url = f"http://localhost:{PORT}/health"
    print(f"⏳ Waiting for vLLM to be ready at {url} (this may take >100s)...")
    timeout = 300  # 5 minutes
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                console.ok("vLLM is ready!")
                return True
        except requests.RequestException:
            pass
        
        print(".", end="", flush=True)
        time.sleep(5)
    
    console.error("Timeout waiting for vLLM readiness.")
    return False


def main():
    # Resource check removed as it requires SSH login which is blocked by firewall

    if not start_vllm():
        console.error("Failed to start vLLM.")
        sys.exit(1)
    
    if not probe_readiness():
        console.error("vLLM failed to become ready.")
        sys.exit(1)

    print("\n🎉 uva node is fully operational!")


if __name__ == "__main__":
    main()
