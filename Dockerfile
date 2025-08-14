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

# Download and extract the latest 3flatline release for linux
RUN LATEST_RELEASE_URL=$(curl -s https://api.github.com/repos/3Flatline/3flatline_releases/releases/latest | jq -r '.assets[] | select(.name | test(".zip$")) | .browser_download_url' | head -n1) && \
echo "Downloading release from $LATEST_RELEASE_URL" && \
curl -sL $LATEST_RELEASE_URL | unzip  && \
mv 3flatline-server_x86_64_linux 3flatline-server && \
chmod +x 3flatline-server

# Copy python scripts and install dependencies
COPY scripts/ /app/scripts/
RUN uv pip install /app/scripts/

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Expose web UI port from README
EXPOSE 7270

# Set entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]

# Default command to run the server
CMD ["./3flatline-server", "-config", "config.ini"]
