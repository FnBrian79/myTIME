# 🛡️ myTIME: The Sovereign Dojo

**"We don't block. We engage. We exhaust."**

`myTIME` is a decentralized system designed to turn the tide against social engineering. By utilizing the "Building Crew" model of specialized AI agents, we transform a nuisance into a high-fidelity "Learning Repo" for the future of Angelic Intelligence.

## 🚀 The Philosophy
Based on the principle of **"Giving it away to keep it,"** this template is a blueprint for a community-governed defense system. We aim for a future of no abuse by making the cost of scamming higher than the reward.

## 🧱 The Building Crew (Roles)
- **The Foreman:** Orchestrates call hand-offs and persona selection.
- **The Actor:** Low-latency voice models (Method Actors) that waste time.
- **The Architect:** Quantizes call data into actionable security patterns.
- **The Auditor:** Ensures cryptographic integrity via v2.4 AEAD Masks.
- **The Steward:** Manages the Gamification Engine and Credit Ledger.
- **The Bridge:** FastAPI WebSocket service bridging Foreman/Actor to ElevenLabs real-time voice synthesis.

## 📱 Mobile Client (React Native)
The `mobile/` directory contains a React Native Android app—the **Combat Ring** interface:
- Real-time WebSocket audio streaming from the Dojo Bridge
- Persona selector (Hazel / Brian / Winner)
- SIP/VOIP integration via `android.permission.USE_SIP`
- Cyberpunk UI matching the Steward dashboard aesthetic

## 🛠️ Stack & Deployment
- **Local:** Docker + Ollama (Testing ground: "The Beast" / "Rock 15").
- **Cloud:** GKE (Google Kubernetes Engine) for massive horizontal scaling.
- **Mobile:** React Native Android client with SIP/VOIP Combat Ring UI.
- **Voice:** ElevenLabs API via FastAPI WebSocket bridge (Dojo Bridge).
- **Privacy:** Sovereign data masking; no Meta/Facebook hooks.

## 🎮 Gamification
- **Wasted Time = Credits:** Earn credits to unlock premium "Maestro" features.
- **AI-on-AI Combat:** Detect scam bots and trigger the **Hallucination Engine**.
- **Leaderboards:** Join the ranks of the "Sovereign Sentinels."

## 🛠️ Quick Start for the Building Crew
1. **Clone the Repo:**
   ```bash
   git clone https://github.com/FnBrian79/scam-waster-gauntlet.git
   ```
2. **Configure your "Sovereign" Masks:**
   Drop your v2.4 AEAD keys into the `services/auditor/keys` folder to ensure all harvested scam data is cryptographically signed.
3. **Ignite the Gauntlet:**
   ```bash
   docker compose up -d
   ```
4. **Pull the Persona Models:**
   ```bash
   docker exec -it gauntlet-actor ollama pull llama3
   ```
5. **Connect to Google Voice:**
   Point your SIP credentials in `config/asterisk/pjsip.conf` to your Google Voice or Twilio number.
6. **Configure ElevenLabs (Dojo Bridge):**
   ```bash
   # Set your API key and voice IDs
   export ELEVENLABS_API_KEY="your_key_here"
   export ELEVENLABS_VOICE_ID="your_default_voice_id"
   # Voice config template at: services/bridge/elevenlabs.config.json
   ```
7. **Launch the Mobile Client:**
   ```bash
   cd mobile && npm install && npx react-native run-android
   ```

## 🏗️ Architecture

```
Android Client (React Native)
    ↕ WebSocket
Dojo Bridge (FastAPI + ElevenLabs TTS)
    ↕ HTTP
Foreman (Triage) → Actor (Persona + Ollama) → Architect (Vosk ASR)
    ↕                    ↕                          ↕
Auditor (AEAD)      Ollama (LLM)            Asterisk (SIP)
    ↕
Steward (Gamification)
```

---
*Built for the future of society. Better than we were yesterday.*
