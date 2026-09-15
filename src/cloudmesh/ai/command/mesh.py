# ... [previous content] ...

@mesh_group.command(name="port")
@click.argument("host", required=True)
def port_cmd(host):
    """
    Set the local port for the specified host to match its configured remote port.

    HOST: The hostname defined in config.yaml
    """
    from cloudmesh.ai.mesh.config_manager import MeshConfigManager
    from cloudmesh.ai.mesh.tunnel_manager import TunnelManager

    try:
        telemetry.start(message=f"Setting local port for {host}")

        # Validate that the host exists in configuration
        config_mgr = MeshConfigManager()
        servers = config_mgr.get_servers_config()

        if not servers or host not in servers:
            console.error(f"Hostname '{host}' not found in configuration.")
            telemetry.complete()
            return

        server_cfg = servers[host]

        # Get the port configuration
        ports = server_cfg.get("port", {})
        remote_port = ports.get("remote")

        if not remote_port:
            console.error(f"No remote port configured for host '{host}' in configuration.")
            telemetry.complete()
            return

        # Update the local port to match the remote port
        try:
            # Get current config data
            config_data = config_mgr.config.data

            # Navigate to the server configuration
            if "cloudmesh" not in config_data:
                config_data["cloudmesh"] = {}
            if "ai" not in config_data["cloudmesh"]:
                config_data["cloudmesh"]["ai"] = {}
            if "mesh" not in config_data["cloudmesh"]["ai"]:
                config_data["cloudmesh"]["ai"]["mesh"] = {}
            if "servers" not in config_data["cloudmesh"]["ai"]["mesh"]:
                config_data["cloudmesh"]["ai"]["mesh"]["servers"] = {}

            # Ensure the specific host exists in servers
            if host not in config_data["cloudmesh"]["ai"]["mesh"]["servers"]:
                config_data["cloudmesh"]["ai"]["mesh"]["servers"][host] = {}

            # Set up port configuration if it doesn't exist
            if "port" not in config_data["cloudmesh"]["ai"]["mesh"]["servers"][host]:
                config_data["cloudmesh"]["ai"]["mesh"]["servers"][host]["port"] = {}

            # Update the local port to match remote port
            config_data["cloudmesh"]["ai"]["mesh"]["servers"][host]["port"]["local"] = int(remote_port)

            # Save the updated configuration
            config_mgr.config.save()

            console.ok(f"Successfully set local port for {host} to {remote_port}")
            console.print(f"Updated config for {host}:")
            console.print(f"  Remote port: {remote_port}")
            console.print(f"  Local port: {remote_port}")

        except Exception as e:
            console.error(f"Failed to update configuration file: {e}")
            telemetry.fail(error=str(e))
            return

        telemetry.complete()
    except Exception as e:
        telemetry.fail(error=str(e))
        console.error(f"Port command failed: {e}")

# ... [rest of the file] ...