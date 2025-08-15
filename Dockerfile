# Use a slim Python image as a base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install necessary tools and dependencies
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    tar \
    npm \
    && npm install -g tree-sitter-cli \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
RUN pip install tree-sitter>=0.25.0 tree-sitter-language-pack>=0.9.0


# Add build argument for target architecture
ARG TARGETARCH

# Copy server binaries to ensure they are not excluded by .dockerignore
COPY 3flatline-server_*_linux /app/

# Copy application files
COPY . /app

# Select and prepare the server binary for the target architecture
RUN set -e; \
    if [ "${TARGETARCH}" = "amd64" ]; then \
        mv 3flatline-server_x86_64_linux 3flatline-server; \
    elif [ "${TARGETARCH}" = "arm64" ]; then \
        mv 3flatline-server_arm64_linux 3flatline-server; \
    else \
        echo "Unsupported architecture: ${TARGETARCH}" >&2; exit 1; \
    fi; \
    chmod +x 3flatline-server


# Create config file from example
RUN cp config.ini.example config.ini

# Expose web UI port from README
EXPOSE 7270

# Default command to run the server. This will populate config.ini from environment variables and then start the server.
CMD ["/bin/sh", "-c", "sed -i \"s|^    apikey=.*|    apikey=${OPENAI_API_KEY}|\" config.ini && sed -i \"s|^    key=.*|    key=${WINTERMUTE_API_KEY}|\" config.ini && sed -i \"s|^    file=.*|    file=${DATABASE_FILE:-database.sqlite}|\" config.ini && sed -i \"s|^    port=.*|    port=${LOADBALANCER_PORT:-11435}|\" config.ini && sed -i \"s|^    endpoints=.*|    endpoints=${LOADBALANCER_ENDPOINTS:-0.0.0.0}|\" config.ini && sed -i \"s|^    no_exploits=.*|    no_exploits=${SECURITY_NOEXPLOITS:-true}|\" config.ini && exec ./3flatline-server -config config.ini"]
