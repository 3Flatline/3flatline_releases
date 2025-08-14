# Use a slim Python image as a base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install necessary tools
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    tar \
    npm \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install tree-sitter-cli
RUN npm install -g tree-sitter-cli

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:${PATH}"

# Add build argument for target architecture
ARG TARGETARCH

# Download and extract the latest 3flatline release for linux based on architecture
RUN set -e; \
    if [ "${TARGETARCH}" = "amd64" ]; then \
        ARCH_STR="x86_64"; \
    elif [ "${TARGETARCH}" = "arm64" ]; then \
        ARCH_STR="arm"; \
    else \
        echo "Unsupported architecture: ${TARGETARCH}" >&2; exit 1; \
    fi; \
    LATEST_RELEASE_URL=$(curl -s https://api.github.com/repos/3Flatline/3flatline_releases/releases/latest | jq -r ".assets[] | select(.name | contains(\"linux\") and contains(\"${ARCH_STR}\") and endswith(\".zip\")) | .browser_download_url" | head -n 1); \
    if [ -z "${LATEST_RELEASE_URL}" ]; then \
        echo "Could not find a release for linux/${TARGETARCH}" >&2; exit 1; \
    fi; \
    echo "Downloading release from ${LATEST_RELEASE_URL}"; \
    curl -sL "${LATEST_RELEASE_URL}" | unzip; \
    mv "3flatline-server_${ARCH_STR}_linux" 3flatline-server; \
    chmod +x 3flatline-server

# Copy python scripts and install dependencies
COPY scripts/ /app/scripts/
RUN uv pip install /app/scripts/

# Expose web UI port from README
EXPOSE 7270

# Default command to run the server. This will create config.ini from environment variables and then start the server.
CMD ["/bin/sh", "-c", "echo \"[openai]\napikey = ${OPENAI_API_KEY}\n\n[wintermute-apikey]\nkey = ${WINTERMUTE_API_KEY}\n\n[database]\nfile = ${DATABASE_FILE:-database.sqlite}\n\n[loadbalancer]\nport = ${LOADBALANCER_PORT:-11435}\nendpoints = ${LOADBALANCER_ENDPOINTS:-0.0.0.0}\n\n[security]\nno_exploits = ${SECURITY_NOEXPLOITS:-true}\" > config.ini && exec ./3flatline-server -config config.ini"]
