"""
Cloudmesh AI Mesh Extension
===========================

This extension provides tools to manage and monitor the local AI development cluster.
It integrates with ai-hpc to provide real-time visibility into compute resources.

Usage Examples:
-------------------------------------------------------------------------------
1. Check the GPU status of the cluster:
   $ cmc mesh status

2. Perform a health check of the HPC environment:
   $ cmc mesh health

3. Get general cluster information:
   $ cmc mesh info

4. Probe server versions and models across the mesh:
   $ cmc mesh probe
"""

import click
from cloudmesh.ai.common.io import console
from cloudmesh.ai.common.logging_utils import get_contextual_logger
from cloudmesh.ai.common.telemetry import Telemetry
from cloudmesh.ai.mesh.config import config

# Initialize Logger
logger = get_contextual_logger("mesh")

# Initialize Telemetry
telemetry = Telemetry("mesh")

@click.group(name="mesh")
def mesh_group():
    """
    AI Mesh tool for managing the local AI development cluster.
    
    This group provides commands to monitor GPU availability and verify 
    the health of the compute nodes.
    """
    pass

@mesh_group.command(name="status")
def status_cmd():
    """
    Check the GPU status and availability across the AI cluster.
    """
    try:
        telemetry.start(message="Checking cluster GPU status")
        
        try:
            from cloudmesh.ai.hpc.hpc import Hpc
            hpc = Hpc()
        except ImportError:
            console.warning("GPU status check currently requires ai-hpc package.")
            telemetry.complete()
            return

        with console.status("Fetching real-time GPU usage from cluster..."):
            usage = hpc.get_cluster_gpu_usage()
            
        if not usage:
            console.warning("No GPU usage data available.")
            return

        # Prepare data for table
        table_data = []
        for node in usage:
            table_data.append([
                node["node"],
                node["partition"],
                node["state"],
                f"{node['available']}/{node['total']}",
                node["used"]
            ])

        console.banner("AI Cluster GPU Status", "Real-time availability across nodes")
        console.table(
            ["Node", "Partition", "State", "Avail/Total", "Used"], 
            table_data
        )
        
        telemetry.complete()
    except Exception as e:
        telemetry.fail(error=str(e))
        console.error(f"Failed to get cluster status: {e}")

@mesh_group.command(name="health")
def health_cmd():
    """
    Perform a health check of the HPC environment (VPN, SSH, Quota).
    """
    try:
        telemetry.start(message="Running cluster health check")
        
        try:
            from cloudmesh.ai.hpc.hpc import Hpc
            hpc = Hpc()
            hpc.check()
        except ImportError:
            console.warning("Health check logic currently requires ai-hpc package.")
            telemetry.complete()
            return
        
        telemetry.complete()
    except Exception as e:
        telemetry.fail(error=str(e))
        console.error(f"Health check failed: {e}")

@mesh_group.command(name="info")
def info_cmd():
    """
    Display general information about the AI Mesh cluster.
    """
    server = config.get("cloudmesh.ai.mesh.servers.inference.server")
    info = (
        "AI Mesh Cluster\\n"
        "---------------\\n"
        f"Inference Server: {server}\\n"
        "Primary Node: WHITE (RTX 3090)\\n"
        "Fallback Node: SPARK (CPU/Lightweight GPU)\\n"
        "Control Plane: LAPTOP\\n"
        "API Gateway: LiteLLM (port 4000)")
    console.banner("Cluster Information", info)

@mesh_group.command(name="probe")
def probe_cmd():
    """
    Probe the versions of inference servers across the mesh.
    """
    from cloudmesh.ai.mesh.servers import OllamaServer, VllmServer
    
    try:
        telemetry.start(message="Probing server versions")
        
        # Defined nodes to probe based on the expected output
        nodes_to_probe = [
            {"host": "localhost", "server": "ollama", "port": 11434, "proxy_port": 11434, "model": "qwen2.5:32b", "auth": "-"},
            {"host": "white", "server": "ollama", "port": 11434, "proxy_port": 11000, "model": "qwen2.5:32b", "auth": "-"},
            {"host": "spark", "server": "ollama", "port": 11434, "proxy_port": 11002, "model": "qwen2.5:32b", "auth": "-"},
            {"host": "uva", "server": "vllm", "port": 17704, "proxy_port": 17704, "model": "google/gemma-4-31B-it", "auth": "File"},
        ]
        
        table_data = []
        
        with console.status("Probing servers..."):
            for node in nodes_to_probe:
                host = node["host"]
                server_type = node["server"]
                port = node["port"]
                proxy_port = node["proxy_port"]
                target_model = node["model"]
                auth_type = node["auth"]
                
                if server_type == "ollama":
                    server = OllamaServer(host, port, "ollama")
                elif server_type == "vllm":
                    server = VllmServer(host, port, "vllm")
                else:
                    continue
                
                result = server.probe()
                
                # Format models column
                model_status = server.check_model(target_model, result["models"])
                
                # Format ports column
                ports_str = f"S:{port}/P:{proxy_port}"
                
                table_data.append([
                    host, 
                    server_type, 
                    result["version"], 
                    model_status, 
                    auth_type, 
                    ports_str
                ])
        
        console.banner("Mesh Server Probe", "Inference server versions and models across nodes")
        console.table(
            ["Host", "Server", "Version", "Models", "Auth", "Ports"], 
            table_data
        )
        
        telemetry.complete()
    except Exception as e:
        telemetry.fail(error=str(e))
        console.error(f"Probe failed: {e}")

@mesh_group.command(name="config")
@click.argument("key", required=False)
@click.argument("value", required=False)
def config_cmd(key, value):
    """
    Get or set the cluster configuration.
    
    Example:
        cmc mesh config inference.server ollama
        cmc mesh config inference.server
    """
    if not key:
        console.error("Key is required.")
        return

    # Map short keys to full nested paths for convenience
    full_key = key
    if key == "inference.server":
        full_key = "cloudmesh.ai.mesh.servers.inference.server"
    elif key == "inference.port":
        full_key = "cloudmesh.ai.mesh.servers.inference.port"

    if value:
        try:
            config.set(full_key, value)
            config.save()
            console.ok(f"Set {full_key} to {value}")
        except Exception as e:
            console.error(f"Failed to set config: {e}")
    else:
        val = config.get(full_key)
        console.print(f"{full_key}: {val}")

def register(cli):
    """Registers the mesh command group to the main CLI."""
    cli.add_command(mesh_group, name="mesh")
