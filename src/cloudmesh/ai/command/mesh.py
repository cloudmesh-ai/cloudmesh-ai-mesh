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
    pass 

@mesh_group.group(name="router")
def router_group():
    """Manage the AI Mesh Router (LiteLLM/OpenRouter)."""
    pass

@router_group.command(name="start")
def router_start():
    """Starts the AI Mesh Router."""
    from cloudmesh.ai.mesh.router_manager import RouterManager
    try:
        telemetry.start(message="Starting AI Mesh Router")
        manager = RouterManager()
        if manager.start():
            console.ok("Router started successfully.")
        else:
            console.error("Failed to start router.")
        telemetry.complete()
    except Exception as e:
        telemetry.fail(error=str(e))
        console.error(f"Router start failed: {e}")

@router_group.command(name="stop")
def router_stop():
    """Stops the AI Mesh Router."""
    from cloudmesh.ai.mesh.router_manager import RouterManager
    try:
        telemetry.start(message="Stopping AI Mesh Router")
        manager = RouterManager()
        if manager.stop():
            console.ok("Router stopped successfully.")
        else:
            console.warn("Router was not running or could not be stopped.")
        telemetry.complete()
    except Exception as e:
        telemetry.fail(error=str(e))
        console.error(f"Router stop failed: {e}")

@router_group.command(name="restart")
def router_restart():
    """Restarts the AI Mesh Router to apply new configurations."""
    from cloudmesh.ai.mesh.router_manager import RouterManager
    try:
        telemetry.start(message="Restarting AI Mesh Router")
        manager = RouterManager()
        if manager.restart():
            console.ok("Router restarted successfully.")
        else:
            console.error("Failed to restart router.")
        telemetry.complete()
    except Exception as e:
        telemetry.fail(error=str(e))
        console.error(f"Router restart failed: {e}")

@router_group.command(name="status")
def router_status():
    """Check the status of the AI Mesh Router."""
    from cloudmesh.ai.mesh.router_manager import RouterManager
    try:
        telemetry.start(message="Checking router status")
        manager = RouterManager()
        status = manager.status()
        
        console.banner("AI Mesh Router Status", f"Host: {status['host']} Port: {status['port']}")
        
        if status["running"]:
            console.ok(f"Container: Running ({status['status_text']})")
            if status["healthy"]:
                console.ok("Health: Healthy ✓")
            else:
                console.error("Health: Unhealthy ✗")
        else:
            console.error("Container: Stopped")
            
        telemetry.complete()
    except Exception as e:
        telemetry.fail(error=str(e))
        console.error(f"Router status check failed: {e}")

@router_group.command(name="models")
def router_models():
    """List all available models in the router."""
    from cloudmesh.ai.mesh.router_manager import RouterManager
    try:
        telemetry.start(message="Listing router models")
        manager = RouterManager()
        models = manager.get_models()
        
        if not models:
            console.warning("No models found in the router config.")
        else:
            console.banner("AI Mesh Router Models", "Available model aliases")
            table_data = [[m["alias"], m["model"], m["host"], m["port"]] for m in models]
            console.table(["Alias", "Model", "Host", "Local Port"], table_data)
            
        telemetry.complete()
    except Exception as e:
        telemetry.fail(error=str(e))
        console.error(f"Failed to list models: {e}")

@router_group.command(name="test")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output during testing")
def router_test(verbose):
    """Test all available models and measure response times."""
    from cloudmesh.ai.mesh.router_manager import RouterManager
    import concurrent.futures
    try:
        telemetry.start(message="Testing router models")
        manager = RouterManager()
        models = manager.get_models()
        
        if not models:
            console.error("No models available to test.")
            telemetry.complete()
            return
        
        console.banner("AI Mesh Router Performance Test", "Measuring response times in parallel")
        
        results = []
        with console.status("Testing models in parallel...") as status:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Map each model alias to the test_model function
                future_to_model = {executor.submit(manager.test_model, m["alias"]): m["alias"] for m in models}
                
                for future in concurrent.futures.as_completed(future_to_model):
                    alias = future_to_model[future]
                    try:
                        res = future.result()
                        results.append([
                            res["model"], 
                            res["original_model"], 
                            res["port"], 
                            res["status"], 
                            res["time"], 
                            res["error"] or "-"
                        ])
                        if verbose:
                            console.print(f"  - {alias}: {res['status']} {res['time']} {'(Error: ' + res['error'] + ')' if res['error'] else ''}")
                        status.update(f"Completed: {alias}")
                    except Exception as e:
                        # We need to try and find the original model/port even on failure
                        model_info = next((m for m in models if m["alias"] == alias), {})
                        results.append([
                            alias, 
                            model_info.get("model", "Unknown"), 
                            model_info.get("port", "-"), 
                            "✗", 
                            "-", 
                            str(e)
                        ])
                        if verbose:
                            console.print(f"  - {alias}: ✗ Failed with error: {e}")
                        status.update(f"Failed: {alias}")
        
        # Sort results by alias to maintain a consistent order
        results.sort(key=lambda x: x[0])
        console.table(["Model Alias", "Model", "Port", "Status", "Time", "Error"], results)
        telemetry.complete()
    except Exception as e:
        telemetry.fail(error=str(e))
        console.error(f"Router test failed: {e}")

@mesh_group.command(name="probe")
@click.option("--hello", is_flag=True, help="Test connectivity to models with a hello message")
def probe_cmd(hello):
    """Probe server versions and models across the mesh."""
    from cloudmesh.ai.mesh.prober import MeshProber
    try:
        telemetry.start(message="Probing mesh servers")
        prober = MeshProber()
        results = prober.probe_all(hello=hello)
        
        if not results:
            console.warning("No active servers found to probe.")
        else:
            console.banner("AI Mesh Server Probe", "Current versions and available models")
            table_data = [
                [
                    r["hostname"],
                    r["host"],
                    r["enabled"],
                    r["tunnel"],
                    r["server"],
                    r["version"],
                    r["config_model"],
                    r["model_status"],
                    r["auth"],
                    r["health"],
                    r["key"],
                    r["hello"],
                    r["ports"]
                ]
                for r in results
            ]
            console.table([
                "Hostname", "Host", "Enabled", "Tunnel", "Server", "Version", 
                "Config Model", "Models", "Auth", "Health", "Key", "Hello", "Ports"
            ], table_data)
            
        telemetry.complete()
    except Exception as e:
        telemetry.fail(error=str(e))
        console.error(f"Probe failed: {e}")

@mesh_group.command(name="tunnel")
@click.argument("action", type=click.Choice(["start", "stop", "status"]))
@click.argument("host", required=False)
def tunnel_cmd(action, host):
    """Manage SSH tunnels to remote hosts in the mesh."""
    from cloudmesh.ai.mesh.tunnel_manager import TunnelManager
    try:
        telemetry.start(message=f"Managing SSH tunnels ({action})")
        tunnel_mgr = TunnelManager()
        
        if action == "start":
            if host:
                if tunnel_mgr.start(host):
                    console.ok(f"SSH tunnel started for {host}")
                else:
                    console.error(f"Failed to start SSH tunnel for {host}")
            else:
                # Start tunnels for all SSH-enabled hosts
                servers = tunnel_mgr.config_manager.get_servers_config()
                started_count = 0
                failed_hosts = []
                for hostname, details in servers.items():
                    if details.get("ssh", False):
                        if tunnel_mgr.start(hostname):
                            started_count += 1
                        else:
                            failed_hosts.append(hostname)
                
                console.ok(f"Started tunnels for {started_count} hosts")
                if failed_hosts:
                    console.error(f"Failed to start tunnels for {len(failed_hosts)} hosts: {', '.join(failed_hosts)}")
        
        elif action == "stop":
            if host:
                if tunnel_mgr.stop(host):
                    console.ok(f"SSH tunnel stopped for {host}")
                else:
                    console.error(f"Failed to stop SSH tunnel for {host}")
            else:
                # Stop all active tunnels
                active_tunnels = tunnel_mgr.list_active()
                if not active_tunnels:
                    console.info("No active tunnels found to stop.")
                else:
                    stopped_count = 0
                    failed_hosts = []
                    for hostname in active_tunnels.keys():
                        if tunnel_mgr.stop(hostname):
                            stopped_count += 1
                        else:
                            console.error(f"Failed to stop SSH tunnel for {hostname}")
                            failed_hosts.append(hostname)
                    
                    console.ok(f"Stopped tunnels for {stopped_count} hosts")
                    if failed_hosts:
                        console.error(f"Failed to stop tunnels for {len(failed_hosts)} hosts: {', '.join(failed_hosts)}")
        
        elif action == "status":
            if host:
                # Check status for specific host
                is_active = tunnel_mgr.status(host)
                if is_active:
                    console.ok(f"SSH tunnel is active for {host}")
                else:
                    console.warn(f"SSH tunnel is not active for {host}")
            else:
                # Show status for all hosts
                active_tunnels = tunnel_mgr.list_active()
                if not active_tunnels:
                    console.info("No active tunnels found.")
                else:
                    console.ok(f"Found {len(active_tunnels)} active tunnels:")
                    for hostname, tunnel_info in active_tunnels.items():
                        console.print(f"  {hostname}: Local {tunnel_info['local_port']} -> Remote {tunnel_info['remote_port']} (via {tunnel_info['ssh_host']})")
        
        telemetry.complete()
    except Exception as e:
        telemetry.fail(error=str(e))
        console.error(f"Tunnel command failed: {e}")

@mesh_group.command(name="set")
@click.argument("host", required=True)
def set_cmd(host):
    """
    Set the default host for the AI Mesh.

    Example:
        cmc mesh set white
    """
    from cloudmesh.ai.mesh.config_manager import MeshConfigManager

    try:
        telemetry.start(message=f"Setting default host to {host}")

        # Validate that the host exists in the servers configuration
        config_mgr = MeshConfigManager()
        servers = config_mgr.get_servers_config()

        if not servers or host not in servers:
            console.error(f"Hostname '{host}' not found in the servers configuration. Cannot set as default.")
            telemetry.complete()
            return

        # Set the default host in the config
        config_mgr.set_config("default", host)

        console.ok(f"Default host has been set to: {host}")
        telemetry.complete()
    except Exception as e:
        telemetry.fail(error=str(e))
        console.error(f"Failed to set default host: {e}")

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
