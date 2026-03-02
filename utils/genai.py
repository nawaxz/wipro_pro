"""
utils/genai.py — Generative AI Secret Message Module
======================================================
Transforms plain user text into secure, AI-formatted confidential messages
before embedding into images via steganography.

GENERATIVE AI APPROACH:
    This module implements a rule-based + template-driven message generator
    that mimics what a large language model (LLM) would produce.
    
    For production deployment with an actual LLM:
        - Swap the `generate_with_llm()` stub with an API call to 
          OpenAI GPT-4, Google Gemini, or Anthropic Claude.
        - The pipeline remains identical regardless of backend.

SECURITY TRANSFORMATIONS APPLIED:
    1. Timestamp injection       → adds UTC time for non-repudiation
    2. Priority classification   → labels message sensitivity level
    3. Cipher hint encoding      → Base64-encodes keywords
    4. Protocol wrapping         → formats as secure transmission packet

Author: AI Steganography System
"""

import base64
import hashlib
import random
from datetime import datetime, timezone


# ──────────────────────────────────────────────────────────────────────────────
# TEMPLATES: Secure Message Formats
# ──────────────────────────────────────────────────────────────────────────────

CLASSIFICATION_LEVELS = ["CONFIDENTIAL", "SECRET", "TOP SECRET", "RESTRICTED"]

PROTOCOL_HEADERS = [
    "SECURE TRANSMISSION INITIATED",
    "ENCRYPTED CHANNEL ACTIVE",
    "CLASSIFIED COMMUNICATION",
    "SECURE PACKET RELAY",
]

def _get_timestamp() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _generate_message_id(text: str) -> str:
    """Generate a short unique ID from message content using MD5 hash."""
    return hashlib.md5(text.encode()).hexdigest()[:8].upper()


def _encode_keywords(text: str) -> str:
    """
    Base64-encode the first significant word as a 'cipher hint'.
    In real GenAI systems, this would be LLM-generated cipher text.
    """
    words = [w for w in text.split() if len(w) > 4]
    if words:
        keyword = words[0]
        encoded = base64.b64encode(keyword.encode()).decode()
        return f"[CIPHER-HINT: {encoded}]"
    return "[CIPHER-HINT: NONE]"


# ──────────────────────────────────────────────────────────────────────────────
# CORE: Generate AI-Formatted Secure Message
# ──────────────────────────────────────────────────────────────────────────────

def generate_secure_message(user_input: str, mode: str = "standard") -> str:
    """
    Transform plain user text into a structured confidential message.

    Args:
        user_input : The original message from the user
        mode       : 'standard', 'military', 'medical', 'financial'

    Returns:
        Formatted secure message string ready for steganographic embedding

    Example:
        Input:  "Meet at the warehouse at midnight"
        Output: "=== TOP SECRET | MSG-ID: A3F9C12B | 2024-01-15T22:30:00Z ===
                 SECURE TRANSMISSION INITIATED
                 [CIPHER-HINT: TWVldA==]
                 PAYLOAD: Meet at the warehouse at midnight
                 --- END TRANSMISSION ---"
    """
    if not user_input or not user_input.strip():
        raise ValueError("Cannot generate secure message from empty input.")

    user_input = user_input.strip()

    # Select classification and header
    classification = random.choice(CLASSIFICATION_LEVELS)
    header = random.choice(PROTOCOL_HEADERS)
    msg_id = _generate_message_id(user_input)
    timestamp = _get_timestamp()
    cipher_hint = _encode_keywords(user_input)

    # Build message based on mode
    if mode == "military":
        formatted = _military_format(user_input, classification, msg_id, timestamp, cipher_hint, header)
    elif mode == "medical":
        formatted = _medical_format(user_input, msg_id, timestamp)
    elif mode == "financial":
        formatted = _financial_format(user_input, msg_id, timestamp)
    else:
        formatted = _standard_format(user_input, classification, msg_id, timestamp, cipher_hint, header)

    return formatted


def _standard_format(text, classification, msg_id, timestamp, cipher_hint, header) -> str:
    return (
        f"=== {classification} | MSG-ID: {msg_id} | {timestamp} ===\n"
        f"{header}\n"
        f"{cipher_hint}\n"
        f"PAYLOAD: {text}\n"
        f"--- END SECURE TRANSMISSION ---"
    )


def _military_format(text, classification, msg_id, timestamp, cipher_hint, header) -> str:
    return (
        f"FROM: COMMAND CENTER\n"
        f"TO: FIELD OPERATIVE\n"
        f"CLASSIFICATION: {classification}\n"
        f"MSG-REF: ALFA-{msg_id}\n"
        f"DTG: {timestamp}\n"
        f"{cipher_hint}\n"
        f"MESSAGE: {text}\n"
        f"AUTHENTICATION: VERIFIED\n"
        f"END OF MESSAGE"
    )


def _medical_format(text, msg_id, timestamp) -> str:
    return (
        f"HIPAA-PROTECTED MEDICAL RECORD\n"
        f"Record-ID: MED-{msg_id}\n"
        f"Timestamp: {timestamp}\n"
        f"CONFIDENTIAL PATIENT DATA:\n"
        f"{text}\n"
        f"Authorized Personnel Only — Unauthorized disclosure is prohibited."
    )


def _financial_format(text, msg_id, timestamp) -> str:
    return (
        f"SECURE FINANCIAL COMMUNICATION\n"
        f"Transaction-Ref: FIN-{msg_id}\n"
        f"Issued: {timestamp}\n"
        f"CONFIDENTIAL ADVISORY:\n"
        f"{text}\n"
        f"This communication is for authorized recipients only."
    )


# ──────────────────────────────────────────────────────────────────────────────
# STUB: Actual LLM Integration (Plug in your API key here)
# ──────────────────────────────────────────────────────────────────────────────

def generate_with_llm(user_input: str, api_key: str = None) -> str:
    """
    Stub for real LLM-based message generation.

    To enable: install 'anthropic' or 'openai' package and add your API key.

    Example with Anthropic Claude:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=256,
            messages=[{
                "role": "user",
                "content": f"Reformat this as a secure classified message: {user_input}"
            }]
        )
        return message.content[0].text

    For now, falls back to rule-based generation.
    """
    # Fallback to rule-based if no API key
    return generate_secure_message(user_input, mode="standard")
