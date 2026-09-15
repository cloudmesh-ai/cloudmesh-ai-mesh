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
    from cloudmesh.ai.mesh.manager import MeshManager
    try:
        telemetry.start(message="Checking cluster GPU status")
        manager = MeshManager()
        
        with console.status("Fetching real-time GPU usage from cluster..."):
            usage = manager.get_gpu_status()
            
        if not usage:
            console.warning("No GPU usage data available.")
            telemetry.complete()
            return

        table_data = [
            [n["node"], n["partition"], n["state"], f"{n['available']}/{n['total']}", n["used"]]
            for n in usage
        ]

        console.banner("AI Cluster GPU Status", "Real-time availability across nodes")
        console.table(["Node", "Partition", "State", "Avail/Total", "Used"], table_data)
        telemetry.complete()
    except ImportError as e:
        console.warning(str(e))
        telemetry.complete()
    except Exception as e:
        telemetry.fail(error=str(e))
        console.error(f"Failed to get cluster status: {e}")

@mesh_group.command(name="health")
def health_cmd():
    """
    Perform a health check of the HPC environment (VPN, SSH, Quota).
    """
    from cloudmesh.ai.mesh.manager import MeshManager
    try:
        telemetry.start(message="Running cluster health check")
        manager = MeshManager()
        manager.run_health_check()
        telemetry.complete()
    except ImportError as e:
        console.warning(str(e))
        telemetry.complete()
    except Exception as e:
        telemetry.fail(error=str(e))
        console.error(f"Health check failed: {e}")

@mesh_group.command(name="info")
def info_cmd():
    """
    Display general information about the AI Mesh cluster.
    """
    from cloudmesh.ai.mesh.manager import MeshManager
    manager = MeshManager()
    info = manager.get_cluster_info()
    
    info_str = (
        f"AI Mesh Cluster\\\\n"
        f"---------------\\n"
        f"Inference Server: {info['inference_server']}\\\\n"
        f"Primary Node: {info['primary_node']}\\\\n"
        f"Fallback Node: {info['fallback_node']}\\\\n"
        f"Control Plane: {info['control_plane']}\\\\n"
        f"API Gateway: {info['api_gateway']}")
    
    console.banner("Cluster Information", info_str)

@mesh_group.command(name="probe")
def probe_cmd():
    """
    Probe the versions of inference servers across the mesh.
    """
    from cloudmesh.ai.mesh.prober import MeshProber
    
    try:
        telemetry.start(message="Probing server versions")
        
        prober = MeshProber()
        
        with console.status("Probing servers..."):
            results = prober.probe_all()
        
        if not results:
            console.error("No servers probed or no servers configured in mesh config.")
            telemetry.complete()
            return

        table_data = [
            [r["host"], r["server"], r["version"], r["config_model"], r["model_status"], r["auth"], r["ports"]]
            for r in results
        ]
        
        console.banner("Mesh Server Probe", "Inference server versions and models across nodes")
        console.table(
            ["Host", "Server", "Version", "Config Model", "Models", "Auth", "Ports"], 
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
    from cloudmesh.ai.mesh.config_manager import MeshConfigManager
    
    if not key:
        console.error("Key is required.")
        return
    
    config_mgr = MeshConfigManager()
    
    if value:
        try:
            config_mgr.set_config(key, value)
            console.ok(f"Set {key} to {value}")
        except Exception as e:
            console.error(f"Failed to set config: {e}")
    else:
        val = config_mgr.get_config(key)
        console.print(f"{key}: {val}")

def register(cli):
    """Registers the mesh command group to the main CLI."""
    cli.add_command(mesh_group, name="mesh")
