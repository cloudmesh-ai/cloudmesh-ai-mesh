#!/usr/bin/env python
import os
import sys
import subprocess
import urllib.request
import json
import shutil
from pathlib import Path

try:
    from simple_term_menu import TerminalMenu
except ImportError:
    print("Error: 'simple-term-menu' is required for arrow-key navigation.")
    print("Run: pip install simple-term-menu")
    sys.exit(1)

LITELLM_URL = "http://localhost:4000/v1/models"

def get_api_key():
    if os.getenv("ANTHROPIC_API_KEY"):
        return os.getenv("ANTHROPIC_API_KEY")
    
    settings_path = Path.home() / ".claude" / "settings.json"
    try:
        if settings_path.exists():
            data = json.loads(settings_path.read_text(encoding="utf-8"))
            return data.get("env", {}).get("ANTHROPIC_API_KEY")
    except Exception:
        pass
        
    return "error"

def fetch_models(api_key):
    req = urllib.request.Request(
        LITELLM_URL,
        headers={"Authorization": f"Bearer {api_key}"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return [model["id"] for model in data.get("data", [])]
    except Exception as e:
        print(f"Error fetching models from proxy: {e}")
        return []

def main():
    api_key = get_api_key()
    print("Fetching active models from LiteLLM proxy...")
    models = fetch_models(api_key)
    
    if not models:
        print("Warning: No models found or proxy is unreachable. Falling back to default list.")
        models = [
            "a100-2-gemma4-31b",
            "a100-4-gemma4-31b",
            "jetstream-gpt-oss-120b",
            "jetstream-gemma4",
            "jetstream-muse-glimmer",
            "jetstream-qwen3",
            "nvidia-deepseek-v4.1",
            "spark-deepseek-r1:32b",
            "mac-qwen3-coder"
        ]

    # Sort models to prioritize A100 and Jetstream 120B at the top
    sorted_models = []
    priority_keywords = ["gemma4-31b", "jetstream-gpt-oss-120b"]
    
    for pk in priority_keywords:
        for m in models:
            if pk in m and m not in sorted_models:
                sorted_models.append(m)
                
    for m in models:
        if m not in sorted_models:
            sorted_models.append(m)

    # Format menu entries with fixed-width right alignment for double-digit indexes
    menu_entries = []
    for idx, model_id in enumerate(sorted_models, 1):
        label = f"[{idx:2d}]  {model_id}"
        menu_entries.append(label)

    print("\nAvailable Models on Proxy (Use arrow keys and Enter to select):")
    
    terminal_menu = TerminalMenu(
        menu_entries,
        menu_cursor_style=("fg_cyan", "bold"),
        menu_highlight_style=("standout",),
        clear_screen=False
    )
    
    selected_index = terminal_menu.show()
    
    if selected_index is None:
        print("Selection canceled. Exiting.")
        sys.exit(0)
        
    selected_model = sorted_models[selected_index]

    # Map target selection to a model string present in LiteLLM config.yaml
    target_cli_model = "claude-3-5-sonnet"
    if "haiku" in selected_model.lower():
        target_cli_model = "claude-3-5-haiku"

    print(f"\nLaunching Claude Code (Selected Proxy Target: {selected_model} via {target_cli_model})\n")
    
    env = os.environ.copy()
    env["ANTHROPIC_BASE_URL"] = "http://localhost:4000"
    if api_key:
        env["ANTHROPIC_API_KEY"] = api_key
    
    # Resolve the underlying executable directly to bypass recursive shell alias execution
    raw_claude = shutil.which("claude")
    if not raw_claude or raw_claude.endswith("claude.py"):
        raw_claude = shutil.which("npx") and "npx @anthropic-ai/claude-code" or "/usr/local/bin/claude"

    if "npx" in raw_claude:
        cmd = ["npx", "@anthropic-ai/claude-code", "--model", target_cli_model]
    else:
        cmd = [raw_claude, "--model", target_cli_model]

    try:
        subprocess.run(cmd, env=env)
    except FileNotFoundError:
        print(f"Error: Claude executable not found.")

if __name__ == "__main__":
    main()
