from cloudmesh.ai.common.logging_utils import get_contextual_logger
from cloudmesh.ai.mesh.config_manager import MeshConfigManager
from cloudmesh.ai.mesh.prober import MeshProber
import subprocess
import os
import yaml
import logging
from typing import List, Dict, Any

logger = get_contextual_logger("mesh.router_manager")

class RouterManager:
    """
    Manages the AI Mesh Router (LiteLLM/OpenRouter) in Docker.
    """

    def __init__(self, config_manager: MeshConfigManager = None):
        self.config_manager = config_manager or MeshConfigManager()
        self.prober = MeshProber(self.config_manager)
        self.container_name = "cloudmesh-router"
        
        # Integrate litellm_service for specialized LiteLLM management
        from cloudmesh.ai.mesh.router.litellm.litellm_service import litellm_service
        self.litellm = litellm_service()

    def _get_router_config(self) -> Dict[str, Any]:
        """Retrieves router configuration from the mesh config."""
        return {
            "host": self.config_manager.get_config("router.host") or "localhost",
            "proxy": self.config_manager.get_config("router.proxy") or "4000",
            "service": self.config_manager.get_config("router.service") or "litellm",
        }

    def start(self) -> bool:
        """Starts the router service."""
        cfg = self._get_router_config()
        service = cfg["service"]

        if service == "litellm":
            try:
                self.litellm.start(service_name=self.container_name)
                return True
            except Exception as e:
                logger.error(f"LiteLLM start failed: {e}")
                return False
        
        logger.error(f"Unsupported router service: {service}. Only 'litellm' is supported currently.")
        return False

    def stop(self) -> bool:
        """Stops the router service."""
        cfg = self._get_router_config()
        service = cfg["service"]

        if service == "litellm":
            try:
                self.litellm.stop(service_name=self.container_name)
                return True
            except Exception as e:
                logger.error(f"LiteLLM stop failed: {e}")
                return False
        
        logger.error(f"Unsupported router service: {service}. Only 'litellm' is supported currently.")
        return False

    def restart(self) -> bool:
        """Restarts the router service."""
        self.stop()
        return self.start()

    def status(self) -> Dict[str, Any]:
        """Checks if the router is running and healthy."""
        cfg = self._get_router_config()
        service = cfg["service"]

        if service == "litellm":
            res = self.litellm.status(service_name=self.container_name)
            return {
                "host": cfg["host"],
                "port": res.get("port") or cfg["proxy"],
                "running": res["status"] == "running",
                "healthy": True, # Assume healthy if running for now
                "status_text": f"{res['status']} - {res.get('uptime', 'unknown')}"
            }

        return {
            "host": cfg["host"],
            "port": cfg["proxy"],
            "running": False,
            "healthy": False,
            "status_text": f"Unsupported service: {service}"
        }

    def get_models(self) -> List[Dict[str, Any]]:
        """Returns a list of models currently configured in the router.
        Includes all enabled nodes regardless of current health.
        """
        probed_nodes = self.prober.probe_all()
        model_list = []
        for node in probed_nodes:
            if node.get("enabled") != "✓":
                continue
                
            hostname = node["hostname"]
            model = node["config_model"]
            try:
                local_port = node["ports"].split('/')[1].replace('L:', '')
            except (IndexError, KeyError):
                local_port = node.get("port", "11434")
                
            model_list.append({
                "alias": hostname,
                "model": model,
                "host": hostname,
                "port": local_port
            })
        
        if model_list:
            gpu_node = next((m for m in model_list if "white" in m["alias"]), model_list[0])
            model_list.append({
                "alias": "gpu-primary",
                "model": gpu_node["model"],
                "host": gpu_node["host"],
                "port": gpu_node["port"]
            })
        return model_list

    def test_model(self, model_name: str) -> Dict[str, Any]:
        """Tests a specific model via the router and measures response time."""
        import time
        import requests
        
        cfg = self._get_router_config()
        proxy_port = cfg["proxy"]
        url = f"http://localhost:{proxy_port}/v1/chat/completions"
        
        # Get model details for the table
        models = self.get_models()
        model_info = next((m for m in models if m["alias"] == model_name), {})
        original_model = model_info.get("model", "Unknown")
        port = model_info.get("port", "-")
        
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": "Hello, who are you?"}],
            "temperature": 0.1
        }
        
        try:
            start_time = time.time()
            response = requests.post(url, json=payload, timeout=30)
            end_time = time.time()
            
            if response.status_code == 200:
                return {
                    "model": model_name,
                    "original_model": original_model,
                    "port": port,
                    "status": "✓",
                    "time": f"{end_time - start_time:.2f}s",
                    "error": None
                }
            else:
                return {
                    "model": model_name,
                    "original_model": original_model,
                    "port": port,
                    "status": "✗",
                    "time": "-",
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                "model": model_name,
                "original_model": original_model,
                "port": port,
                "status": "✗",
                "time": "-",
                "error": str(e)
            }
