import yaml
import importlib.resources
from pathlib import Path
from typing import Any, Dict, Optional
from cloudmesh.ai.common.config import Config
from cloudmesh.ai.common import logging as ai_log

logger = ai_log.get_logger("mesh")

class MeshConfig(Config):
    """Configuration for the AI Mesh cluster."""
    
    # Prefer the detailed directory structure, fallback to the flat file
    CONFIG_PATHS = [
        Path("~/.config/cloudmesh/ai/mesh/config.yaml").expanduser(),
        Path("~/.config/cloudmesh/ai-mesh.yaml").expanduser(),
    ]
    
    DEFAULTS = {}
    
    SCHEMA = {
        "cloudmesh.ai.mesh.servers.inference.server": {"type": str},
        "cloudmesh.ai.mesh.servers.inference.port": {"type": int},
        "cloudmesh.ai.mesh.logging.level": {"type": str},
        "cloudmesh.ai.mesh.logging.json_format": {"type": bool},
        "cloudmesh.ai.mesh.logging.log_dir": {"type": str},
    }

    def _load_config(self):
        """Loads configuration from local project file, bundled config, and then user overrides."""
        # 1. Try to load from the local workspace file first (crucial for development)
        try:
            # Path relative to this file: src/cloudmesh/ai/mesh/config.py -> src/cloudmesh/ai/mesh/config.yaml
            local_config_path = Path(__file__).parent / "config.yaml"
            if local_config_path.exists():
                with open(local_config_path, "r") as f:
                    local_data = yaml.safe_load(f)
                    if local_data:
                        self.data.update(local_data)
                        # logger.info(f"Loaded local workspace config from: {local_config_path}")
        except Exception as e:
            logger.warning(f"Could not load local workspace config: {e}")
        
        # 2. Fallback to bundled config.yaml using importlib.resources
        try:
            config_path = importlib.resources.files("cloudmesh.ai.mesh").joinpath("config.yaml")
            with config_path.open("r") as f:
                bundled_data = yaml.safe_load(f)
                if bundled_data:
                    # Only update if not already set by local config
                    for k, v in bundled_data.items():
                        if k not in self.data:
                            self.data[k] = v
        except Exception as e:
            logger.warning(f"Could not load bundled config config.yaml: {e}")
        
        # 3. Load user overrides from the config paths (in order of preference)
        for path in self.CONFIG_PATHS:
            if path.exists():
                try:
                    with open(path, "r") as f:
                        user_config = yaml.safe_load(f)
                        if user_config:
                            self.data.update(user_config)
                except Exception as e:
                    logger.warning(f"Could not load user config file {path}: {e}")
        
        # 4. Apply logging configuration to ai-common logging system
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