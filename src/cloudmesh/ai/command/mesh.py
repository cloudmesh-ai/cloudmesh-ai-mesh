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
"""

import click
from cloudmesh.ai.common.io import console
from cloudmesh.ai.common.logging_utils import get_contextual_logger
from cloudmesh.ai.common.telemetry import Telemetry
from cloudmesh.ai.hpc.hpc import Hpc
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
        hpc = Hpc()
        
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
        hpc = Hpc()
        hpc.check()
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
        "AI Mesh Cluster\n"
        "---------------\n"
        f"Inference Server: {server}\n"
        "Primary Node: WHITE (RTX 3090)\n"
        "Fallback Node: SPARK (CPU/Lightweight GPU)\n"
        "Control Plane: LAPTOP\n"
        "API Gateway: LiteLLM (port 4000)"
    )
    console.banner("Cluster Information", info)

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