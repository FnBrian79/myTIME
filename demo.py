#!/usr/bin/env python3
"""
Demo script showing the myTIME infrastructure in action
"""

import os
import sys

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")

def print_section(title):
    print(f"\n{'─' * 70}")
    print(f"  {title}")
    print('─' * 70)

def show_directory_structure():
    print_header("myTIME Directory Structure")
    
    print("📁 myTIME/")
    print("├── 🔧 run.sh                   # Bootstrap script")
    print("├── 🏥 check_health.sh          # Health verification")
    print("├── 📖 README.md                # Project overview")
    print("├── 📖 SETUP.md                 # Detailed setup guide")
    print("├── 🐳 docker-compose.yml       # Service orchestration")
    print("│")
    print("├── 📂 config/")
    print("│   ├── 🔑 master.key           # Generated AEAD key (600)")
    print("│   ├── ⚙️  settings.yaml        # System configuration")
    print("│   ├── 🎤 voice_settings.yaml   # Voice cloning config")
    print("│   └── 📂 asterisk/")
    print("│       ├── extensions.conf")
    print("│       └── pjsip.conf")
    print("│")
    print("├── 📂 learning_repo/")
    print("│   ├── 📂 vault/               # Encrypted transcripts")
    print("│   └── 📂 metadata/            # Call metadata")
    print("│")
    print("├── 📂 logs/")
    print("│   ├── 📂 foreman/")
    print("│   ├── 📂 actor/")
    print("│   ├── 📂 architect/")
    print("│   ├── 📂 auditor/")
    print("│   └── 📂 steward/")
    print("│")
    print("└── 📂 services/")
    print("    ├── 📂 foreman/             # Call orchestration")
    print("    ├── 📂 actor/               # AI personas")
    print("    ├── 📂 architect/           # Deepfake detection")
    print("    ├── 📂 auditor/             # AEAD encryption")
    print("    └── 📂 steward/             # Gamification")

def show_crypto_demo():
    print_header("AEAD Crypto System Demo")
    
    sys.path.insert(0, '/home/runner/work/myTIME/myTIME/services/auditor')
    from crypto_utils import encrypt_transcript, decrypt_transcript, load_master_key
    
    # Load key
    master_key = load_master_key('/home/runner/work/myTIME/myTIME/config/master.key')
    print(f"🔑 Master Key: {master_key[:16]}...{master_key[-16:]}")
    print(f"   Length: {len(master_key)} hex chars (32 bytes)")
    
    print_section("Encrypting Transcript for Persona 'Hazel'")
    
    transcript = "IRS Scammer: You owe $5,000 in back taxes."
    print(f"📝 Original: {transcript}")
    
    encrypted = encrypt_transcript("hazel", transcript, master_key)
    print(f"🔐 Encrypted: {encrypted[:20].hex()}... ({len(encrypted)} bytes)")
    
    decrypted = decrypt_transcript("hazel", encrypted, master_key)
    print(f"🔓 Decrypted: {decrypted}")
    print(f"✅ Match: {decrypted == transcript}")
    
    print_section("Persona Separation Test")
    print("Attempting to decrypt Hazel's data as Brandon...")
    try:
        decrypt_transcript("brandon", encrypted, master_key)
        print("❌ SECURITY BREACH: Wrong persona decrypted!")
    except Exception as e:
        print(f"✅ Security Working: Decryption failed (as expected)")
        print(f"   Error: {str(e)[:60]}...")

def show_service_overview():
    print_header("Service Architecture")
    
    services = {
        "Foreman": {
            "port": 8080,
            "role": "Orchestrates call hand-offs and persona selection",
            "health": "/health",
            "key_features": ["SIP Bridge", "Call Triage", "Ghost Buffer"]
        },
        "Actor": {
            "port": 8000,
            "role": "Low-latency voice models that waste scammer time",
            "health": "/health",
            "key_features": ["Multiple Personas", "Hallucination Engine", "AI Detection"]
        },
        "Architect": {
            "port": 5000,
            "role": "Quantizes call data and detects deepfakes",
            "health": "/health",
            "key_features": ["Wav2Vec 2.0", "Real-time Analysis", "Pattern Recognition"]
        },
        "Auditor": {
            "port": 5001,
            "role": "Ensures cryptographic integrity via AEAD",
            "health": "/health",
            "key_features": ["AEAD Encryption", "Persona Separation", "Forensic Ledger"]
        },
        "Steward": {
            "port": 8080,
            "role": "Manages gamification and credit ledger",
            "health": "/health",
            "key_features": ["XP System", "Leaderboards", "Credit Multipliers"]
        }
    }
    
    for name, info in services.items():
        print(f"\n🎯 {name} (Port {info['port']})")
        print(f"   Role: {info['role']}")
        print(f"   Health: http://localhost:{info['port']}{info['health']}")
        print(f"   Features: {', '.join(info['key_features'])}")

def show_setup_flow():
    print_header("Setup Flow")
    
    steps = [
        ("1️⃣", "Run ./run.sh", "Creates directories, generates keys, starts containers"),
        ("2️⃣", "Run ./check_health.sh", "Verifies all services are active"),
        ("3️⃣", "Pull Ollama models", "docker exec -it gauntlet-actor ollama pull llama3"),
        ("4️⃣", "Configure SIP", "Edit config/asterisk/pjsip.conf with phone credentials"),
        ("5️⃣", "Start wasting time!", "Scammers call → myTIME engages → Credits earned"),
    ]
    
    for emoji, title, desc in steps:
        print(f"{emoji} {title}")
        print(f"   → {desc}\n")

def show_health_check_output():
    print_header("Health Check Output (Simulated)")
    
    print("🏥 Checking myTIME Service Health...")
    print()
    print("Checking Foreman (Triage)... \033[0;32mACTIVE\033[0m")
    print("Checking Actor (Service)... \033[0;32mACTIVE\033[0m")
    print("Checking Architect... \033[0;32mACTIVE\033[0m")
    print("Checking Auditor... \033[0;32mACTIVE\033[0m")
    print("Checking Steward... \033[0;32mACTIVE\033[0m")
    print()
    print("Checking Ollama (Actor Backend)...")
    print("\033[0;32mOllama container is running\033[0m")
    print()
    print("Checking Asterisk (Foreman SIP)...")
    print("\033[0;32mAsterisk container is running\033[0m")
    print()
    print("📊 Quick Stats:")
    print("   - Directory Structure: \033[0;32m✓\033[0m")
    print("   - Master Key: \033[0;32m✓\033[0m")
    print("   - Config File: \033[0;32m✓\033[0m")
    print()
    print("🛡️ The Building Crew status check complete.")

if __name__ == "__main__":
    show_directory_structure()
    show_crypto_demo()
    show_service_overview()
    show_setup_flow()
    show_health_check_output()
    
    print("\n" + "=" * 70)
    print("  🎉 myTIME Infrastructure Demo Complete!")
    print("  Built for the future of society. Better than we were yesterday.")
    print("=" * 70 + "\n")
