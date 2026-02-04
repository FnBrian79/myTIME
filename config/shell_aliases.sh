#!/bin/bash
# myTIME CLI Aliases for the Building Crew
# Source this file: source config/shell_aliases.sh
# Or add to your ~/.bashrc or ~/.zshrc

# --- GitHub Copilot CLI (requires: gh auth login && gh extension install github/gh-copilot) ---
alias '??'='gh copilot suggest'
alias explain='gh copilot explain'

# --- myTIME Docker Shortcuts ---
alias dojo-up='docker compose up -d'
alias dojo-down='docker compose down'
alias dojo-logs='docker compose logs -f'
alias dojo-bridge='docker compose logs -f bridge'
alias dojo-steward='docker compose logs -f steward'

# --- Ollama Model Management ---
alias pull-llama='docker exec -it gauntlet-actor ollama pull llama3'
alias pull-mistral='docker exec -it gauntlet-actor ollama pull mistral'

# --- Combat Ring Quick Tests ---
alias bridge-health='curl -s http://localhost:8000/health | python3 -m json.tool'
alias steward-board='curl -s http://localhost:8080/api/leaderboard | python3 -m json.tool'
alias test-tts='curl -s -X POST http://localhost:8000/tts -H "Content-Type: application/json" -d "{\"text\": \"This is a test of the myTIME Combat Ring.\"}" -o /tmp/mytime_test.mp3 && echo "Audio saved to /tmp/mytime_test.mp3"'
