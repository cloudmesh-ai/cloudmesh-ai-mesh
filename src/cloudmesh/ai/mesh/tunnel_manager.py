from cloudmesh.ai.common.ssh.tunnel import Tunnel
from cloudmesh.ai.mesh.config_manager import MeshConfigManager
from cloudmesh.ai.common.logging_utils import get_contextual_logger

logger = get_contextual_logger("mesh.tunnel_manager")

class TunnelManager:
    """Manages SSH tunnels for AI Mesh servers."""

    def __init__(self, config_manager: MeshConfigManager = None):
        self.config_manager = config_manager or MeshConfigManager()
        self.tunnels = {}

    def _get_server_config(self, hostname: str):
        """Helper to get server config and validate SSH enablement."""
        servers = self.config_manager.get_servers_config()
        if not servers or hostname not in servers:
            raise ValueError(f"Hostname {hostname} not found in configuration.")

        cfg = servers[hostname]
        if not cfg.get("ssh", False):
            raise ValueError(f"SSH is not enabled for host {hostname} in configuration.")

        return cfg

    def start(self, hostname: str) -> bool:
        """Starts a tunnel for the specified hostname."""
        cfg = self._get_server_config(hostname)

        ports = cfg.get("port", {})
        local_port = ports.get("local")
        remote_port = ports.get("remote")

        if not local_port or not remote_port:
            raise ValueError(f"Missing local or remote port configuration for {hostname}.")

        if hostname in self.tunnels and self.tunnels[hostname].is_active():
            logger.warn(f"Tunnel for {hostname} is already running.")
            return True

        # remote_host is typically localhost when forwarding to a service on the ssh_host
        tunnel = Tunnel(
            local_port=int(local_port),
            remote_host="localhost",
            remote_port=int(remote_port),
            ssh_host=hostname
        )

        if tunnel.start():
            self.tunnels[hostname] = tunnel
            return True

        logger.error(f"Failed to start tunnel for {hostname}")
        return False

    def stop(self, hostname: str) -> bool:
        """Stops the tunnel for the specified hostname."""
        if hostname not in self.tunnels:
            logger.warn(f"No active tunnel found for {hostname} to stop.")
            return False

        tunnel = self.tunnels[hostname]
        if tunnel.stop():
            del self.tunnels[hostname]
            return True

        return False

    def status(self, hostname: str) -> bool:
        """Returns the status of the tunnel for the specified hostname."""
        # Ensure the host is configured for SSH even for status checks
        self._get_server_config(hostname)

        if hostname in self.tunnels:
            return self.tunnels[hostname].is_active()

        return False

    def list_active(self) -> dict:
        """Returns a dictionary of all active tunnels."""
        active_tunnels = {}
        for host, tunnel in self.tunnels.items():
            if tunnel.is_active():
                active_tunnels[host] = {
                    "local_port": tunnel.local_port,
                    "remote_port": tunnel.remote_port,
                    "remote_host": tunnel.remote_host,
                    "ssh_host": tunnel.ssh_host
                }
        return active_tunnels