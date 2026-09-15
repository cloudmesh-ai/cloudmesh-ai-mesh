from abc import ABC, abstractmethod
import requests
from cloudmesh.ai.common.io import console
from cloudmesh.ai.common.logging_utils import get_contextual_logger

logger = get_contextual_logger("mesh.servers")

class BaseServer(ABC):
    """Base class for mesh inference servers."""

    def __init__(self, host: str, port: int, server_type: str, auth_key: str = None):
        self.host = host
        self.port = port
        self.server_type = server_type
        self.auth_key = auth_key
        self.url = f"http://{host}:{port}"

    def _get_headers(self):
        headers = {}
        if self.auth_key:
            headers["Authorization"] = f"Bearer {self.auth_key}"
        return headers

    @abstractmethod
    def probe(self) -> dict:
        """
        Probes the server for version and model availability.
        Returns a dictionary with 'version', 'models', and 'status'.
        """
        pass

    def check_model(self, model_name: str, available_models: list) -> str:
        """Returns a checkmark or cross based on model availability."""
        if any(model_name in m for m in available_models):
            return "✓ " + model_name
        return "✗ N/A"
