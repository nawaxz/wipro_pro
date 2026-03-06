"""
utils/genai.py -- Generative AI Message Module with Hash Security
=================================================================
PIPELINE:
    User types message
        -> SHA256 Hash generated (fingerprint)
        -> Message encoded with Base64
        -> Secure packet built with hash + encoded message
        -> Embedded into image

DECRYPTION:
    Extract packet from image
        -> Split hash and encoded message
        -> Base64 decode to get original message
        -> Verify SHA256 hash matches
        -> Return original message

Author: AI Steganography System
"""

import base64
import hashlib
import random
from datetime import datetime, timezone


# -- Constants ------------------------------------------------------------------

CLASSIFICATION_LEVELS = ["CONFIDENTIAL", "SECRET", "TOP SECRET", "RESTRICTED"]
PROTOCOL_HEADERS = [
    "SECURE TRANSMISSION INITIATED",
    "ENCRYPTED CHANNEL ACTIVE",
    "CLASSIFIED COMMUNICATION",
    "SECURE PACKET RELAY",
]
PACKET_START = "<<STEGO-PACKET>>"
PACKET_END   = "<<END-PACKET>>"


# -- Hash Functions -------------------------------------------------------------

def compute_sha256(text):
    """
    Generate SHA256 hash of the message.
    SHA256 always produces 64 character hex string.

    Example:
        'hello' -> '2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824'
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def compute_md5_id(text):
    """Short 8-char MD5 for message ID."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:8].upper()


# -- Encode / Decode -----------------------------------------------------------

def encode_message(text):
    """
    Encode message to Base64 for safe embedding.
    Base64 uses only ASCII characters -- safe for LSB steganography.

    Example:
        'hello' -> 'aGVsbG8='
    """
    return base64.b64encode(text.encode('utf-8')).decode('utf-8')


def decode_message(encoded):
    """
    Decode Base64 back to original message.

    Example:
        'aGVsbG8=' -> 'hello'
    """
    return base64.b64decode(encoded.encode('utf-8')).decode('utf-8')


# -- Verify Hash ---------------------------------------------------------------

def verify_hash(original_text, stored_hash):
    """
    Verify message integrity by recomputing SHA256.
    If hash matches -- message is authentic and unchanged.

    Returns: True if verified, False if tampered
    """
    computed = compute_sha256(original_text)
    return computed == stored_hash


# -- Main Packet Builder -------------------------------------------------------

def generate_secure_message(user_input, mode="standard"):
    """
    Build a secure packet containing:
        - SHA256 hash of original message (for verification)
        - Base64 encoded message (for recovery)
        - Metadata (timestamp, classification, message ID)

    The packet is what gets embedded into the image via LSB.

    IMPORTANT: Only ASCII characters used -- no unicode arrows or symbols.
    This ensures LSB embedding works correctly.
    """
    if not user_input or not user_input.strip():
        raise ValueError("Cannot generate secure message from empty input.")

    user_input = user_input.strip()

    # Step 1: Generate SHA256 hash
    sha256_hash = compute_sha256(user_input)

    # Step 2: Base64 encode the message
    encoded_msg = encode_message(user_input)

    # Step 3: Generate metadata
    msg_id         = compute_md5_id(user_input)
    timestamp      = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    classification = random.choice(CLASSIFICATION_LEVELS)
    header         = random.choice(PROTOCOL_HEADERS)

    # Step 4: Build packet based on mode
    if mode == "military":
        packet = _military_packet(encoded_msg, sha256_hash, msg_id, timestamp, classification)
    elif mode == "medical":
        packet = _medical_packet(encoded_msg, sha256_hash, msg_id, timestamp)
    elif mode == "financial":
        packet = _financial_packet(encoded_msg, sha256_hash, msg_id, timestamp)
    else:
        packet = _standard_packet(encoded_msg, sha256_hash, msg_id, timestamp, classification, header)

    return packet


# -- Packet Templates ----------------------------------------------------------

def _standard_packet(encoded, sha256, msg_id, timestamp, classification, header):
    return (
        PACKET_START + "\n" +
        "=== " + classification + " | MSG-ID: " + msg_id + " | " + timestamp + " ===\n" +
        header + "\n" +
        "SECURITY: SHA256-HASH + BASE64-ENCODING\n" +
        "SHA256: " + sha256 + "\n" +
        "ENCODED-MESSAGE: " + encoded + "\n" +
        "--- END SECURE TRANSMISSION ---\n" +
        PACKET_END
    )


def _military_packet(encoded, sha256, msg_id, timestamp, classification):
    return (
        PACKET_START + "\n" +
        "FROM: COMMAND CENTER\n" +
        "TO: FIELD OPERATIVE\n" +
        "CLASSIFICATION: " + classification + "\n" +
        "MSG-REF: ALFA-" + msg_id + "\n" +
        "DTG: " + timestamp + "\n" +
        "SECURITY: SHA256-HASH + BASE64-ENCODING\n" +
        "SHA256: " + sha256 + "\n" +
        "ENCODED-MESSAGE: " + encoded + "\n" +
        "AUTHENTICATION: VERIFIED\n" +
        PACKET_END
    )


def _medical_packet(encoded, sha256, msg_id, timestamp):
    return (
        PACKET_START + "\n" +
        "HIPAA-PROTECTED MEDICAL RECORD\n" +
        "Record-ID: MED-" + msg_id + "\n" +
        "Timestamp: " + timestamp + "\n" +
        "SECURITY: SHA256-HASH + BASE64-ENCODING\n" +
        "SHA256: " + sha256 + "\n" +
        "ENCODED-MESSAGE: " + encoded + "\n" +
        "Authorized Personnel Only\n" +
        PACKET_END
    )


def _financial_packet(encoded, sha256, msg_id, timestamp):
    return (
        PACKET_START + "\n" +
        "SECURE FINANCIAL COMMUNICATION\n" +
        "Transaction-Ref: FIN-" + msg_id + "\n" +
        "Issued: " + timestamp + "\n" +
        "SECURITY: SHA256-HASH + BASE64-ENCODING\n" +
        "SHA256: " + sha256 + "\n" +
        "ENCODED-MESSAGE: " + encoded + "\n" +
        "Authorized recipients only.\n" +
        PACKET_END
    )


# -- Decryption ----------------------------------------------------------------

def decrypt_packet(packet_text):
    """
    Extract and verify original message from secure packet.

    Steps:
        1. Find ENCODED-MESSAGE line -> Base64 decode -> original message
        2. Find SHA256 line -> verify hash matches
        3. Return original message + verification status

    Returns dict:
        {
            "original_message": "hello",
            "sha256_stored":    "2cf24dba...",
            "sha256_computed":  "2cf24dba...",
            "verified":         True,
            "status":           "VERIFIED - Message is authentic"
        }
    """
    result = {
        "original_message": None,
        "sha256_stored":    None,
        "sha256_computed":  None,
        "verified":         False,
        "status":           "Could not parse packet"
    }

    try:
        lines = packet_text.strip().split('\n')

        # Find encoded message and hash
        for line in lines:
            line = line.strip()
            if line.startswith("ENCODED-MESSAGE:"):
                encoded = line.replace("ENCODED-MESSAGE:", "").strip()
                result["original_message"] = decode_message(encoded)
            if line.startswith("SHA256:"):
                result["sha256_stored"] = line.replace("SHA256:", "").strip()

        # Verify hash
        if result["original_message"] and result["sha256_stored"]:
            result["sha256_computed"] = compute_sha256(result["original_message"])
            result["verified"] = verify_hash(result["original_message"], result["sha256_stored"])
            if result["verified"]:
                result["status"] = "VERIFIED - Message is authentic and untampered"
            else:
                result["status"] = "WARNING - Hash mismatch! Message may be tampered"

    except Exception as e:
        result["status"] = "Error: " + str(e)

    return result


# -- Stub LLM ------------------------------------------------------------------

def generate_with_llm(user_input, api_key=None):
    """Stub for real LLM. Falls back to rule-based."""
    return generate_secure_message(user_input, mode="standard")
