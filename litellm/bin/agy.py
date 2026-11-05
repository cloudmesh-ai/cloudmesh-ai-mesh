#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

# please note that fall back to sk-1234 does not work and should be removed

# Map your friendly shortcuts directly to agy's recognized model names
MODELS_LIST = [
    ("gemini-3.8-flash-high", ["gemma4", "jetstream.gemma4", "gemini-high"], "Gemini 3.8 Flash (High / Gemma mapping)"),
    ("gpt-oss-120b-medium", ["gpt", "jetstream.gpt", "gpt-medium"], "GPT-OSS 120B (Medium)"),
    ("claude-sonnet-4-6", ["qwen", "jetstream.qwen", "sonnet"], "Claude Sonnet 4.6 (Qwen mapping)"),
    ("gemini-3.8-flash-medium", ["muse", "jetstream.muse", "gemini-med"], "Gemini 3.8 Flash (Medium / Muse mapping)"),
    ("gemini-3.8-flash-low", ["gemini", "gemini-low"], "Gemini 3.8 Flash (Low)"),
]

MODEL_MAP = {}
NUMERIC_MAP = {}
for idx, (model_id, shortcuts, _) in enumerate(MODELS_LIST, 1):
    NUMERIC_MAP[str(idx)] = model_id
    for sc in shortcuts:
        MODEL_MAP[sc] = model_id

def get_litellm_key():
    env_path = Path.home() / ".config" / "litellm" / "env"
    if not env_path.is_file():
        return "sk-1234"
    try:
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("LITELLM_MASTER_KEY="):
                    key = line.split("=", 1)[1].strip()
                    return key.strip('"').strip("'")
    except Exception:
        pass
    return "sk-1234"

def select_model_interactively():
    print("Select a model:")
    for idx, (model_id, shortcuts, desc) in enumerate(MODELS_LIST, 1):
        shortcuts_str = ", ".join(shortcuts)
        print(f"  [{idx}] {desc} ({model_id}) [shortcuts: {shortcuts_str}]")
    
    choice = input("Enter number, shortcut, or press Enter to skip: ").strip()
    if not choice:
        return None
    if choice in NUMERIC_MAP:
        return NUMERIC_MAP[choice]
    if choice in MODEL_MAP:
        return MODEL_MAP[choice]
    print(f"Invalid selection: '{choice}'")
    sys.exit(1)

def main():
    args = sys.argv[1:]
    model_arg = None

    if args:
        first_arg = args[0]
        if first_arg in MODEL_MAP:
            args.pop(0)
            model_arg = MODEL_MAP[first_arg]
        elif first_arg in NUMERIC_MAP:
            args.pop(0)
            model_arg = NUMERIC_MAP[first_arg]

    if not model_arg:
        model_arg = select_model_interactively()

    if model_arg:
        print(f"-> Using model [{model_arg}]")

    env = os.environ.copy()
    env["OPENAI_API_BASE"] = "http://localhost:4000/v1"
    env["OPENAI_API_KEY"] = get_litellm_key()

    agy_cmd = ["agy"]
    if model_arg:
        agy_cmd.extend(["--model", model_arg])
    agy_cmd.extend(args)

    try:
        result = subprocess.run(agy_cmd, env=env)
        sys.exit(result.returncode)
    except FileNotFoundError:
        print("Error: 'agy' command not found in your environment PATH.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()#!/usr/bin/env python3
import os
import sys
import json
import subprocess
from pathlib import Path

# Define models with their full ID, shortcuts, and display description
MODELS_LIST = [
    ("jetstream-gemma4", ["gemma4", "jetstream.gemma4"], "Jetstream Gemma 4"),
    ("jetstream-gpt-oss-120b", ["gpt", "jetstream.gpt"], "Jetstream GPT-OSS 120B"),
    ("jetstream-qwen3", ["qwen", "jetstream.qwen"], "Jetstream Qwen 3"),
    ("jetstream-muse-glimmer", ["muse", "jetstream.muse"], "Jetstream Muse Glimmer"),
    ("gemini-flash-direct", ["gemini"], "Gemini Flash Direct"),
]

MODEL_MAP = {}
NUMERIC_MAP = {}
for idx, (model_id, shortcuts, _) in enumerate(MODELS_LIST, 1):
    NUMERIC_MAP[str(idx)] = model_id
    for sc in shortcuts:
        MODEL_MAP[sc] = model_id

def get_litellm_key():
    env_path = Path.home() / ".config" / "litellm" / "env"
    if not env_path.is_file():
        return "sk-1234"
    try:
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("LITELLM_MASTER_KEY="):
                    key = line.split("=", 1)[1].strip()
                    return key.strip('"').strip("'")
    except Exception:
        pass
    return "sk-1234"

def select_model_interactively():
    print("Select a model:")
    for idx, (model_id, shortcuts, desc) in enumerate(MODELS_LIST, 1):
        shortcuts_str = ", ".join(shortcuts)
        print(f"  [{idx}] {desc} ({model_id}) [shortcuts: {shortcuts_str}]")
    
    choice = input("Enter number, shortcut, or press Enter to skip: ").strip()
    if not choice:
        return None
    if choice in NUMERIC_MAP:
        return NUMERIC_MAP[choice]
    if choice in MODEL_MAP:
        return MODEL_MAP[choice]
    print(f"Invalid selection: '{choice}'")
    sys.exit(1)

def main():
    args = sys.argv[1:]
    model_arg = None

    if args:
        first_arg = args[0]
        if first_arg in MODEL_MAP:
            args.pop(0)
            model_arg = MODEL_MAP[first_arg]
        elif first_arg in NUMERIC_MAP:
            args.pop(0)
            model_arg = NUMERIC_MAP[first_arg]

    if not model_arg:
        model_arg = select_model_interactively()

    if model_arg:
        print(f"-> Using model [{model_arg}]")

    env = os.environ.copy()
    api_key = get_litellm_key()
    env["OPENAI_API_BASE"] = "http://localhost:4000/v1"
    env["OPENAI_API_KEY"] = api_key

    agy_cmd = ["agy"]
    
    if model_arg:
        # Pass inline settings JSON to force agy to accept custom model string over proxy
        settings_override = json.dumps({
            "model": model_arg,
            "custom_models": [model_arg]
        })
        agy_cmd.extend(["--settings", settings_override])

    agy_cmd.extend(args)

    try:
        result = subprocess.run(agy_cmd, env=env)
        sys.exit(result.returncode)
    except FileNotFoundError:
        print("Error: 'agy' command not found in your environment PATH.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

# Define models with their full ID, shortcuts, and display description
MODELS_LIST = [
    ("jetstream-gemma4", ["gemma4", "jetstream.gemma4"], "Jetstream Gemma 4"),
    ("jetstream-gpt-oss-120b", ["gpt", "jetstream.gpt"], "Jetstream GPT-OSS 120B"),
    ("jetstream-qwen3", ["qwen", "jetstream.qwen"], "Jetstream Qwen 3"),
    ("jetstream-muse-glimmer", ["muse", "jetstream.muse"], "Jetstream Muse Glimmer"),
    ("gemini-flash-direct", ["gemini"], "Gemini Flash Direct"),
]

MODEL_MAP = {}
NUMERIC_MAP = {}
for idx, (model_id, shortcuts, _) in enumerate(MODELS_LIST, 1):
    NUMERIC_MAP[str(idx)] = model_id
    for sc in shortcuts:
        MODEL_MAP[sc] = model_id

def get_litellm_key():
    env_path = Path.home() / ".config" / "litellm" / "env"
    if not env_path.is_file():
        return "sk-1234"
    try:
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("LITELLM_MASTER_KEY="):
                    key = line.split("=", 1)[1].strip()
                    return key.strip('"').strip("'")
    except Exception:
        pass
    return "sk-1234"

def select_model_interactively():
    print("Select a model:")
    for idx, (model_id, shortcuts, desc) in enumerate(MODELS_LIST, 1):
        shortcuts_str = ", ".join(shortcuts)
        print(f"  [{idx}] {desc} ({model_id}) [shortcuts: {shortcuts_str}]")
    
    choice = input("Enter number, shortcut, or press Enter to skip: ").strip()
    if not choice:
        return None
    if choice in NUMERIC_MAP:
        return NUMERIC_MAP[choice]
    if choice in MODEL_MAP:
        return MODEL_MAP[choice]
    print(f"Invalid selection: '{choice}'")
    sys.exit(1)

def main():
    args = sys.argv[1:]
    model_arg = None

    # Check if the first argument matches a shortcut or number directly
    if args:
        first_arg = args[0]
        if first_arg in MODEL_MAP:
            args.pop(0)
            model_arg = MODEL_MAP[first_arg]
        elif first_arg in NUMERIC_MAP:
            args.pop(0)
            model_arg = NUMERIC_MAP[first_arg]

    # If no model was passed via CLI, prompt interactively
    if not model_arg:
        model_arg = select_model_interactively()

    if model_arg:
        print(f"-> Using model [{model_arg}]")

    # Set up environment variables for LiteLLM proxy routing
    env = os.environ.copy()
    env["OPENAI_API_BASE"] = "http://localhost:4000/v1"
    env["OPENAI_API_KEY"] = get_litellm_key()

    # Build the agy command using the native --model flag
    agy_cmd = ["agy"]
    if model_arg:
        agy_cmd.extend(["--model", model_arg])
    agy_cmd.extend(args)

    try:
        result = subprocess.run(agy_cmd, env=env)
        sys.exit(result.returncode)
    except FileNotFoundError:
        print("Error: 'agy' command not found in your environment PATH.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

# Define models with their display name, string shortcuts, and full LiteLLM ID
MODELS_LIST = [
    ("jetstream-gemma4", ["gemma4", "jetstream.gemma4"], "Jetstream Gemma 4"),
    ("jetstream-gpt-oss-120b", ["gpt", "jetstream.gpt"], "Jetstream GPT-OSS 120B"),
    ("jetstream-qwen3", ["qwen", "jetstream.qwen"], "Jetstream Qwen 3"),
    ("jetstream-muse-glimmer", ["muse", "jetstream.muse"], "Jetstream Muse Glimmer"),
    ("gemini-flash-direct", ["gemini"], "Gemini Flash Direct"),
]

MODEL_MAP = {}
NUMERIC_MAP = {}
for idx, (model_id, shortcuts, _) in enumerate(MODELS_LIST, 1):
    NUMERIC_MAP[str(idx)] = model_id
    for sc in shortcuts:
        MODEL_MAP[sc] = model_id

def get_litellm_key():
    env_path = Path.home() / ".config" / "litellm" / "env"
    if not env_path.is_file():
        return "sk-1234"
    try:
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("LITELLM_MASTER_KEY="):
                    key = line.split("=", 1)[1].strip()
                    return key.strip('"').strip("'")
    except Exception:
        pass
    return "sk-1234"

def select_model_interactively():
    print("Select a model:")
    for idx, (model_id, shortcuts, desc) in enumerate(MODELS_LIST, 1):
        shortcuts_str = ", ".join(shortcuts)
        print(f"  [{idx}] {desc} ({model_id}) [shortcuts: {shortcuts_str}]")
    
    choice = input("Enter number, shortcut, or press Enter to skip: ").strip()
    if not choice:
        return None
    if choice in NUMERIC_MAP:
        return NUMERIC_MAP[choice]
    if choice in MODEL_MAP:
        return MODEL_MAP[choice]
    print(f"Invalid selection: '{choice}'")
    sys.exit(1)

def main():
    args = sys.argv[1:]
    model_arg = None

    # Check if the first argument matches a shortcut or number directly
    if args:
        first_arg = args[0]
        if first_arg in MODEL_MAP:
            args.pop(0)
            model_arg = MODEL_MAP[first_arg]
        elif first_arg in NUMERIC_MAP:
            args.pop(0)
            model_arg = NUMERIC_MAP[first_arg]

    # If no model was passed via CLI, prompt interactively
    if not model_arg:
        model_arg = select_model_interactively()

    if model_arg:
        print(f"-> Using model [{model_arg}]")

    # Set up environment variables for LiteLLM proxy routing
    env = os.environ.copy()
    env["OPENAI_API_BASE"] = "http://localhost:4000/v1"
    env["OPENAI_API_KEY"] = get_litellm_key()

    # Build agy command. If agy supports a model flag, pass it here. 
    # Otherwise, pass the model name if agy accepts it as an argument or flag.
    agy_cmd = ["agy"]
    if model_arg:
        # Check if agy takes a model flag, or if we pass it through environment/arguments
        # Many CLIs accept --model or similar. Let's append it if supported, 
        # or check agy's help output. For now, let's inject it if agy expects a flag:
        agy_cmd.extend(["--model", model_arg])

    agy_cmd.extend(args)

    try:
        result = subprocess.run(agy_cmd, env=env)
        sys.exit(result.returncode)
    except FileNotFoundError:
        print("Error: 'agy' command not found in your environment PATH.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
