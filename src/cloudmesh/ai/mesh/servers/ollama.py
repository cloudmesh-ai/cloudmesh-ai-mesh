from .base import BaseServer
import requests
from cloudmesh.ai.common.io import console
from cloudmesh.ai.common.logging_utils import get_contextual_logger

logger = get_contextual_logger("mesh.servers.ollama")

class OllamaServer(BaseServer):
    """Ollama server probe implementation."""

    def probe(self) -> dict:
        try:
            # Get models
            resp = requests.get(f"{self.url}/api/tags", headers=self._get_headers(), timeout=2)
            resp.raise_for_status()
            models_data = resp.json().get("models", [])
            models = [m.get("name") for m in models_data]

            # Get version - Ollama's /api/version returns a JSON object
            version = "Unknown"
            try:
                v_resp = requests.get(f"{self.url}/api/version", headers=self._get_headers(), timeout=1)
                if v_resp.status_code == 200:
                    v_data = v_resp.json()
                    version = v_data.get("version", "Unknown")
            except:
                pass

            return {
                "status": "up",
                "version": version,
                "models": models,
                "error": None
            }
        except Exception as e:
            # Use console.error instead of logger to avoid the context_id logging error
            console.error(f"Failed to get models from Ollama on {self.host}: {e}")
            return {
                "status": "down",
                "version": "N/A",
                "models": [],
                "error": str(e)
            }
