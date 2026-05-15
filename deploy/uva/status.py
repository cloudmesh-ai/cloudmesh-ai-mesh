import re
import sys
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from cloudmesh.ai.common.io import console
from cloudmesh.ai.common.Shell import Shell

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

CONFIG = load_config()
# Configuration
NODES = [CONFIG["uva"]["slurm_node"]]

def run_command(cmd):
    """Executes a shell command and returns the output."""
    try:
        return Shell.run(cmd)
    except RuntimeError:
        # We return None to indicate failure for a specific call
        return None

def gather_node_data(node):
    """Gathers SLURM data for a specific node and returns it as a dictionary."""
    data = {"node": node, "resources": {}, "active_jobs": [], "error": None}
    
    node_info = run_command(f"scontrol show node {node}")
    if not node_info:
        data["error"] = f"Could not retrieve info for node {node}"
        return data

    def extract(pattern, text):
        match = re.search(pattern, text)
        return int(match.group(1)) if match else 0

    # Resource Gathering
    cfg_cpu = extract(r'CPUTot=(\d+)', node_info)
    cfg_mem = extract(r'RealMemory=(\d+)', node_info)
    cfg_gpu_match = re.search(r'Gres=.*gpu.*?:\s*(\d+)', node_info)
    cfg_gpu = int(cfg_gpu_match.group(1)) if cfg_gpu_match else 0

    alloc_cpu = extract(r'CPUAlloc=(\d+)', node_info)
    alloc_mem = extract(r'AllocMem=(\d+)', node_info)
    alloc_gpu_match = re.search(r'AllocTRES=.*gres/gpu=(\d+)', node_info)
    alloc_gpu = int(alloc_gpu_match.group(1)) if alloc_gpu_match else 0

    data["resources"] = {
        "cpu": {"total": cfg_cpu, "used": alloc_cpu, "free": cfg_cpu - alloc_cpu},
        "mem_mb": {"total": cfg_mem, "used": alloc_mem, "free": cfg_mem - alloc_mem},
        "gpu": {"total": cfg_gpu, "used": alloc_gpu, "free": cfg_gpu - alloc_gpu}
    }

    # Active Jobs Gathering
    jobs_output = run_command(f"squeue -w {node} -h -o '%i %u %t %M %C %m %b'")
    if jobs_output:
        for line in jobs_output.strip().split('\n'):
            parts = line.split()
            if len(parts) >= 7:
                data["active_jobs"].append({
                    "jobid": parts[0], "user": parts[1], "state": parts[2],
                    "time": parts[3], "cpus": parts[4], "mem": parts[5], "gres": parts[6]
                })
    
    return data

def gather_pending_jobs():
    """Gathers pending jobs from the queue."""
    pending_output = run_command("squeue -t PD -o '%.10i %.12u %.5t %.10M %.20R'")
    if not pending_output:
        return []
    
    lines = pending_output.strip().split('\n')
    # Skip header and take top 10
    jobs = []
    for line in lines[1:11]:
        jobs.append(line)
    return jobs

def print_report(full_data):
    """Special print method that takes the gathered JSON data and prints the report."""
    nodes_data = full_data.get("nodes", {})
    pending_jobs = full_data.get("pending_jobs", [])

    for node, data in nodes_data.items():
        if data.get("error"):
            console.error(f"Node {node}: {data['error']}")
            continue

        print("======================================")
        print(f" SLURM NODE REPORT: {node}")
        print("======================================")

        res = data["resources"]
        print("\n---- RESOURCE SUMMARY ----")
        print(f"CPUs:   used={res['cpu']['used']} / total={res['cpu']['total']} / free={res['cpu']['free']}")
        print(f"Mem:    used={res['mem_mb']['used'] // 1024}GB / total={res['mem_mb']['total'] // 1024}GB / free={res['mem_mb']['free'] // 1024}GB")
        print(f"GPUs:   used={res['gpu']['used']} / total={res['gpu']['total']} / free={res['gpu']['free']}")

        print("\n---- ACTIVE JOBS & RESOURCE ALLOCATION ----")
        print(f"{'JOBID':<10} {'USER':<12} {'ST':<5} {'TIME':<10} {'CPUS':<5} {'MEM':<10} {'GRES':<15}")
        print("-" * 66)
        for job in data["active_jobs"]:
            print(f"{job['jobid']:<10} {job['user']:<12} {job['state']:<5} {job['time']:<10} {job['cpus']:<5} {job['mem']:<10} {job['gres']:<15}")

    if pending_jobs:
        print("\n---- PENDING JOBS (Top 10) ----")
        for job in pending_jobs:
            print(job)
    
    print("\n")

def main():
    # Parallel gathering with a barrier (merge)
    final_json = {"nodes": {}, "pending_jobs": []}
    
    with ThreadPoolExecutor() as executor:
        # Parallel callouts to nodes
        future_to_node = {executor.submit(gather_node_data, node): node for node in NODES}
        # Parallel callout for pending jobs
        future_pending = executor.submit(gather_pending_jobs)
        
        for future in as_completed(future_to_node):
            node = future_to_node[future]
            try:
                final_json["nodes"][node] = future.result()
            except Exception as e:
                final_json["nodes"][node] = {"error": str(e)}
        
        try:
            final_json["pending_jobs"] = future_pending.result()
        except Exception as e:
            console.error(f"Failed to gather pending jobs: {e}")

    # Print the final merged data
    print_report(final_json)

if __name__ == "__main__":
    main()
