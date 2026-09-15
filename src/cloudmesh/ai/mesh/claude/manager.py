"""
Claude Manager Implementation

This module provides functionality to manage Claude AI settings and credentials.
"""

import json
import os
import difflib
from pathlib import Path
from typing import Any, Dict, Optional
from cloudmesh.ai.common.io import readfile, writefile
from cloudmesh.ai.common.logging_utils import get_contextual_logger

logger = get_contextual_logger("common.claude.manager")

class ClaudeManager:
    """Manages Claude AI settings and credentials."""

    def __init__(self, hostname: str, config_dir: Optional[str] = None):
        """
        Initializes the ClaudeManager.

        Args:
            hostname: The hostname of the target environment, used to locate configuration.
            config_dir: Optional override for the configuration directory.
        """
        self.hostname = hostname
        
        if config_dir:
            self.config_dir = config_dir
        else:
            # 1. Try the standard user-specific path: ~/.cloudmesh/ai/{hostname}/claude
            user_path = Path("~/.cloudmesh/ai").expanduser() / hostname / "claude"
            
            # 2. Fallback to the discovered development path if the user path doesn't exist
            dev_path = Path("/Users/grey/work/cloudmesh-ai-mesh/src/cloudmesh/ai/mesh/claude")
            
            if user_path.exists():
                self.config_dir = str(user_path)
            else:
                self.config_dir = str(dev_path)
        
        logger.debug(f"ClaudeManager initialized for host {hostname} using config dir: {self.config_dir}")

    def get_settings(self) -> Dict[str, Any]:
        """
        Returns the Claude settings from settings.json.

        Returns:
            A dictionary containing the settings, or an empty dictionary if the file could not be loaded.
        """
        path = os.path.join(self.config_dir, "settings.json")
        try:
            content = readfile(path)
            return json.loads(content)
        except Exception as e:
            logger.error(f"Failed to load Claude settings from {path}: {e}")
            return {}

    def get_credentials(self) -> Dict[str, Any]:
        """
        Returns the Claude credentials from .credentials.json.

        Returns:
            A dictionary containing the credentials, or an empty dictionary if the file could not be loaded.
        """
        path = os.path.join(self.config_dir, ".credentials.json")
        try:
            content = readfile(path)
            return json.loads(content)
        except Exception as e:
            logger.error(f"Failed to load Claude credentials from {path}: {e}")
            return {}

    def save_settings(self, settings: Dict[str, Any]) -> str:
        """
        Saves the Claude settings to ~/claude/settings.json if they have changed.

        Args:
            settings: The settings dictionary to save.

        Returns:
            A message indicating the result of the save operation.
        """
        path = str(Path("~/claude/settings.json").expanduser())
        return self._save_json(path, settings, "Settings")

    def save_credentials(self, credentials: Dict[str, Any]) -> str:
        """
        Saves the Claude credentials to ~/.claude/.credentials.json if they have changed.

        Args:
            credentials: The credentials dictionary to save.

        Returns:
            A message indicating the result of the save operation.
        """
        path = str(Path("~/.claude/.credentials.json").expanduser())
        return self._save_json(path, credentials, "Credentials")

    def _save_json(self, path: str, data: Dict[str, Any], label: str) -> str:
        """
        Internal helper to save JSON data with diff checking and user confirmation.

        Args:
            path: The destination file path.
            data: The data to save.
            label: A label for the data (e.g., "Settings") for logging and prompts.

        Returns:
            A message indicating whether the file was saved, unchanged, or if save was cancelled.
        """
        try:
            # Prepare new content as a sorted JSON string for consistent diffing
            new_content = json.dumps(data, indent=2, sort_keys=True)
            
            # Read existing content
            existing_content = ""
            if os.path.exists(path):
                try:
                    existing_content = readfile(path)
                    # To avoid formatting differences, re-serialize the existing data
                    existing_data = json.loads(existing_content)
                    existing_content = json.dumps(existing_data, indent=2, sort_keys=True)
                except Exception:
                    # If existing file is not valid JSON, treat as empty for diffing
                    existing_content = ""

            # Check if content is the same
            if existing_content == new_content:
                return f"The {label} file does not have to be changed."

            # Show differences
            print(f"\\n--- Differences in {label} ({path}) ---")
            diff = difflib.unified_diff(
                existing_content.splitlines(),
                new_content.splitlines(),
                fromfile="Existing",
                tofile="New",
                lineterm=""
            )
            for line in diff:
                print(line)
            print("---------------------------------------")

            # Ask for confirmation
            confirm = input(f"Would you like to save these changes to {label}? (y/n): ").strip().lower()
            if confirm == 'y':
                writefile(path, new_content)
                return f"{label} saved successfully to {path}."
            else:
                return f"Save for {label} cancelled by user."

        except Exception as e:
            logger.error(f"Error during {label} save process to {path}: {e}")
            return f"Failed to save {label}: {e}"
