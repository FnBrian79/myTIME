# myTIME Setup Guide

## 🚀 Quick Start - "One Command to Rule Them All"

The myTIME Gauntlet uses a **Sovereign Bootstrap** system that sets up everything you need in one command:

```bash
./run.sh
```

This script will:
1. ✅ Create the directory structure (`learning_repo/`, `logs/`, `config/`)
2. 🔑 Generate a secure v2.4 AEAD Master Key
3. ⚙️  Create the minimal configuration file
4. 🐳 Build and launch all Docker containers

## 📋 Prerequisites

- **Docker** and **Docker Compose** (v2.0+)
- **Python 3.11+** (for key generation)
- **NVIDIA GPU** (optional, for Architect deepfake detection)
- **ElevenLabs API Key** (optional, for voice cloning)

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```bash
# ElevenLabs API Key (for voice cloning)
ELEVENLABS_API_KEY=your_api_key_here

# Optional: Custom ports
# FOREMAN_PORT=8080
# ACTOR_PORT=8000
# ARCHITECT_PORT=5000
# AUDITOR_PORT=5001
# STEWARD_PORT=8080
```

### SIP Configuration

To connect your phone system, edit `config/asterisk/pjsip.conf` with your:
- Google Voice credentials
- Twilio SIP credentials
- Or any SIP-compatible phone provider

## 🏥 Health Check

After starting the system, verify all services are running:

```bash
./check_health.sh
```

This will check:
- ✅ All 5 services (Foreman, Actor, Architect, Auditor, Steward)
- ✅ Supporting services (Ollama, Asterisk)
- ✅ Directory structure and keys

### Manual Health Checks

You can also check individual services:

```bash
# Foreman (Triage)
curl http://localhost:8080/health

# Actor (Method Actor Service)
curl http://localhost:8000/health

# Architect (Deepfake Detection)
curl http://localhost:5000/health

# Auditor (AEAD Crypto)
curl http://localhost:5001/health

# Steward (Gamification)
curl http://localhost:8080/health
```

## 🔐 Security - The Sovereign Way

### AEAD Master Key

The bootstrap script generates a **256-bit master key** using secure random bytes:
- Stored at `config/master.key` (600 permissions)
- Used for encrypting all transcripts and call data
- Each persona has its own encryption context (preventing cross-persona decryption)

### Key Features

- **Persona Separation**: Hazel's transcripts can't be decrypted as Brandon's
- **AEAD (Authenticated Encryption with Associated Data)**: Prevents tampering
- **No Hardcoded Keys**: Generated fresh on each installation

### Using Crypto Utils

```python
from services.auditor.crypto_utils import encrypt_transcript, decrypt_transcript, load_master_key

# Load the master key
master_key = load_master_key('/app/config/master.key')

# Encrypt a transcript
encrypted = encrypt_transcript('hazel', 'Hello from Hazel!', master_key)

# Decrypt it
decrypted = decrypt_transcript('hazel', encrypted, master_key)
```

## 📊 Accessing Services

### Steward Dashboard

Open your browser to view the gamification dashboard:
```
http://localhost:8080
```

Features:
- Real-time leaderboard
- Your credits and level
- Time wasted statistics

### Actor Service API

```bash
# Set a persona
curl -X POST http://localhost:8000/set_persona \
  -H "Content-Type: application/json" \
  -d '{"persona_name": "hazel"}'

# Generate a response
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"transcript_history": ["Scammer: This is the IRS."]}'
```

## 🛠️ Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose logs [service-name]

# Rebuild a specific service
docker compose up --build [service-name]
```

### Ollama Model Missing

If the Actor can't connect to Ollama:

```bash
# Pull the LLaMA model
docker exec -it gauntlet-actor ollama pull llama3
```

### GPU Not Detected

If the Architect can't find your GPU:

```bash
# Install NVIDIA Container Toolkit
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

# Verify GPU is available
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

## 🧪 Testing

Run the test suite:

```bash
# Test crypto utilities
python3 test_crypto.py

# Test infrastructure
python3 test_infrastructure.py
```

## 🔄 Updating

To update the system:

```bash
# Pull latest changes
git pull

# Rebuild containers
docker compose down
docker compose up --build -d
```

## 🗑️ Clean Uninstall

To completely remove myTIME:

```bash
# Stop and remove containers
docker compose down -v

# Remove generated files
rm -rf learning_repo logs config/master.key config/settings.yaml

# Remove test files (optional)
rm test_crypto.py test_infrastructure.py
```

## 📞 Phone Integration

### Google Voice Setup

1. Enable Google Voice forwarding to SIP
2. Update `config/asterisk/pjsip.conf`:
   ```ini
   [google-voice]
   type=registration
   outbound_auth=google-voice-auth
   server_uri=sip:sip.google.com
   client_uri=sip:yourphonenumber@sip.google.com
   ```

### Call Flow

1. **Scammer calls** → Asterisk receives call
2. **Foreman** triages the call (known scammer?)
3. **Actor** engages with selected persona
4. **Architect** analyzes voice for deepfake detection
5. **Auditor** encrypts and stores transcript
6. **Steward** awards credits and XP

## 🎮 Gamification System

- **10 credits per minute** of scammer time wasted
- **Multipliers:**
  - 2x for unique/new scams
  - 1.5x for AI-on-AI detection
  - 2x for voice cloning detected
  - 5x for "myTIME" (live Master-Student handoff)

## 🔮 Next Steps

- Configure your SIP credentials
- Customize personas in `services/actor/personas.yaml`
- Set up your ElevenLabs voice clone
- Connect your phone number
- Start wasting scammer time!

---

**Built for the future of society. Better than we were yesterday.** 🛡️
