from cloudmesh.ai.common.logging_utils import get_contextual_logger
from cloudmesh.ai.mesh.config_manager import MeshConfigManager
from cloudmesh.ai.mesh.servers import OllamaServer, VllmServer

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
        for host, details in servers_config.items():
            server_type = details.get("server")
            # Normalize olama -> ollama
            if server_type == "olama":
                server_type = "ollama"
            
            model = details.get("model")
            ssh = details.get("ssh", False)
            port_cfg = details.get("port", {})
            
            if isinstance(port_cfg, dict):
                remote_port = port_cfg.get("remote")
                local_port = port_cfg.get("local", remote_port)
            else:
                remote_port = port_cfg
                local_port = port_cfg
            
            nodes_to_probe.append({
                "host": host,
                "server": server_type,
                "port": remote_port,
                "local_port": local_port,
                "model": model,
                "auth": "SSH" if ssh else "-",
                "ssh": ssh,
                "auth_key": details.get("auth_key")
            })
        return nodes_to_probe

    def probe_all(self) -> list:
        """
        Probe all configured servers and return structured results.
        """
        nodes = self.get_nodes_to_probe()
        results = []
        
        for node in nodes:
            host = node["host"]
            server_type = node["server"]
            remote_port = node["port"]
            local_port = node["local_port"]
            target_model = node["model"]
            auth_type = node["auth"]
            ssh = node["ssh"]
            auth_key = node.get("auth_key")
            
            probe_port = local_port if not ssh else remote_port
            
            try:
                if server_type == "ollama":
                    server = OllamaServer(host, probe_port, "ollama", auth_key=auth_key, ssh=ssh)
                elif server_type == "vllm":
                    server = VllmServer(host, probe_port, "vllm", auth_key=auth_key, ssh=ssh)
                else:
                    logger.warning(f"Unsupported server type {server_type} for host {host}")
                    continue
                
                probe_result = server.probe()
                model_status = server.check_model(target_model, probe_result["models"])
                
                results.append({
                    "host": host,
                    "server": server_type,
                    "version": probe_result["version"],
                    "config_model": target_model,
                    "model_status": model_status,
                    "auth": auth_type,
                    "ports": f"R:{remote_port}/L:{local_port}"
                })
            except Exception as e:
                logger.error(f"Failed to probe {host}: {e}")
                results.append({
                    "host": host,
                    "server": server_type,
                    "version": "ERROR",
                    "config_model": target_model,
                    "model_status": "✗",
                    "auth": auth_type,
                    "ports": f"R:{remote_port}/L:{local_port}",
                    "error": str(e)
                })
        
        return results
