#!/bin/bash

CLEAN_URL="https://throughout-spell-preferences-derek.trycloudflare.com"
BASE_URL="${CLEAN_URL}/v1"
MODEL_NAME="/models/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf"

echo "⚙️ Configuring Hermes Agent Profile & Overriding Context Window Checks..."

mkdir -p /home/vscode/.hermes

# Write config.yaml with root AND auxiliary compression context overrides
cat << CONFIG > /home/vscode/.hermes/config.yaml
model: "${MODEL_NAME}"
provider: "custom"
base_url: "${BASE_URL}"
api_key: "none"
context_length: 65536
max_tokens: 2048

# Override the detected 8K per-slot limit for the Hermes compression engine
auxiliary:
  compression:
    model: "${MODEL_NAME}"
    context_length: 65536

terminal:
  backend: "local"
  enabled: true

tools:
  file_read: true
  file_write: true
  terminal_execute: true
CONFIG

# Update Hermes CLI internal configuration state
hermes config set provider custom
hermes config set base_url "${BASE_URL}"
hermes config set model "${MODEL_NAME}"
hermes config set api_key "none"
hermes config set context_length 65536
hermes config set max_tokens 2048

echo "🚀 Starting Hermes Dashboard..."
hermes dashboard --port 9119
