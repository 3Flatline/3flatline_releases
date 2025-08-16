# Use a slim Python image as a base
FROM python:3.12-slim

WORKDIR /app

# Install necessary tools and dependencies
RUN apt-get update && apt-get install -y \
    curl \
    meson \
    jq \
    tar \
    npm \
    && npm install -g tree-sitter-cli \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
RUN pip install tree-sitter tree-sitter-language-pack

# setup and install rizin
RUN git clone https://github.com/rizinorg/rizin

WORKDIR /app/rizin

RUN meson setup build
RUN meson compile -C build
RUN meson install -C build

WORKDIR /app

# Download and extract the latest release
RUN LATEST_RELEASE_URL=$(curl -s https://api.github.com/repos/3Flatline/3flatline_releases/releases/latest | jq -r '.assets[] | select(.name | endswith(".tar.gz")) | .browser_download_url') && \
    curl -L -o 3flatline.tar.gz "${LATEST_RELEASE_URL}" && \
    tar -xzvf 3flatline.tar.gz --strip-components=1 && \
    rm 3flatline.tar.gz

# Determine architecture and select server binary
RUN ARCH=$(dpkg --print-architecture) && \
    set -e; \
    if [ "${ARCH}" = "amd64" ]; then \
        mv 3flatline-server_x86_64_linux 3flatline-server; \
    elif [ "${ARCH}" = "arm64" ]; then \
        mv 3flatline-server_arm64_linux 3flatline-server; \
    else \
        echo "Unsupported architecture: ${ARCH}" >&2; exit 1; \
    fi; \
    chmod +x 3flatline-server


# Create config file from example
RUN cp config.ini.example config.ini

# Expose web UI port from README
EXPOSE 7270

# Default command to run the server. This will populate config.ini from environment variables and then start the server.
CMD ["/bin/sh", "-c", "sed -i \"s|^    apikey=.*|    apikey=${OPENAI_API_KEY}|\" config.ini && sed -i \"s|^    key=.*|    key=${WINTERMUTE_API_KEY}|\" config.ini && sed -i \"s|^    file=.*|    file=${DATABASE_FILE:-database.sqlite}|\" config.ini && sed -i \"s|^    port=.*|    port=${LOADBALANCER_PORT:-11435}|\" config.ini && sed -i \"s|^    endpoints=.*|    endpoints=${LOADBALANCER_ENDPOINTS:-0.0.0.0}|\" config.ini && sed -i \"s|^    no_exploits=.*|    no_exploits=${SECURITY_NOEXPLOITS:-true}|\" config.ini && exec ./3flatline-server -config config.ini"]

