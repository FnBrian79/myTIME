from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

def encrypt_transcript(persona_id, transcript_text, master_key_hex):
    """
    Encrypts transcript text using AEAD with persona_id as associated data.
    
    Args:
        persona_id: The persona identifier (e.g., "hazel", "brandon")
        transcript_text: The text to encrypt
        master_key_hex: The master key in hex format
    
    Returns:
        bytes: nonce + ciphertext (nonce is first 12 bytes)
    """
    aesgcm = AESGCM(bytes.fromhex(master_key_hex))
    nonce = os.urandom(12)
    # persona_id is our 'Associated Data' (AD)
    # This ensures "Hank's" data can't be decrypted as "Brandon's"
    aad = persona_id.encode()
    ciphertext = aesgcm.encrypt(nonce, transcript_text.encode(), aad)
    return nonce + ciphertext

def decrypt_transcript(persona_id, encrypted_data, master_key_hex):
    """
    Decrypts transcript data using AEAD.
    
    Args:
        persona_id: The persona identifier used during encryption
        encrypted_data: The encrypted data (nonce + ciphertext)
        master_key_hex: The master key in hex format
    
    Returns:
        str: The decrypted transcript text
    """
    aesgcm = AESGCM(bytes.fromhex(master_key_hex))
    nonce = encrypted_data[:12]
    ciphertext = encrypted_data[12:]
    aad = persona_id.encode()
    plaintext = aesgcm.decrypt(nonce, ciphertext, aad)
    return plaintext.decode()

def load_master_key(key_path=None):
    """
    Loads the master key from the config file.
    
    Args:
        key_path: Path to the master key file. If None, tries default locations.
    
    Returns:
        str: The master key in hex format
    """
    if key_path is None:
        # Try common locations
        possible_paths = [
            "/app/config/master.key",  # Docker container
            "config/master.key",        # Local relative
            "../config/master.key",     # From services directory
        ]
        for path in possible_paths:
            if os.path.exists(path):
                key_path = path
                break
        else:
            raise Exception("Master key not found. Run bootstrap script first or provide key_path.")
    
    try:
        with open(key_path, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        raise Exception(f"Master key not found at {key_path}. Run bootstrap script first.")

# The Architect will call this before saving to the learning_repo
