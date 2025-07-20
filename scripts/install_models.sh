# Install Ollama if not installed
if ! command -v ollama &>/dev/null; then
  echo "Ollama not found."
else
    echo "Pulling Ollama models..."
    ollama pull nomic-embed-text:v1.5
    ollama pull qwen2.5-coder:32b-instruct-q4_0

    echo "Make sure that ollama allows incoming connections and the correct context window size. Add the following environment variables

    export OLLAMA_HOST=0.0.0.0
    export OLLAMA_CONTEXT_LENGTH=120000"
fi
