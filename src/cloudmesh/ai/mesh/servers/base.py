from abc import ABC, abstractmethod
import os

import requests
import subprocess
import json
from cloudmesh.ai.common.io import console
from cloudmesh.ai.common.logging_utils import get_contextual_logger

logger = get_contextual_logger("mesh.servers")

class BaseServer(ABC):
    """Base class for mesh inference servers."""

    def __init__(self, host: str, port: int, server_type: str, auth_key: str = None, ssh: bool = False, timeout: int = 10):
        self.host = host
        self.port = port
        self.server_type = server_type
        
        # If auth_key is a path to a file, read its content
        if auth_key:
            expanded_path = os.path.expanduser(auth_key)
            if os.path.exists(expanded_path) and os.path.isfile(expanded_path):
                try:
                    with open(expanded_path, 'r') as f:
                        auth_key = f.read().strip()
                except Exception as e:
                    logger.error(f"Failed to read auth_key file {expanded_path}: {e}")
        
        self.auth_key = auth_key
        self.ssh = ssh
        self.url = f"http://{host}:{port}"
        self.timeout = timeout

    def _get_headers(self):
        headers = {}
        if self.auth_key:
            headers["Authorization"] = f"Bearer {self.auth_key}"
        return headers

    def _request(self, endpoint: str, timeout: int = None):
        """Perform an HTTP request, either locally or via SSH."""
        if timeout is None:
            timeout = 2  # Default for metadata requests
        
        if not self.ssh:
            resp = requests.get(f"{self.url}{endpoint}", headers=self._get_headers(), timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        else:
            # Use curl on the remote host targeting localhost
            url = f"http://localhost:{self.port}{endpoint}"
            
            header_args = []
            if self.auth_key:
                header_args.append(f"-H 'Authorization: Bearer {self.auth_key}'")
            
            header_str = " ".join(header_args)
            curl_cmd = f"curl -s {header_str} {url}".strip()
            
            try:
                result = subprocess.run(
                    ["ssh", self.host, curl_cmd],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                if result.returncode != 0:
                    raise Exception(f"SSH command failed with exit code {result.returncode}: {result.stderr}")
                
                return json.loads(result.stdout)
            except subprocess.TimeoutExpired:
                raise Exception(f"SSH request to {self.host} timed out after {timeout}s")
            except json.JSONDecodeError:
                raise Exception(f"Failed to parse JSON response from {self.host}: {result.stdout}")

    def _post(self, endpoint: str, data: dict, timeout: int = None):
        """Perform an HTTP POST request, either locally or via SSH."""
        if timeout is None:
            timeout = self.timeout
            
        if not self.ssh:
            resp = requests.post(f"{self.url}{endpoint}", headers=self._get_headers(), json=data, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        else:
            # Use curl on the remote host targeting localhost
            url = f"http://localhost:{self.port}{endpoint}"
            
            header_args = []
            if self.auth_key:
                header_args.append(f"-H 'Authorization: Bearer {self.auth_key}'")
            header_args.append("-H 'Content-Type: application/json'")
            
            header_str = " ".join(header_args)
            json_data = json.dumps(data)
            curl_cmd = f"curl -s {header_str} -d '{json_data}' {url}".strip()
            
            try:
                result = subprocess.run(
                    ["ssh", self.host, curl_cmd],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                if result.returncode != 0:
                    raise Exception(f"SSH command failed with exit code {result.returncode}: {result.stderr}")
                
                return json.loads(result.stdout)
            except subprocess.TimeoutExpired:
                raise Exception(f"SSH request to {self.host} timed out after {timeout}s")
            except json.JSONDecodeError:
                raise Exception(f"Failed to parse JSON response from {self.host}: {result.stdout}")

    def ping(self) -> bool:
        """Check if the server is reachable."""
        try:
            if not self.ssh:
                resp = requests.get(self.url, timeout=1)
                return resp.status_code < 500
            else:
                # Use curl to check reachability via SSH
                url = f"http://localhost:{self.port}/"
                result = subprocess.run(["ssh", self.host, f"curl -s -o /dev/null -w '%{{http_code}}' {url}"], 
                                        capture_output=True, text=True, timeout=1)
                return result.stdout.strip() != "000" and result.stdout.strip() != "500"
        except Exception:
            return False

    def ping_auth(self) -> bool:
        """Check if the server is reachable and authentication is accepted."""
        if not self.auth_key:
            return False
        try:
            if not self.ssh:
                resp = requests.get(self.url, headers=self._get_headers(), timeout=1)
                return resp.status_code == 200 or resp.status_code == 404 # 404 is okay for root if server is up
            else:
                url = f"http://localhost:{self.port}/"
                header = f"-H 'Authorization: Bearer {self.auth_key}'"
                result = subprocess.run(["ssh", self.host, f"curl -s -o /dev/null -w '%{{http_code}}' {header} {url}"], 
                                        capture_output=True, text=True, timeout=1)
                code = result.stdout.strip()
                return code == "200" or code == "404"
        except Exception:
            return False

    @abstractmethod
    def probe(self) -> dict:
        """
        Probes the server for version and model availability.
        Returns a dictionary with 'version', 'models', and 'status'.
        """
        pass

    @abstractmethod
    def send_hello(self, model: str) -> bool:
        """
        Sends a 'hello' prompt to the server to verify it can generate a response.
        Returns True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def send(self, model: str, msg: str) -> str:
        """
        Sends a message to the server and returns the response text.
        """
        pass

    def check_model(self, model_name: str, available_models: list) -> str:
        """Returns a checkmark or cross based on model availability."""
        if not available_models:
            return "✗"
        
        # Check if the configured model is among the available models
        if any(model_name == m for m in available_models):
            return "✓"
            
        # If different, show the first available model
        return f"✗ {available_models[0]}"
