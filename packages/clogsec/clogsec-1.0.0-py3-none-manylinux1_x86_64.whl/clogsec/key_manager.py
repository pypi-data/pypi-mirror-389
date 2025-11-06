import os
import logging
import base64

def generate_key(encryption_key, key_file, logger):
    """Load or generate an RC4 encryption key as a base64-encoded string."""
    # Create a console-only logger for key messages
    console_logger = logging.getLogger("key_manager")
    console_logger.setLevel(logging.INFO)
    console_logger.handlers = []  # Clear any existing handlers
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(message)s'))  # Simplified format
    console_logger.addHandler(console_handler)

    if encryption_key:
        try:
            key_bytes = base64.b64decode(encryption_key)
            if len(key_bytes) not in range(5, 257):  # RC4 key length: 5-256 bytes
                raise ValueError("RC4 key must decode to 5-256 bytes")
            console_logger.info("Using provided base64-encoded encryption key")
            return encryption_key
        except Exception as e:
            console_logger.error(f"Provided base64-encoded key is invalid: {e}; generating a new one")

    if os.path.exists(key_file):
        try:
            with open(key_file, "r", encoding='utf-8') as f:
                key = f.read().strip()
            key_bytes = base64.b64decode(key)
            if len(key_bytes) not in range(5, 257):
                raise ValueError("Invalid base64-encoded key length for RC4")
            console_logger.info(f"Loaded valid base64-encoded encryption key from {key_file}")
            return key
        except Exception as e:
            console_logger.error(f"Invalid base64-encoded key in {key_file}: {e}; generating a new one")

    # Generate new 16-byte key
    new_key_bytes = os.urandom(16)
    new_key = base64.b64encode(new_key_bytes).decode('utf-8')
    try:
        with open(key_file, "w", encoding='utf-8') as f:
            f.write(new_key)
        console_logger.info(f"Generated and saved new base64-encoded encryption key to {key_file}")
    except Exception as e:
        console_logger.error(f"Failed to save base64-encoded encryption key to {key_file}: {e}")
    return new_key