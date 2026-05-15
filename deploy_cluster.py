import os
import json
from cloudmesh.ai.common.io import console
from cloudmesh.ai.common.Shell import Shell

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def load_state():
    if os.path.exists("cluster_state.json"):
        with open("cluster_state.json", "r") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open("cluster_state.json", "w") as f:
        json.dump(state, f, indent=2)

CONFIG = load_config()
NODES = CONFIG["nodes"]

def run_remote(host, cmd):
    """Executes a command on a remote host via SSH."""
    print(f"Executing on {host}: {cmd}")
    try:
        return Shell.run(f"ssh {host} {cmd}")
    except RuntimeError as e:
        console.error(f"Error on {host}: {e}")
        return None

def deploy_node(node_name, config, state):
    """Deploys the configuration to a specific node."""
    host = config["host"]
    
    # State Tracking: Check if deployment is needed
    current_cfg = {
        "host": host,
        "deploy_path": config.get("deploy_path"),
        "source_path": config.get("source_path")
    }
    
    if state.get(node_name) == current_cfg:
        print(f"⏭️  {node_name.upper()} is already up-to-date. Skipping...")
        return True

    if host == "uva":
        print(f"\n🚀 Special deployment for {node_name.upper()} on {host}...")
        try:
            # Run the specialized uva management script
            Shell.run(f"python3 deploy/uva/manage_uva.py")
            console.ok(f"{node_name.upper()} (uva) is up and running!")
            state[node_name] = current_cfg
            return True
        except RuntimeError as e:
            console.error(f"Specialized deployment failed for {host}: {e}")
            return False

    src = config["source_path"]
    dest = config["deploy_path"]

    print(f"\n🚀 Deploying to {node_name.upper()} ({host})...")
    
    # 1. Create remote directory
    run_remote(host, f"mkdir -p {dest}")
    
    # 2. Sync files using rsync (standard cloudmesh-ai-common pattern for file sync)
    print(f"📦 Syncing {src} to {host}:{dest}...")
    try:
        Shell.run(f"rsync -avz {src}/ {host}:{dest}/")
    except RuntimeError as e:
        console.error(f"Sync failed: {e}")
        return False

    # 3. Start containers
    print(f"⚙️  Starting containers on {host}...")
    res = run_remote(host, f"cd {dest} && docker compose up -d")
    
    if res:
        console.ok(f"{node_name.upper()} is up and running!")
        state[node_name] = current_cfg
        return True
    return False

def main():
    print("🌐 CloudMesh-AI Cluster Orchestrator")
    print("=" * 40)
    
    state = load_state()
    success_count = 0
    for node, config in NODES.items():
        if deploy_node(node, config, state):
            success_count += 1
    
    save_state(state)
    
    print("\n" + "=" * 40)
    print(f"Deployment Summary: {success_count}/{len(NODES)} nodes successful.")
    if success_count == len(NODES):
        print("🎉 Cluster is fully operational!")
    else:
        print("⚠️ Some nodes failed to deploy. Check logs above.")

if __name__ == "__main__":
    main()