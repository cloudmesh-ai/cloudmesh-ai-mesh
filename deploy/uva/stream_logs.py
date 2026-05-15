import sys
import json
from cloudmesh.ai.common.io import console
from cloudmesh.ai.common.Shell import Shell

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def stream_logs():
    config = load_config()
    host = "uva"
    # Assuming logs are in the deploy path specified in config
    # We use the first node's deploy path as a reference for the uva machine
    deploy_path = next(iter(config["nodes"].values()))["deploy_path"]
    log_file = f"{deploy_path}/vllm.log"
    
    console.ok(f"Streaming logs from {host}:{log_file}...")
    
    # Use Shell.live to stream the output of tail -f
    cmd = f"ssh {host} 'tail -f {log_file}'"
    try:
        Shell.live(cmd)
    except KeyboardInterrupt:
        print("\nStopping log stream.")
    except Exception as e:
        console.error(f"Failed to stream logs: {e}")

if __name__ == "__main__":
    stream_logs()