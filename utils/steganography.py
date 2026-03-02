"""
utils/steganography.py — LSB Image Steganography (Computer Vision Module)
Supports both text messages and file embedding via Base64 encoding.
Author: AI Steganography System
"""

import numpy as np
from PIL import Image
import base64
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DELIMITER, IMG_SIZE


# ── Text ↔ Binary ─────────────────────────────────────────────────────────────

def text_to_binary(text: str) -> str:
    return ''.join(format(ord(char), '08b') for char in text)


def binary_to_text(binary: str) -> str:
    chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
    return ''.join(chr(int(b, 2)) for b in chars if len(b) == 8)


# ── File → Base64 string ──────────────────────────────────────────────────────

def file_to_base64_string(file_path: str) -> str:
    """Convert any file to a Base64 encoded string for embedding."""
    filename = os.path.basename(file_path)
    with open(file_path, 'rb') as f:
        file_bytes = f.read()
    b64_data = base64.b64encode(file_bytes).decode('utf-8')
    # Format: FILE:filename:base64data
    return f"FILE:{filename}:{b64_data}"


def base64_string_to_file(encoded_str: str, output_dir: str) -> str:
    """Convert Base64 string back to original file and save it."""
    if not encoded_str.startswith("FILE:"):
        raise ValueError("Not a file payload.")
    parts = encoded_str.split(":", 2)
    if len(parts) != 3:
        raise ValueError("Invalid file payload format.")
    _, filename, b64_data = parts
    file_bytes = base64.b64decode(b64_data)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    with open(output_path, 'wb') as f:
        f.write(file_bytes)
    return output_path


# ── LSB Encoding ──────────────────────────────────────────────────────────────

def encode_image(cover_image_path: str, secret_message: str, output_path: str) -> str:
    """Embed a secret message (text or file payload) into a cover image."""
    img = Image.open(cover_image_path).convert("RGB")
    img_array = np.array(img, dtype=np.uint8)

    full_message = secret_message + DELIMITER
    binary_message = text_to_binary(full_message)
    message_length = len(binary_message)

    max_capacity = img_array.size
    if message_length > max_capacity:
        raise ValueError(
            f"Message too large! Need {message_length} bits, image holds {max_capacity} bits."
        )

    flat = img_array.flatten().copy()
    for i, bit in enumerate(binary_message):
        flat[i] = (flat[i] & 0b11111110) | int(bit)

    stego_array = flat.reshape(img_array.shape)
    stego_img = Image.fromarray(stego_array.astype(np.uint8), "RGB")
    stego_img.save(output_path, format="PNG")
    return output_path


# ── LSB Decoding ──────────────────────────────────────────────────────────────

def decode_image(stego_image_path: str) -> str:
    """Extract hidden message or file payload from stego image."""
    img = Image.open(stego_image_path).convert("RGB")
    img_array = np.array(img, dtype=np.uint8)
    flat = img_array.flatten()

    binary_bits = ''.join(str(pixel & 1) for pixel in flat)
    decoded_text = ""
    for i in range(0, len(binary_bits), 8):
        byte = binary_bits[i:i+8]
        if len(byte) < 8:
            break
        char = chr(int(byte, 2))
        decoded_text += char
        if decoded_text.endswith(DELIMITER):
            return decoded_text[:-len(DELIMITER)]

    raise ValueError("No hidden message found.")


# ── Capacity Calculator ───────────────────────────────────────────────────────

def get_image_capacity(image_path: str) -> dict:
    img = Image.open(image_path).convert("RGB")
    img_array = np.array(img)
    max_bits = img_array.size
    max_chars = max_bits // 8 - len(DELIMITER)
    max_bytes = max_chars  # approx file size in bytes
    w, h = img.size
    return {
        "image_size": f"{w}x{h}",
        "max_bits": max_bits,
        "max_chars": max_chars,
        "max_file_kb": round(max_bytes / 1024, 1)
    }
