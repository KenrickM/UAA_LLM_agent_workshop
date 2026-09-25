#!/bin/bash

CLEAN_URL="https://throughout-spell-preferences-derek.trycloudflare.com"
BASE_URL="${CLEAN_URL}/v1"
MODEL_NAME="/models/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf"

echo "⚙️ Configuring Hermes Agent Profile for Qwen 3.6 35B GGUF..."

mkdir -p /home/vscode/.hermes

# 1. Write config.yaml directly for Hermes Dashboard UI
cat << CONFIG > /home/vscode/.hermes/config.yaml
model: "${MODEL_NAME}"
provider: "custom"
base_url: "${BASE_URL}"
api_key: "none"
context_length: 8192

# Enable local Codespace tool execution
terminal:
  backend: "local"
  enabled: true

tools:
  file_read: true
  file_write: true
  terminal_execute: true
CONFIG

# 2. Update CLI state
hermes config set provider custom
hermes config set base_url "${BASE_URL}"
hermes config set model "${MODEL_NAME}"
hermes config set api_key "none"
hermes config set context_length 8192

echo "🚀 Starting Hermes Dashboard on Port 9119..."
hermes dashboard --port 9119
