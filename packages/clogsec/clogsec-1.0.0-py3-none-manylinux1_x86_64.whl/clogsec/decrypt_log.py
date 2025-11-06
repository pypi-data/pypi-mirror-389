import os
import hashlib
import base64
from .crypto import decrypt_message

def decrypt_log(log_file, encryption_key):
    """Decrypt and return RC4-encrypted log file contents, printing only decrypted logs."""
    if not log_file or not encryption_key or not os.path.exists(log_file):
        return []

    try:
        with open(log_file, "r", encoding='utf-8') as f:
            lines = f.readlines()
    except Exception:
        return []

    decrypted_logs = []
    for i, line in enumerate(lines, 1):
        try:
            line = line.strip()
            if not line or '>' not in line:
                continue
            asctime, levelname, correlation_id, message = line.split('>')
            if not message or ':' not in message:
                continue
            checksum, encrypted_msg = message.split(':')
            if not checksum or not encrypted_msg or len(checksum) != 64:
                continue
            decrypted = decrypt_message(encrypted_msg, encryption_key).decode('utf-8')
            computed_checksum = hashlib.sha256(decrypted.encode('utf-8')).hexdigest()
            if computed_checksum != checksum:
                continue
            decrypted_logs.append({
                "asctime" : asctime,
                "levelname" : levelname,
                "correlation_id" : correlation_id,
                "checksum" : checksum,
                "decrypt_message" : decrypted,
                })
        except Exception as e:
            print(e)

    return decrypted_logs