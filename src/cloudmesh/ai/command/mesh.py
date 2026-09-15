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
@mesh_group.command(name="claude")
def claude_cmd():
    """
    Start Claude AI.
    """
    import subprocess
    import os
    from cloudmesh.ai.common.io import console

    try:
        telemetry.start(message="Starting Claude AI")
        
        # Environment variables as defined in bin/start-claude
        env = os.environ.copy()
        env["ANTHROPIC_API_KEY"] = "fake-key-local-only"
        env["ANTHROPIC_BASE_URL"] = "http://localhost:11434/v1"
        
        # Command as defined in bin/start-claude
        cmd = ["claude", "--model", "qwen3-coder"]
        
        console.info(f"Executing: {' '.join(cmd)}")
        
        # Run the command and pipe output to the current terminal
        subprocess.run(cmd, env=env, check=True)
        
        telemetry.complete()
    except subprocess.CalledProcessError as e:
        telemetry.fail(error=str(e))
        console.error(f"Claude failed to start: {e}")
    except Exception as e:
        telemetry.fail(error=str(e))
        console.error(f"Error starting Claude: {e}")

    from cloudmesh.ai.mesh.manager import MeshManager
    from cloudmesh.ai.mesh.config_manager import MeshConfigManager

    manager = MeshManager()
    info = manager.get_cluster_info()

    # Get configuration details including ports
    config_mgr = MeshConfigManager()
    servers = config_mgr.get_servers_config()

    # Build the main cluster info
    info_str = (
        f"AI Mesh Cluster\n"
        f"---------------\n"
        f"Inference Server: {info['inference_server']}\n"
        f"Primary Node: {info['primary_node']}\n"
        f"Fallback Node: {info['fallback_node']}\n"
        f"Control Plane: {info['control_plane']}\n"
        f"API Gateway: {info['api_gateway']}")

    console.banner("Cluster Information", info_str)

    # Show port configuration if available
    if servers:
        console.banner("Port Configuration", "Hosts with their local and remote ports")
        table_data = []
        for host, details in servers.items():
            server_type = details.get("server", "unknown")
            ssh_enabled = details.get("ssh", False)

            # Get port information
            ports = details.get("port", {})
            local_port = ports.get("local", "Not configured")
            remote_port = ports.get("remote", "Not configured")

            table_data.append([
                host,
                server_type,
                f"Local: {local_port}",
                f"Remote: {remote_port}",
                "SSH" if ssh_enabled else "-"
            ])

        console.table(
            ["Host", "Server", "Local Port", "Remote Port", "SSH"],
            table_data
        )

@mesh_group.command(name="probe")
@click.option("--hello", is_flag=True, help="Send 'hello' to LLMs and measure response time")
def probe_cmd(hello):
    """
    Probe the versions of inference servers across the mesh.
    """
    from cloudmesh.ai.mesh.prober import MeshProber

    try:
        telemetry.start(message="Probing server versions")

        prober = MeshProber()

        with console.status("Probing servers..."):
            results = prober.probe_all(hello=hello)

        if not results:
            console.error("No servers probed or no servers configured in mesh config.")
            telemetry.complete()
            return

        headers = ["Host", "On", "Server", "Version", "Config Model", "Models", "Auth", "Health", "Key"]
        if hello:
            headers.append("Hello")
        headers.append("Ports")

        table_data = []
        for r in results:
            row = [r["host"], r.get("on", "-"), r["server"], r["version"], r["config_model"], r["model_status"], r["auth"], r["health"], r["key"]]
            if hello:
                row.append(r.get("hello", "-"))
            row.append(r["ports"])
            table_data.append(row)

        console.banner("Mesh Server Probe", "Inference server versions and models across nodes")
        console.table(headers, table_data)

        telemetry.complete()
    except Exception as e:
        telemetry.fail(error=str(e))
        console.error(f"Probe failed: {e}")

@mesh_group.command(name="tunnel")
@click.argument("action", required=True, type=click.Choice(["start", "stop", "status"]))
@click.argument("host", required=False)
def tunnel_cmd(action, host):
    """
    Manage SSH tunnels for hosts in the mesh.

    ACTION: start, stop, or status
    HOST: The hostname defined in config.yaml (optional for 'start' and 'stop')
    """
    from cloudmesh.ai.mesh.tunnel_manager import TunnelManager
    from cloudmesh.ai.mesh.config_manager import MeshConfigManager

    try:
        telemetry.start(message=f"SSH tunnel {action} command")

        config_mgr = MeshConfigManager()
        servers = config_mgr.get_servers_config()

        if not servers:
            console.error("No servers found in configuration.")
            telemetry.complete()
            return

        tunnel_mgr = TunnelManager()

        # Handle different actions
        if action == "start":
            if host:
                # Start tunnel for specific host
                if host not in servers:
                    console.error(f"Hostname '{host}' not found in configuration.")
                    telemetry.complete()
                    return

                server_cfg = servers[host]
                if not server_cfg.get("ssh", False):
                    console.error(f"SSH is not enabled for host '{host}' in configuration.")
                    telemetry.complete()
                    return

                if tunnel_mgr.start(host):
                    console.ok(f"SSH tunnel started successfully for {host}")
                    console.print(f"Local port: {server_cfg['port'].get('local')}")
                    console.print(f"Remote port: {server_cfg['port'].get('remote')}")
                    console.print(f"Target host: {host}")
                else:
                    console.error(f"Failed to start SSH tunnel for {host}")
                    telemetry.fail()
            else:
                # Start tunnels for all SSH-enabled hosts
                started_count = 0
                failed_hosts = []

                for hostname, server_cfg in servers.items():
                    if server_cfg.get("ssh", False):
                        if tunnel_mgr.start(hostname):
                            console.ok(f"SSH tunnel started successfully for {hostname}")
                            started_count += 1
                        else:
                            console.error(f"Failed to start SSH tunnel for {hostname}")
                            failed_hosts.append(hostname)

                if started_count > 0:
                    console.ok(f"Started tunnels for {started_count} hosts")
                if failed_hosts:
                    console.error(f"Failed to start tunnels for {len(failed_hosts)} hosts: {', '.join(failed_hosts)}")

        elif action == "stop":
            if host:
                # Stop tunnel for specific host
                if tunnel_mgr.stop(host):
                    console.ok(f"SSH tunnel stopped successfully for {host}")
                else:
                    console.error(f"Failed to stop SSH tunnel for {host}")
            else:
                # Stop tunnels for all active hosts
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
