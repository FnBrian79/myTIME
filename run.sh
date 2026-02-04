#!/usr/bin/env bash
# run.sh - myTIME Sovereign Bootstrapper

set -e

echo "⏳ Initializing myTIME Gauntlet on The Beast..."

# Create Infrastructure
mkdir -p learning_repo/{vault,metadata} logs/{foreman,actor,architect,auditor,steward} config

# Generate AEAD Master Key if missing
if [ ! -f config/master.key ]; then
  echo "🔑 Generating v2.4 AEAD Master Key..."
  # Uses python to generate a secure 32-byte key
  python3 -c "import os; print(os.urandom(32).hex())" > config/master.key
  chmod 600 config/master.key
fi

# Create Minimal Config
if [ ! -f config/settings.yaml ]; then
  cat > config/settings.yaml <<EOF
system:
  mode: "GAUNTLET_BURN"
  version: "2.4"
  log_level: "INFO"
crypto:
  key_path: "/app/config/master.key"
EOF
fi

echo "🚀 Launching the Building Crew..."
docker compose up --build -d

echo "✅ System is live. Run './check_health.sh' to verify."
