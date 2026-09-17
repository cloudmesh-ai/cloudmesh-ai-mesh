from cloudmesh.ai.mesh.config import config

class MeshConfigManager:
    """
    Manages configuration for the AI Mesh.
    """

    def __init__(self):
        self.config = config

    def get_servers_config(self):
        """Returns the dictionary of all configured servers."""
        return self.config.get("cloudmesh.ai.mesh.servers")

    def get_inference_server(self):
        """Retrieves the global inference server setting."""
        return self.config.get("cloudmesh.ai.mesh.servers.inference.server")

    def get_config(self, key: str, default=None):
        """Gets a config value using a short key mapping."""
        full_key = self._map_key(key)
        return self.config.get(full_key, default)

    def set_config(self, key: str, value):
        """Sets a config value using a short key mapping."""
        full_key = self._map_key(key)
        self.config.set(full_key, value)
        self.config.save()

    def _map_key(self, key: str) -> str:
        """Maps short CLI keys to full config paths."""
        mapping = {
            "inference.server": "cloudmesh.ai.mesh.servers.inference.server",
            "inference.port": "cloudmesh.ai.mesh.servers.inference.port",
            "default": "cloudmesh.ai.mesh.default",
            "router.host": "cloudmesh.ai.mesh.router.host",
            "router.proxy": "cloudmesh.ai.mesh.router.proxy",
            "router.service": "cloudmesh.ai.mesh.router.service",
        }
        return mapping.get(key, key)
