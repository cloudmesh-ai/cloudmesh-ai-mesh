import yaml
import importlib.resources
from pathlib import Path
from typing import Any, Dict, Optional
from cloudmesh.ai.common.config import Config
from cloudmesh.ai.common import logging as ai_log

logger = ai_log.get_logger("mesh")

class MeshConfig(Config):
    """Configuration for the AI Mesh cluster."""
    
    DEFAULT_CONFIG_PATH = Path("~/.config/cloudmesh/ai-mesh.yaml").expanduser()
    
    DEFAULTS = {}
    
    SCHEMA = {
        "cloudmesh.ai.mesh.servers.inference.server": {"type": str},
        "cloudmesh.ai.mesh.servers.inference.port": {"type": int},
        "cloudmesh.ai.mesh.logging.level": {"type": str},
        "cloudmesh.ai.mesh.logging.json_format": {"type": bool},
        "cloudmesh.ai.mesh.logging.log_dir": {"type": str},
    }

    def _load_config(self):
        """Loads configuration from bundled mesh.yaml and then user overrides."""
        # 1. Load bundled mesh.yaml as base defaults using importlib.resources
        try:
            # Access the mesh.yaml file within the cloudmesh.ai.mesh package
            with importlib.resources.files("cloudmesh.ai.mesh").joinpath("mesh.yaml").open("r") as f:
                bundled_data = yaml.safe_load(f)
                if bundled_data:
                    self.data.update(bundled_data)
        except Exception as e:
            logger.warning(f"Could not load bundled config mesh.yaml: {e}")
        
        # 2. Load user overrides from the config path
        if self.path.exists():
            try:
                with open(self.path, "r") as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        self.data.update(user_config)
            except Exception as e:
                logger.warning(f"Could not load user config file {self.path}: {e}")
        
        # 3. Apply logging configuration to ai-common logging system
        self._apply_logging_config()

    def _apply_logging_config(self):
        """Pushes logging settings from the config to the ai-common logging utility."""
        try:
            logging_cfg = self.get("cloudmesh.ai.mesh.logging")
            if logging_cfg and isinstance(logging_cfg, dict):
                # Update the global config in ai-common.logging
                ai_log._logging_config.update(logging_cfg)
        except Exception as e:
            logger.warning(f"Failed to apply logging config: {e}")

# Singleton instance for easy access
config = MeshConfig()