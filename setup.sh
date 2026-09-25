#!/bin/bash

CLEAN_URL="https://throughout-spell-preferences-derek.trycloudflare.com"
BASE_URL="${CLEAN_URL}/v1"

echo "⚙️ Configuring Hermes Agent Profile..."

mkdir -p /home/vscode/.hermes

# Write configuration directly so the Dashboard UI picks up the provider on load
cat << CONFIG > /home/vscode/.hermes/config.yaml
model: "Qwen/Qwen3.8-27B-FP8"
provider: "custom"
base_url: "${BASE_URL}"
api_key: "none"
CONFIG

# Initialize CLI state
hermes config set provider custom
hermes config set base_url "${BASE_URL}"
hermes config set model "Qwen/Qwen3.8-27B-FP8"

echo "🚀 Starting Hermes Dashboard..."
hermes dashboard --port 9119

