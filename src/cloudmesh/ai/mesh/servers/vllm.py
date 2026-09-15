from .base import BaseServer
import requests
from cloudmesh.ai.common.io import console
from cloudmesh.ai.common.logging_utils import get_contextual_logger

logger = get_contextual_logger("mesh.servers.vllm")

class VllmServer(BaseServer):
    """vLLM server probe implementation."""

    def get_models(self) -> list:
        """Queries the vLLM server for available models."""
        try:
            # vLLM typically follows OpenAI API
            models_data = self._request("/v1/models").get("data", [])
            return [m.get("id") for m in models_data]
        except Exception as e:
            logger.debug(f"Failed to query vLLM models on {self.host}: {e}")
            return []

    def probe(self) -> dict:
        try:
            models = self.get_models()
            
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
