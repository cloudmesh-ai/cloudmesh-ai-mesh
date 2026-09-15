from .base import BaseServer
import requests
from cloudmesh.ai.common.io import console
from cloudmesh.ai.common.logging_utils import get_contextual_logger

logger = get_contextual_logger("mesh.servers.vllm")

class VllmServer(BaseServer):
    """vLLM server probe implementation."""

    def probe(self) -> dict:
        try:
            # vLLM typically follows OpenAI API
            resp = requests.get(f"{self.url}/v1/models", headers=self._get_headers(), timeout=2)
            resp.raise_for_status()
            models_data = resp.json().get("data", [])
            models = [m.get("id") for m in models_data]

            # vLLM doesn't have a standard /version endpoint like Ollama
            # Often the model name is the primary identifier
            version = models[0] if models else "Unknown"

            return {
                "status": "up",
                "version": version,
                "models": models,
                "error": None
            }
        except Exception as e:
            # Use console.error instead of logger to avoid the context_id logging error
            console.error(f"Failed to get models from vLLM on {self.host}: {e}")
            return {
                "status": "down",
                "version": "N/A",
                "models": [],
                "error": str(e)
            }
