#!/usr/bin/env bash
set -euo pipefail

# Provision an EC2 instance as an IdleClaw seed node.
# Usage: seed-setup.sh <model1> [model2] ...
# Example: seed-setup.sh llama3.2:3b

if [ $# -eq 0 ]; then
  echo "Usage: seed-setup.sh <model1> [model2] ..."
  echo "Example: seed-setup.sh llama3.2:3b"
  exit 1
fi

MODELS=("$@")
REPO_URL="git@github.com:futurejunk/idleclaw.git"
INSTALL_DIR="/opt/idleclaw"

echo "=== IdleClaw Seed Node Setup ==="
echo "Models: ${MODELS[*]}"
echo ""

# --- 0. System packages ---
echo "[..] Updating package cache and installing prerequisites..."
sudo apt update -y
sudo apt install -y python3 python3-venv git
echo "[OK] System packages ready"

# --- 1. Install Ollama ---
if command -v ollama &>/dev/null; then
  echo "[OK] Ollama already installed"
else
  echo "[..] Installing Ollama..."
  curl -fsSL https://ollama.com/install.sh | sh
  echo "[OK] Ollama installed"
fi

# Ensure Ollama service is running
if systemctl is-active --quiet ollama 2>/dev/null; then
  echo "[OK] Ollama service running"
else
  echo "[..] Starting Ollama service..."
  sudo systemctl enable --now ollama
  echo "[OK] Ollama service started"
fi

# Wait for Ollama API to be ready
echo "[..] Waiting for Ollama API..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:11434/api/tags &>/dev/null; then
    echo "[OK] Ollama API ready"
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "FAIL: Ollama API not ready after 30s"
    exit 1
  fi
  sleep 1
done

# --- 2. Pull models ---
for model in "${MODELS[@]}"; do
  echo "[..] Pulling model: ${model}..."
  ollama pull "${model}"
  echo "[OK] Model ready: ${model}"
done

# --- 3. Clone repo ---
# Accept GitHub's SSH host key if not already known
ssh-keyscan -t ed25519 github.com >> ~/.ssh/known_hosts 2>/dev/null

if [ -d "${INSTALL_DIR}/.git" ]; then
  echo "[OK] Repo already cloned at ${INSTALL_DIR}"
  cd "${INSTALL_DIR}" && git pull
elif [ -d "${INSTALL_DIR}" ]; then
  echo "[..] Directory exists without git — initializing repo..."
  git clone "${REPO_URL}" /tmp/idleclaw-tmp
  cp -r /tmp/idleclaw-tmp/.git "${INSTALL_DIR}/.git"
  rm -rf /tmp/idleclaw-tmp
  sudo chown -R ubuntu:ubuntu "${INSTALL_DIR}"
  cd "${INSTALL_DIR}" && git checkout -- . && git pull
  echo "[OK] Git repo initialized"
else
  echo "[..] Cloning repo to ${INSTALL_DIR}..."
  sudo mkdir -p "${INSTALL_DIR}"
  sudo chown ubuntu:ubuntu "${INSTALL_DIR}"
  git clone "${REPO_URL}" "${INSTALL_DIR}"
  echo "[OK] Repo cloned"
fi

# --- 4. Set up node-agent venv ---
if [ -d "${INSTALL_DIR}/node-agent/.venv" ]; then
  echo "[OK] Node-agent venv already exists"
else
  echo "[..] Creating node-agent venv..."
  python3 -m venv "${INSTALL_DIR}/node-agent/.venv"
  echo "[OK] Venv created"
fi

echo "[..] Installing node-agent dependencies..."
"${INSTALL_DIR}/node-agent/.venv/bin/pip" install -e "${INSTALL_DIR}/node-agent"
echo "[OK] Dependencies installed"

# --- 5. Install systemd service ---
echo "[..] Installing systemd service..."
sudo cp "${INSTALL_DIR}/deploy/idleclaw-node.service" /etc/systemd/system/
sudo systemctl daemon-reload
echo "[OK] Systemd service installed"

# --- 6. Enable and start ---
echo "[..] Enabling and starting idleclaw-node..."
sudo systemctl enable --now idleclaw-node
echo "[OK] Node agent running"

echo ""
echo "=== Setup Complete ==="
echo "Check status: sudo systemctl status idleclaw-node"
echo "View logs:    journalctl -u idleclaw-node -f"
