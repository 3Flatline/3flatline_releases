# Check for Homebrew
if ! command -v brew &>/dev/null; then
  echo "Homebrew not found. Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
  echo "Homebrew is already installed."
fi

# Install Ollama if not installed
if ! command -v ollama &>/dev/null; then
  echo "Ollama not found. Installing Ollama..."
  brew install ollama
else
  echo "Ollama is already installed."
fi

echo "Pulling Ollama models..."
ollama pull nomic-embed-text:v1.5
ollama pull qwen2.5-coder:32b-instruct-q4_0

echo "Make sure that ollama allows incoming connections and the correct context window size. Add the following environment variables

export OLLAMA_HOST=0.0.0.0
export OLLAMA_CONTEXT_LENGTH=120000"
