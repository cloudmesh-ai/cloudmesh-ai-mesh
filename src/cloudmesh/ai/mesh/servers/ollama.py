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
            models_data = self._request("/api/tags").get("models", [])
            models = [m.get("name") for m in models_data]

            # Get version - Ollama's /api/version returns a JSON object
            version = "Unknown"
            try:
                v_data = self._request("/api/version", timeout=1)
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

    def send_hello(self, model: str) -> bool:
        """Sends a 'hello' prompt to the Ollama server."""
        try:
            data = {
                "model": model,
                "prompt": "hello",
                "stream": False
            }
            self._post("/api/generate", data)
            return True
        except Exception as e:
            logger.error(f"Hello probe failed for Ollama on {self.host}: {e}")
            return False

    def send(self, model: str, msg: str) -> str:
        """Sends a message to the Ollama server and returns the response."""
        try:
            data = {
                "model": model,
                "prompt": msg,
                "stream": False
            }
            response = self._post("/api/generate", data)
            return response.get("response", "")
        except Exception as e:
            logger.error(f"Failed to send message to Ollama on {self.host}: {e}")
            return f"Error: {e}"
