from cloudmesh.ai.common.logging_utils import get_contextual_logger
from cloudmesh.ai.mesh.config_manager import MeshConfigManager
from cloudmesh.ai.mesh.servers import OllamaServer, VllmServer
from cloudmesh.ai.mesh.servers.base import BaseServer
import concurrent.futures
import socket

logger = get_contextual_logger("mesh.prober")

class MeshProber:
    """
    Probes the versions of inference servers across the mesh.
    """

    def __init__(self, config_manager: MeshConfigManager = None):
        self.config_manager = config_manager or MeshConfigManager()

    def get_nodes_to_probe(self) -> list:
        """
        Parse configuration to identify nodes to probe.
        """
        servers_config = self.config_manager.get_servers_config()
        if not servers_config:
            return []

        nodes_to_probe = []
        for hostname, details in servers_config.items():
            server_type = details.get("server")
            # Normalize ollama -> ollama
            if server_type == "ollama":
                server_type = "ollama"
            
            model = details.get("model")
            ssh = details.get("ssh", False)
            port_cfg = details.get("port", {})
            
            # Check for 'enabled' first, then 'on'
            enabled = details.get("enabled", details.get("on", True))
            
            # Handle weird YAML parsing where boolean values might become keys
            if "enabled" not in details and "on" not in details:
                for k, v in details.items():
                    if isinstance(v, bool) and k not in ["ssh"]:
                        enabled = v
                        break
            
            if isinstance(port_cfg, dict):
                remote_port = port_cfg.get("remote")
                local_port = port_cfg.get("local", remote_port)
            else:
                remote_port = port_cfg
                local_port = port_cfg
            
            # Use auth_key or api_key from config
            auth_key = details.get("auth_key") or details.get("api_key")
            
            nodes_to_probe.append({
                "hostname": hostname,
                "host": details.get("host", hostname),
                "server": server_type,
                "port": remote_port,
                "local_port": local_port,
                "model": model,
                "auth": "SSH" if ssh else "-",
                "ssh": ssh,
                "auth_key": auth_key,
                "enabled": enabled
            })
        return nodes_to_probe

    def _probe_node(self, node, hello=False) -> dict:
        """
        Probes a single node and returns the result.
        """
        import time
        hostname = node["hostname"]
        host = node["host"]
        server_type = node["server"]
        remote_port = node["port"]
        local_port = node["local_port"]
        target_model = node["model"]
        auth_type = node["auth"]
        ssh = node["ssh"]
        auth_key = node.get("auth_key")
        enabled = node.get("enabled", True)
        
        # Determine tunnel status
        tunnel_status = "-"
        if ssh:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.1)
                    if s.connect_ex(('localhost', int(local_port))) == 0:
                        tunnel_status = "✓"
                    else:
                        tunnel_status = "✗"
            except Exception:
                tunnel_status = "✗"
        
        if not enabled:
            return {
                "hostname": hostname,
                "host": host,
                "server": server_type,
                "version": "-",
                "config_model": target_model,
                "model_status": "-",
                "auth": auth_type,
                "health": "-",
                "key": "-",
                "hello": "-",
                "ports": f"R:{remote_port}/L:{local_port}",
                "enabled": "✗",
                "tunnel": tunnel_status
            }

        # Initialize server object first to use its connectivity methods
        try:
            if server_type == "ollama":
                server = OllamaServer(host, local_port if not ssh else remote_port, "ollama", auth_key=auth_key, ssh=ssh)
            elif server_type == "vllm":
                server = VllmServer(host, local_port if not ssh else remote_port, "vllm", auth_key=auth_key, ssh=ssh)
            else:
                logger.warning(f"Unsupported server type {server_type} for host {host}")
                return None
        except Exception as e:
            logger.error(f"Failed to initialize server for {host}: {e}")
            return None

        # Health check using server's ping method
        health_status = "✓" if server.ping() else "✗"
        
        # Reachability check with auth using server's ping_auth method
        key_status = "-"
        if auth_key:
            key_status = "✓ File" if server.ping_auth() else "✗ File"
        
        # Actual probe for version and models
        try:
            probe_result = server.probe()
            model_status = server.check_model(target_model, probe_result["models"])
            
            # Hello check
            hello_status = "-"
            if hello:
                try:
                    start_time = time.time()
                    if server.send_hello(target_model):
                        elapsed = time.time() - start_time
                        hello_status = f"✓ {elapsed:.2f}s"
                    else:
                        hello_status = "✗"
                except Exception:
                    hello_status = "✗"
            
            return {
                "hostname": hostname,
                "host": host,
                "server": server_type,
                "version": probe_result["version"],
                "config_model": target_model,
                "model_status": model_status,
                "auth": auth_type,
                "health": health_status,
                "key": key_status,
                "hello": hello_status,
                "ports": f"R:{remote_port}/L:{local_port}",
                "enabled": "✓",
                "tunnel": tunnel_status
            }
        except Exception as e:
            logger.error(f"Failed to probe {host}: {e}")
            return {
                "hostname": hostname,
                "host": host,
                "server": server_type,
                "version": "ERROR",
                "config_model": target_model,
                "model_status": "✗",
                "auth": auth_type,
                "health": health_status,
                "key": key_status,
                "hello": "-",
                "ports": f"R:{remote_port}/L:{local_port}",
                "error": str(e),
                "enabled": "✓",
                "tunnel": tunnel_status
            }

    def probe_all(self, hello=False) -> list:
        """
        Probe all configured servers and return structured results.
        """
        nodes = self.get_nodes_to_probe()
        if not nodes:
            return []
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Use submit to pass the hello flag
            futures = [executor.submit(self._probe_node, node, hello) for node in nodes]
            results = [f.result() for f in futures]
        
        # Filter out None results (from unsupported server types)
        return [r for r in results if r is not None]
