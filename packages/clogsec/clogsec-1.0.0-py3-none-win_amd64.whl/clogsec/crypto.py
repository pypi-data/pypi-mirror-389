import base64
from Crypto.Cipher import ARC4

def encrypt_message(message, encryption_key):
    """Encrypt a message using RC4 with the provided key."""
    print("message", message)
    print("encryption_key", encryption_key)
    try:
        # Ensure message is a string
        if not isinstance(message, str):
            raise ValueError("Message must be a string")

        # Decode base64 key to bytes
        key_bytes = base64.b64decode(encryption_key)

        # Initialize RC4 cipher
        cipher = ARC4.new(key_bytes)

        # Convert message to bytes and encrypt
        message_bytes = message.encode('utf-8')
        encrypted = cipher.encrypt(message_bytes)

        # Encode to base64 for storage
        return base64.b64encode(encrypted).decode('utf-8')
    except Exception as e:
        raise ValueError(f"Encryption failed: {e}")

def decrypt_message(cipher, encryption_key):
    print("cipher", cipher)
    print("encryption_key", encryption_key)
    """Decrypt a message using RC4 with the provided key."""
    try:
        # Decode base64 key and ciphertext
        key_bytes = base64.b64decode(encryption_key)
        cipher_bytes = base64.b64decode(cipher)

        # Initialize RC4 cipher
        cipher = ARC4.new(key_bytes)

        # Decrypt
        decrypted_bytes = cipher.decrypt(cipher_bytes)
        return decrypted_bytes
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}")