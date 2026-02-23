#!/usr/bin/env bash
set -euo pipefail

# Update a seed node: pull latest code, reinstall deps, restart service.
# Usage: ./deploy-seed.sh <host> [--pull <model1> ...]
# Example: ./deploy-seed.sh 54.123.45.67
# Example: ./deploy-seed.sh 54.123.45.67 --pull llama3.2:3b

HOST=""
PULL_MODELS=()

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --pull)
      shift
      while [[ $# -gt 0 && "$1" != --* ]]; do
        PULL_MODELS+=("$1")
        shift
      done
      ;;
    *)
      if [ -z "$HOST" ]; then
        HOST="$1"
      else
        echo "Error: unexpected argument '$1'" >&2
        exit 1
      fi
      shift
      ;;
  esac
done

if [ -z "$HOST" ]; then
  echo "Usage: ./deploy-seed.sh <host> [--pull <model1> ...]"
  echo "Example: ./deploy-seed.sh 54.123.45.67"
  echo "Example: ./deploy-seed.sh 54.123.45.67 --pull llama3.2:3b"
  exit 1
fi

echo "=== Deploying to seed node: ${HOST} ==="

# Build the remote command
REMOTE_CMD='cd /opt/idleclaw && git pull && cd node-agent && .venv/bin/pip install -e .'

# Add model pulls if requested
for model in "${PULL_MODELS[@]}"; do
  REMOTE_CMD+=" && ollama pull $(printf '%q' "${model}")"
done

REMOTE_CMD+=' && sudo systemctl restart idleclaw-node'

echo "Running on ${HOST}..."
ssh "ubuntu@${HOST}" "${REMOTE_CMD}"

echo ""
echo "=== Deploy complete ==="
echo "Check status: ssh ubuntu@${HOST} 'sudo systemctl status idleclaw-node'"
