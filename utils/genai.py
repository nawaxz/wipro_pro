import base64
import hashlib
import random
from datetime import datetime, timezone

DEFAULT_CAESAR_KEY = 13
DEFAULT_XOR_KEY = [0x5A, 0x3C, 0x7F, 0x1A, 0x42]
CLASSIFICATION_LEVELS = ["CONFIDENTIAL", "SECRET", "TOP SECRET", "RESTRICTED"]
PROTOCOL_HEADERS = ["SECURE TRANSMISSION INITIATED", "ENCRYPTED CHANNEL ACTIVE", "CLASSIFIED COMMUNICATION", "SECURE PACKET RELAY"]

def _get_timestamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _generate_message_id(text):
    return hashlib.md5(text.encode()).hexdigest()[:8].upper()

def _generate_key_fingerprint(caesar_key, xor_key):
    raw = str(caesar_key) + ''.join(str(k) for k in xor_key)
    return hashlib.sha256(raw.encode()).hexdigest()[:12].upper()

def caesar_encrypt(text, shift=None):
    if shift is None: shift = DEFAULT_CAESAR_KEY
    result = []
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            result.append(chr((ord(char) - base + shift) % 26 + base))
        else:
            result.append(char)
    return ''.join(result)

def caesar_decrypt(text, shift=None):
    if shift is None: shift = DEFAULT_CAESAR_KEY
    return caesar_encrypt(text, -shift)

def xor_encrypt(text, key=None):
    if key is None: key = DEFAULT_XOR_KEY
    text_bytes = text.encode('utf-8')
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(text_bytes)])

def xor_decrypt(data, key=None):
    if key is None: key = DEFAULT_XOR_KEY
    decrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])
    return decrypted.decode('utf-8')

def base64_encode(data):
    return base64.b64encode(data).decode('utf-8')

def base64_decode(text):
    return base64.b64decode(text.encode('utf-8'))

def encrypt_message(text, caesar_key=None, xor_key=None):
    if caesar_key is None: caesar_key = DEFAULT_CAESAR_KEY
    if xor_key is None: xor_key = DEFAULT_XOR_KEY
    after_caesar = caesar_encrypt(text, caesar_key)
    after_xor = xor_encrypt(after_caesar, xor_key)
    encrypted_b64 = base64_encode(after_xor)
    fingerprint = _generate_key_fingerprint(caesar_key, xor_key)
    return {
        "encrypted": encrypted_b64,
        "original_len": len(text),
        "caesar_key": caesar_key,
        "fingerprint": fingerprint,
        "layers": "Caesar-13 -> XOR-5byte -> Base64"
    }

def decrypt_message(encrypted_b64, caesar_key=None, xor_key=None):
    if caesar_key is None: caesar_key = DEFAULT_CAESAR_KEY
    if xor_key is None: xor_key = DEFAULT_XOR_KEY
    after_b64 = base64_decode(encrypted_b64)
    after_xor = xor_decrypt(after_b64, xor_key)
    return caesar_decrypt(after_xor, caesar_key)

def generate_secure_message(user_input, mode="standard"):
    if not user_input or not user_input.strip():
        raise ValueError("Cannot generate secure message from empty input.")
    user_input = user_input.strip()
    enc = encrypt_message(user_input)
    classification = random.choice(CLASSIFICATION_LEVELS)
    header = random.choice(PROTOCOL_HEADERS)
    msg_id = _generate_message_id(user_input)
    timestamp = _get_timestamp()
    if mode == "military":
        return _military_format(enc, msg_id, timestamp, classification)
    elif mode == "medical":
        return _medical_format(enc, msg_id, timestamp)
    elif mode == "financial":
        return _financial_format(enc, msg_id, timestamp)
    else:
        return _standard_format(enc, classification, msg_id, timestamp, header)

def _standard_format(enc, classification, msg_id, timestamp, header):
    return (
        "=== " + classification + " | MSG-ID: " + msg_id + " | " + timestamp + " ===\n" +
        header + "\n" +
        "ENCRYPTION: " + enc["layers"] + "\n" +
        "KEY-FINGERPRINT: " + enc["fingerprint"] + "\n" +
        "ENCRYPTED-PAYLOAD:\n" +
        enc["encrypted"] + "\n" +
        "ORIGINAL-LENGTH: " + str(enc["original_len"]) + " chars\n" +
        "--- END SECURE TRANSMISSION ---"
    )

def _military_format(enc, msg_id, timestamp, classification):
    return (
        "FROM: COMMAND CENTER\n" +
        "TO: FIELD OPERATIVE\n" +
        "CLASSIFICATION: " + classification + "\n" +
        "MSG-REF: ALFA-" + msg_id + "\n" +
        "DTG: " + timestamp + "\n" +
        "ENCRYPTION: " + enc["layers"] + "\n" +
        "KEY-FINGERPRINT: " + enc["fingerprint"] + "\n" +
        "ENCRYPTED-MESSAGE:\n" +
        enc["encrypted"] + "\n" +
        "AUTHENTICATION: VERIFIED\n" +
        "END OF MESSAGE"
    )

def _medical_format(enc, msg_id, timestamp):
    return (
        "HIPAA-PROTECTED MEDICAL RECORD\n" +
        "Record-ID: MED-" + msg_id + "\n" +
        "Timestamp: " + timestamp + "\n" +
        "ENCRYPTION: " + enc["layers"] + "\n" +
        "KEY-FINGERPRINT: " + enc["fingerprint"] + "\n" +
        "ENCRYPTED-DATA:\n" +
        enc["encrypted"] + "\n" +
        "Authorized Personnel Only"
    )

def _financial_format(enc, msg_id, timestamp):
    return (
        "SECURE FINANCIAL COMMUNICATION\n" +
        "Transaction-Ref: FIN-" + msg_id + "\n" +
        "Issued: " + timestamp + "\n" +
        "ENCRYPTION: " + enc["layers"] + "\n" +
        "KEY-FINGERPRINT: " + enc["fingerprint"] + "\n" +
        "ENCRYPTED-PAYLOAD:\n" +
        enc["encrypted"] + "\n" +
        "Authorized recipients only."
    )

def generate_with_llm(user_input, api_key=None):
    return generate_secure_message(user_input, mode="standard")
