#!/usr/bin/env bash
set -euo pipefail

# Usage: ./deploy.sh <elastic-ip>
# Example: ./deploy.sh 54.123.45.67

HOST="${1:?Usage: ./deploy.sh <elastic-ip-or-hostname>}"

ssh -i ~/.ssh/idleclaw-server-ssh.pem "ubuntu@${HOST}" 'source ~/.local/bin/env && \
  cd /opt/idleclaw && git pull && \
  cd server && uv sync && \
  cd ../frontend && npm install && npm run build && \
  sudo systemctl restart idleclaw-server idleclaw-frontend'
