from cloudmesh.ai.common.logging_utils import get_contextual_logger
from cloudmesh.ai.mesh.config_manager import MeshConfigManager

logger = get_contextual_logger(\"mesh.manager\")

class MeshManager:
    \"\"\"
    Manages high-level operations and observation of the AI Mesh.
    \"\"\"

    def __init__(self, config_manager: MeshConfigManager = None):
        self.config_manager = config_manager or MeshConfigManager()

    def get_cluster_info(self) -> dict:
        \"\"\"
        Retrieves general information about the AI Mesh cluster.
        \"\"\"
        server = self.config_manager.get_inference_server()
        return {
            \"inference_server\": server,
            \"primary_node\": \"WHITE (RTX 3090)\",
            \"fallback_node\": \"SPARK (CPU/Lightweight GPU)\",
            \"control_plane\": \"LAPTOP\",
            \"api_gateway\": \"LiteLLM (port 4000)\"
        }

    def get_gpu_status(self) -> list:
        \"\"\"
        Fetches real-time GPU usage from the cluster.
        \"\"\"
        try:
            from cloudmesh.ai.hpc.hpc import Hpc
            hpc = Hpc()
            return hpc.get_cluster_gpu_usage()
        except ImportError:
            logger.error(\"ai-hpc package is required for GPU status check.\")
            raise ImportError(\"ai-hpc package is required for GPU status check.\")
        except Exception as e:
            logger.error(f\"Failed to fetch GPU status: {e}\")
            raise

    def run_health_check(self):
        \"\"\"
        Performs a health check of the HPC environment.
        \"\"\"
        try:
            from cloudmesh.ai.hpc.hpc import Hpc
            hpc = Hpc()
            hpc.check()
            return True
        except ImportError:
            logger.error(\"ai-hpc package is required for health check.\")
            raise ImportError(\"ai-hpc package is required for health check.\")
        except Exception as e:
            logger.error(f\"Health check failed: {e}\")
            raise
