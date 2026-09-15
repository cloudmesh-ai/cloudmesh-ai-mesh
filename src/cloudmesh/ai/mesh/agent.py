import requests
import subprocess
import sys

# Configuration
API_URL = "http://localhost:4000/v1/chat/completions"
DEFAULT_MODEL = "gpu-primary"

SYSTEM_PROMPT = """
You are the Local AI Cluster Agent. 
You have access to a distributed compute environment:
- WHITE: Primary GPU node (vLLM)
- SPARK: Fallback CPU node (llama.cpp)
- LAPTOP: Control plane

Your goal is to assist with software engineering tasks while remaining aware of the cluster's local-only nature.
"""

def llm(prompt, model=DEFAULT_MODEL):
    try:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }
        response = requests.post(API_URL, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"❌ API Error: {str(e)}"
    except (KeyError, IndexError):
        return "❌ Error: Received an unexpected response format from the LLM."

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            return result.stdout if result.stdout else "Command executed successfully (no output)."
        else:
            return f"❌ Command failed with exit code {result.returncode}:\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return "❌ Error: Command timed out after 5 minutes."
    except Exception as e:
        return f"❌ Unexpected error running command: {str(e)}"

def main():
    print("🤖 Local AI Cluster Agent Active")
    print("Commands: 'run <cmd>' to execute shell, 'model <name>' to switch models, 'exit' to quit")
    print("-" * 50)

    current_model = DEFAULT_MODEL

    while True:
        try:
            user_input = input(f"[{current_model}] agent> ").strip()
            if not user_input:
                continue
            
            if user_input.lower() == 'exit':
                print("Shutting down agent...")
                break
            
            if user_input.startswith("run "):
                cmd = user_input[4:].strip()
                print(f"Executing: {cmd}...")
                print(run_command(cmd))
            
            elif user_input.startswith("model "):
                current_model = user_input[6:].strip()
                print(f"Switched to model: {current_model}")
            
            else:
                print("Thinking...")
                print(llm(user_input, model=current_model))
                
        except KeyboardInterrupt:
            print("\nShutting down agent...")
            break

if __name__ == "__main__":
    main()