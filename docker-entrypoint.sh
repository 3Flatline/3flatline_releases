#!/bin/sh
set -e

# Create config.ini from environment variables
cat > config.ini <<EOF
[openai]
apikey = ${OPENAI_API_KEY}

[wintermute-apikey]
key = ${WINTERMUTE_API_KEY}

[database]
file = ${DATABASE_FILE:-database.sqlite}

[loadbalancer]
port = ${LOADBALANCER_PORT:-11435}
endpoints = ${LOADBALANCER_ENDPOINTS:-0.0.0.0}

[security]
no_exploits = ${SECURITY_NOEXPLOITS:-true}
EOF

# Execute the command passed to the script
exec "$@"
