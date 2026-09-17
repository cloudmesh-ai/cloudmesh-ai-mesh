import os
import subprocess
import yaml
import logging
import json
from datetime import datetime, timezone
from importlib import resources

# Set up logging
logger = logging.getLogger(__name__)

class LiteLLMServiceError(Exception):
    """Exception raised for errors in the litellm_service."""
    pass

class litellm_service:
    """
    Service to manage the LiteLLM proxy server.

    This service handles the generation of LiteLLM configuration from the 
    Cloudmesh AI Mesh configuration, and manages the lifecycle of the 
    LiteLLM proxy running in a Docker container.
    """

    DEFAULT_IMAGE = "ghcr.io/berriai/litellm:v1.89.4"

    def __init__(self, file=None, dir=None):
        """
        Initializes the LiteLLM service.

        Args:
            file (str, optional): Path to the config.yaml file. 
                Defaults to 'src/cloudmesh/ai/mesh/config.yaml' relative to 
                the package or current working directory.
            dir (str, optional): Working directory where the litellm_config.yaml 
                will be written. Defaults to the current working directory.
        """
        if dir is None:
            dir = os.getcwd()
        
        self.dir = dir
        if file is None:
            try:
                # Use importlib.resources to find the file relative to the package.
                # This works both for pip install -e . and for installed packages.
                self.config_file = str(resources.files('cloudmesh.ai.mesh').joinpath('config.yaml'))
            except (ImportError, ModuleNotFoundError, FileNotFoundError):
                # Fallback for local development if package is not installed
                self.config_file = os.path.join(dir, "src/cloudmesh/ai/mesh/config.yaml")
        else:
            self.config_file = file

    def start(self, 
              service_name="litellm-proxy"
              ):
        """
        Starts the LiteLLM proxy service in a Docker container.

        This method first generates the `litellm_config.yaml` file based on the 
        mesh configuration and then runs the Docker command to start the proxy.

        Args:
            service_name (str): Name of the Docker container. Defaults to "litellm-proxy".

        Raises:
            LiteLLMServiceError: If the configuration cannot be generated or 
                the Docker container fails to start.
        """
        config_path = self.get_litellm_config()
        if not config_path:
            raise LiteLLMServiceError("Failed to generate litellm_config.yaml. Cannot start service.")

        # Get proxy port from config
        proxy_port = self._get_proxy_port()

        # 1. Remove container by name
        subprocess.run(["docker", "rm", "-f", service_name], capture_output=True)

        # 2. Find and remove any other containers using the proxy port to avoid "port is already allocated"
        try:
            port_filter = f"publish={proxy_port}"
            result = subprocess.run(["docker", "ps", "-q", "--filter", port_filter], capture_output=True, text=True)
            container_ids = result.stdout.strip().split('\n')
            for cid in container_ids:
                if cid:
                    logger.info(f"Removing existing container {cid} using port {proxy_port}")
                    subprocess.run(["docker", "rm", "-f", cid], capture_output=True)
        except Exception as e:
            logger.warning(f"Could not clean up containers using port {proxy_port}: {e}")

        # 3. Check if the port is still occupied by a non-docker process
        try:
            # lsof -i :port
            check_port = subprocess.run(["lsof", "-i", f":{proxy_port}"], capture_output=True, text=True)
            if check_port.returncode == 0:
                # Port is occupied. We should check if it's a docker-proxy or something else.
                if "docker-proxy" not in check_port.stdout:
                    logger.error(f"Port {proxy_port} is occupied by a non-docker process:\n{check_port.stdout}")
                    raise LiteLLMServiceError(f"Port {proxy_port} is already allocated by another process. Please kill it first.")
        except FileNotFoundError:
            logger.warning("lsof command not found, skipping port occupancy check.")
        except LiteLLMServiceError:
            raise
        except Exception as e:
            logger.warning(f"Error checking port occupancy: {e}")

        # Construct docker run command as a list for security and correctness
        docker_run = [
            "docker", "run", "-d",
            "--name", service_name,
            "-p", f"{proxy_port}:{proxy_port}",
            "--add-host=host.docker.internal:host-gateway",
            "-v", f"{os.path.abspath(config_path)}:/app/litellm_config.yaml",
            "-e", "CONFIG_FILE_PATH=/app/litellm_config.yaml",
            self.DEFAULT_IMAGE
        ]
        
        try:
            subprocess.run(docker_run, check=True, capture_output=True, text=True)
            logger.info(f"LiteLLM service {service_name} started successfully on port {proxy_port}.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start LiteLLM container: {e.stderr}")
            raise LiteLLMServiceError(f"Docker run failed: {e.stderr}")

    def stop(self, service_name="litellm-proxy"): 
        """
        Stops and removes the LiteLLM proxy Docker container.

        Args:
            service_name (str): Name of the Docker container to stop. 
                Defaults to "litellm-proxy".
        """
        try:
            subprocess.run(["docker", "rm", "-f", service_name], check=True, capture_output=True)
            subprocess.run(["docker", "system", "prune", "-f"], check=True, capture_output=True)
            logger.info(f"LiteLLM service {service_name} stopped and resources pruned.")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Error while stopping service: {e.stderr}")

    def restart(self, service_name="litellm-proxy"):
        """
        Restarts the LiteLLM proxy service.

        Args:
            service_name (str): Name of the Docker container. 
                Defaults to "litellm-proxy".
        """
        self.stop(service_name)
        self.start(service_name)

    def status(self, service_name="litellm-proxy"):
        """
        Gets the current status of the LiteLLM proxy Docker container.

        Args:
            service_name (str): Name of the Docker container. 
                Defaults to "litellm-proxy".

        Returns:
            dict: A dictionary containing status, uptime, and port. 
                Example: {"status": "running", "uptime": "2h 15m", "port": 4000}
                Returns {"status": "not_found"} if the container does not exist.
        """
        try:
            result = subprocess.run(
                ["docker", "inspect", service_name], 
                capture_output=True, text=True, check=True
            )
            container_info = json.loads(result.stdout)[0]
            
            state = container_info.get("State", {})
            status = state.get("Status", "unknown")
            
            # Calculate uptime
            uptime = "unknown"
            started_at = state.get("StartedAt")
            if started_at:
                try:
                    # Docker uses RFC3339 format: 2023-09-17T10:00:00.123456789Z
                    # We strip nanoseconds for compatibility with fromisoformat
                    started_dt = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                    now = datetime.now(timezone.utc)
                    diff = now - started_dt
                    
                    days = diff.days
                    hours, remainder = divmod(diff.seconds, 3600)
                    minutes, _ = divmod(remainder, 60)
                    
                    uptime_parts = []
                    if days > 0: uptime_parts.append(f"{days}d")
                    if hours > 0: uptime_parts.append(f"{hours}h")
                    if minutes > 0: uptime_parts.append(f"{minutes}m")
                    uptime = " ".join(uptime_parts) if uptime_parts else "just started"
                except Exception as e:
                    logger.warning(f"Could not parse started_at time: {e}")

            # Find the host port mapped to 4000 (or whatever proxy_port is)
            port = None
            proxy_port = self._get_proxy_port()
            ports = container_info.get("NetworkSettings", {}).get("Ports", {})
            # Format is usually {'4000/tcp': [{'HostIp': '0.0.0.0', 'HostPort': '4000'}]}
            port_key = f"{proxy_port}/tcp"
            if port_key in ports:
                port = ports[port_key][0].get("HostPort")

            return {
                "status": status,
                "uptime": uptime,
                "port": int(port) if port else None
            }

        except subprocess.CalledProcessError:
            return {"status": "not_found"}
        except (json.JSONDecodeError, IndexError, KeyError) as e:
            logger.error(f"Error parsing docker inspect output: {e}")
            return {"status": "error", "message": str(e)}

    def __str__(self):
        """
        Returns a string representation of the LiteLLM service.

        Returns:
            str: A string containing the configuration file and working directory.
        """
        return f"litellm_service(config_file={self.config_file}, dir={self.dir})"

    def get_litellm_config(self, filename="litellm_config.yaml"):
        """
        Generates a LiteLLM configuration file from the mesh config.

        Reads the servers defined in the mesh configuration and transforms them 
        into the format expected by LiteLLM.

        Args:
            filename (str): The name of the output configuration file. 
                Defaults to "litellm_config.yaml".

        Returns:
            str: The absolute path to the generated configuration file, 
                or None if the source config file was not found.
        """
        if not os.path.exists(self.config_file):
            logger.error(f"Config file not found: {self.config_file}")
            return None

        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error reading config file: {e}")
            return None

        servers = config.get('cloudmesh', {}).get('ai', {}).get('mesh', {}).get('servers', {})
        model_list = []

        for server_name, server_info in servers.items():
            if not server_info.get('enabled', False):
                continue
            
            server_type = server_info.get('server')
            model = server_info.get('model')
            port = server_info.get('port', {}).get('local')
            
            if not server_type or not model or not port:
                logger.warning(f"Server {server_name} missing required info (server, model, or port). Skipping.")
                continue

            litellm_model = self._map_server_to_litellm(server_type, model)
            api_key = self._resolve_api_key(server_info.get('auth_key'))
                
            model_entry = {
                "model_name": server_name,
                "litellm_params": {
                    "model": litellm_model,
                    "api_base": f"http://host.docker.internal:{port}",
                }
            }
            if api_key:
                model_entry["litellm_params"]["api_key"] = api_key

            model_list.append(model_entry)

        litellm_config = {"model_list": model_list}
        
        config_path = os.path.join(self.dir, filename)
        try:
            with open(config_path, 'w') as f:
                yaml.dump(litellm_config, f, default_flow_style=False)
            return os.path.abspath(config_path)
        except Exception as e:
            logger.error(f"Failed to write litellm_config.yaml: {e}")
            return None

    def _get_proxy_port(self):
        """
        Extracts the proxy port from the mesh configuration.
        
        Returns:
            int: The proxy port defined in config, or 4000 as a default.
        """
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
            return int(config.get('cloudmesh', {}).get('ai', {}).get('mesh', {}).get('router', {}).get('proxy', 4000))
        except Exception:
            return 4000

    def _map_server_to_litellm(self, server_type, model):
        """
        Maps server type and model name to a LiteLLM model identifier.
        """
        if server_type == 'ollama':
            return f"ollama/{model}"
        elif server_type == 'vllm':
            return f"openai/{model}"
        return model

    def _resolve_api_key(self, auth_key):
        """
        Resolves the API key from a string or a file path.
        """
        if not auth_key:
            return None
        
        if auth_key.startswith('~') or auth_key.startswith('/'):
            expanded_path = os.path.expanduser(auth_key)
            if os.path.exists(expanded_path):
                try:
                    with open(expanded_path, 'r') as key_file:
                        return key_file.read().strip()
                except Exception as e:
                    logger.warning(f"Could not read API key from {expanded_path}: {e}")
        
        return auth_key
