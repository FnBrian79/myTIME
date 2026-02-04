#!/usr/bin/env python3
"""
Test script to verify the AEAD crypto utilities work correctly.
"""
import sys
import os

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Add services/auditor to path
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'services', 'auditor'))

from crypto_utils import encrypt_transcript, decrypt_transcript, load_master_key

def test_crypto_utils():
    print("🔐 Testing AEAD Crypto Utilities...")
    
    # Load the generated master key
    master_key_path = os.path.join(PROJECT_ROOT, 'config', 'master.key')
    try:
        master_key_hex = load_master_key(master_key_path)
        print(f"✅ Master key loaded: {master_key_hex[:16]}... ({len(master_key_hex)} chars)")
    except Exception as e:
        print(f"❌ Failed to load master key: {e}")
        return False
    
    # Test encryption/decryption
    test_cases = [
        ("hazel", "Hello, this is a test transcript from the IRS scammer."),
        ("brandon", "I need your credit card number to verify your identity."),
        ("hank", "This is a very long transcript that should still encrypt and decrypt properly without any issues even though it contains many words and sentences."),
    ]
    
    for persona_id, original_text in test_cases:
        print(f"\n📝 Testing persona: {persona_id}")
        print(f"   Original: {original_text[:50]}...")
        
        # Encrypt
        try:
            encrypted = encrypt_transcript(persona_id, original_text, master_key_hex)
            print(f"   ✅ Encrypted: {len(encrypted)} bytes")
        except Exception as e:
            print(f"   ❌ Encryption failed: {e}")
            return False
        
        # Decrypt
        try:
            decrypted = decrypt_transcript(persona_id, encrypted, master_key_hex)
            print(f"   Decrypted: {decrypted[:50]}...")
        except Exception as e:
            print(f"   ❌ Decryption failed: {e}")
            return False
        
        # Verify
        if decrypted == original_text:
            print(f"   ✅ Verification passed!")
        else:
            print(f"   ❌ Verification failed! Texts don't match.")
            return False
    
    # Test persona separation (trying to decrypt with wrong persona)
    print(f"\n🔒 Testing persona separation...")
    encrypted_hazel = encrypt_transcript("hazel", "Secret message for Hazel", master_key_hex)
    try:
        # This should fail
        decrypt_transcript("brandon", encrypted_hazel, master_key_hex)
        print(f"   ❌ Security breach! Wrong persona could decrypt the data.")
        return False
    except Exception as e:
        print(f"   ✅ Persona separation working! Cannot decrypt with wrong persona.")
    
    print(f"\n✅ All crypto tests passed!")
    return True

if __name__ == "__main__":
    success = test_crypto_utils()
    sys.exit(0 if success else 1)
