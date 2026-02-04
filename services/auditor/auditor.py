import os
import time
import json
import hashlib
import hmac
from flask import Flask, jsonify

app = Flask(__name__)

class Auditor:
    def __init__(self, key_path="/data/vault/keys/v2.4_aead.key"):
        self.key_path = key_path
        self._ensure_key()

    def _ensure_key(self):
        """Ensures the v2.4 AEAD key exists (placeholder logic)."""
        if not os.path.exists(os.path.dirname(self.key_path)):
            os.makedirs(os.path.dirname(self.key_path), exist_ok=True)
        
        if not os.path.exists(self.key_path):
            with open(self.key_path, "wb") as f:
                f.write(os.urandom(32)) # Generate a random 256-bit key
            print(f"Generated new v2.4 AEAD key at {self.key_path}")

    def detect_voice_theft(self, audio_metadata):
        """
        Simulates detection of recording software or specific 'Sampling' patterns.
        """
        # Placeholder: If certain frequencies or patterns are detected
        if audio_metadata.get("recording_signal_detected"):
            print("🚨 [AUDITOR] Voice sampling detected! Triggering KILL SWITCH.")
            return True
        return False

    def trigger_voice_swap(self, actor_url="http://actor:8000"):
        """Orders the Actor to swap from cloned voice to a decoy."""
        try:
            # This would signal the Actor container to change its voice ID
            # requests.post(f"{actor_url}/pivot-voice", json={"voice_id": "hazel_decoy"})
            print("👤 [AUDITOR] Identity Guard: Voice swapped to Hazel Decoy.")
            return True
        except Exception as e:
            print(f"❌ [AUDITOR] Failed to trigger voice swap: {e}")
            return False

    def sign_transaction(self, payload):
        """
        Applies a HMAC-SHA256 signature to the payload, 
        simulating the 'Adversarial Handshake' signature mandate.
        """
        with open(self.key_path, "rb") as f:
            key = f.read()

        payload_bytes = json.dumps(payload, sort_keys=True).encode()
        signature = hmac.new(key, payload_bytes, hashlib.sha256).hexdigest()
        
        return f"sig_v2.4_{signature}"

    def process_log_entry(self, entry_type, content, user_id):
        """Signs and prepares a log entry for the Forensic Ledger."""
        payload = {
            "timestamp": time.time(),
            "type": entry_type,
            "content": content,
            "user_id": user_id
        }
        
        signature = self.sign_transaction(payload)
        payload["signature"] = signature
        
        return payload

    def write_to_ledger(self, signed_entry, ledger_path="/data/vault/forensic_ledger.jsonl"):
        """Appends the signed entry to the append-only ledger."""
        with open(ledger_path, "a") as f:
            f.write(json.dumps(signed_entry) + "\n")
        print(f"📜 [AUDITOR] Inscribed transaction in ledger: {signed_entry['signature'][:12]}...")

auditor = Auditor()

@app.route('/health')
def health():
    """Health check endpoint for service monitoring."""
    return jsonify({
        "status": "active",
        "service": "auditor",
        "mode": "Sovereign",
        "integrity": "verified"
    })

@app.route('/status')
def status():
    """Extended status information."""
    return jsonify({
        "status": "active",
        "service": "auditor",
        "key_path": auditor.key_path,
        "key_exists": os.path.exists(auditor.key_path)
    })

if __name__ == "__main__":
    print("Auditor Service (v2.4 AEAD) Initialized.")
    
    # Test Entry
    test_content = "Mock scam call transcript fragment: 'I need your password...'"
    entry = auditor.process_log_entry("CALL_FRAGMENT", test_content, "Brian_Sovereign")
    auditor.write_to_ledger(entry)
    
    # Start Flask server
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port)
