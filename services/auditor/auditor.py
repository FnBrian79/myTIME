import os
import time
import json
import hashlib
import hmac

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

if __name__ == "__main__":
    auditor = Auditor()
    print("Auditor Service (v2.4 AEAD) Initialized.")
    
    # Test Entry
    test_content = "Mock scam call transcript fragment: 'I need your password...'"
    entry = auditor.process_log_entry("CALL_FRAGMENT", test_content, "Brian_Sovereign")
    auditor.write_to_ledger(entry)
