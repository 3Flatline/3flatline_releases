#!/bin/sh
set -e

# Create config.ini from environment variables
cat > config.ini <<EOF
[openai]
apikey = ${OPENAI_API_KEY}

[wintermute]
apikey = ${WINTERMUTE_API_KEY}

[database]
file = ${DATABASE_FILE:-database.sqlite}

[loadbalancer]
port = ${LOADBALANCER_PORT:-7270}
endpoints = ${LOADBALANCER_ENDPOINTS:-}

[security]
noexploits = ${SECURITY_NOEXPLOITS:-false}
EOF

# Execute the command passed to the script
exec "$@"
