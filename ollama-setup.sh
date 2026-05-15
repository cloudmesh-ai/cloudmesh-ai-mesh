n Machine: white (GPU Server)
1. Stop any existing Ollama service (if running):

Bash
sudo systemctl stop ollama
2. Launch Ollama in user mode with custom port:

Bash
export OLLAMA_HOST=127.0.0.1:18123
ollama serve
3. Download recommended coding model (separate terminal):

Bash
ollama pull qwen2.5-coder:32b
On Your Laptop
1. Establish the SSH tunnel:

Bash
ssh -L 18123:127.0.0.1:18123 white
2. Configure Cline (In VS Code Settings):

API Provider: Ollama

Base URL: http://localhost:18123

Model ID: qwen2.5-coder:32b

Optional: Automation (Laptop ~/.bashrc or ~/.zshrc)
Bash
alias tunnel-white='ssh -fN -L 18123:127.0.0.1:18123 white'