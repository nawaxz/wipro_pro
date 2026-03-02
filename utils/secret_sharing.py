"""
utils/secret_sharing.py — Multi-Image Secret Sharing
======================================================
Splits a secret message across 3 different images.
ALL 3 images are needed to reconstruct the original message.

HOW IT WORKS:
    1. Secret message is converted to binary bits
    2. Bits are split into 3 shares using XOR operations:
       - Share1 = Random bits
       - Share2 = Random bits  
       - Share3 = Message XOR Share1 XOR Share2
    3. Each share is embedded into a separate image using LSB
    4. To reconstruct: Share1 XOR Share2 XOR Share3 = Original Message

WHY IT IS SECURE:
    - Any 1 or 2 images alone reveal NOTHING about the message
    - All 3 images together perfectly reconstruct the message
    - This is based on XOR Secret Sharing scheme

Author: AI Steganography System
"""

import numpy as np
from PIL import Image
import os
import sys
import random
import string

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DELIMITER


# ── Text ↔ Binary ─────────────────────────────────────────────────────────────

def text_to_bits(text: str) -> list:
    """Convert text to list of bits (0s and 1s)."""
    bits = []
    for char in text:
        byte = format(ord(char), '08b')
        bits.extend([int(b) for b in byte])
    return bits


def bits_to_text(bits: list) -> str:
    """Convert list of bits back to text."""
    chars = []
    for i in range(0, len(bits), 8):
        byte = bits[i:i+8]
        if len(byte) == 8:
            chars.append(chr(int(''.join(str(b) for b in byte), 2)))
    return ''.join(chars)


# ── XOR Secret Sharing ────────────────────────────────────────────────────────

def split_message_into_shares(message: str) -> tuple:
    """
    Split a message into 3 shares using XOR.
    
    Returns:
        (share1_bits, share2_bits, share3_bits)
        
    Property: share1 XOR share2 XOR share3 = original message bits
    """
    # Add delimiter
    full_message = message + DELIMITER
    message_bits = text_to_bits(full_message)
    n = len(message_bits)

    # Generate 2 random shares
    share1 = [random.randint(0, 1) for _ in range(n)]
    share2 = [random.randint(0, 1) for _ in range(n)]

    # share3 = message XOR share1 XOR share2
    share3 = [message_bits[i] ^ share1[i] ^ share2[i] for i in range(n)]

    return share1, share2, share3


def reconstruct_message_from_shares(share1: list, share2: list, share3: list) -> str:
    """
    Reconstruct original message from 3 shares using XOR.
    
    share1 XOR share2 XOR share3 = original message
    """
    if len(share1) != len(share2) or len(share2) != len(share3):
        raise ValueError("All 3 shares must have the same length!")

    # XOR all 3 shares
    reconstructed_bits = [share1[i] ^ share2[i] ^ share3[i] for i in range(len(share1))]
    text = bits_to_text(reconstructed_bits)

    # Find and remove delimiter
    if DELIMITER in text:
        return text[:text.index(DELIMITER)]
    raise ValueError("Could not reconstruct message. Make sure all 3 images are correct.")


# ── Embed Share into Image ────────────────────────────────────────────────────

def embed_share_in_image(image_path: str, share_bits: list, output_path: str, share_num: int):
    """
    Embed a share (list of bits) into an image using LSB.
    
    Also embeds a header: SHARE:N:LENGTH: so we know share number and size.
    """
    img = Image.open(image_path).convert("RGB")
    img_array = np.array(img, dtype=np.uint8)

    # Create header: SHARE:1:1234: (share number and bit length)
    header = f"SHARE:{share_num}:{len(share_bits)}:"
    header_bits = text_to_bits(header)

    # Combine header + share bits + end marker
    end_marker_bits = text_to_bits("###END###")
    all_bits = header_bits + share_bits + end_marker_bits

    max_capacity = img_array.size
    if len(all_bits) > max_capacity:
        raise ValueError(
            f"Image too small for share {share_num}! "
            f"Need {len(all_bits)} bits, image holds {max_capacity} bits."
        )

    flat = img_array.flatten().copy()
    for i, bit in enumerate(all_bits):
        flat[i] = (flat[i] & 0b11111110) | int(bit)

    stego_array = flat.reshape(img_array.shape)
    stego_img = Image.fromarray(stego_array.astype(np.uint8), "RGB")
    stego_img.save(output_path, format="PNG")


def extract_share_from_image(image_path: str) -> tuple:
    """
    Extract share bits from a stego image.
    
    Returns:
        (share_num, share_bits)
    """
    img = Image.open(image_path).convert("RGB")
    img_array = np.array(img, dtype=np.uint8)
    flat = img_array.flatten()

    # Extract all LSBs
    all_bits = [int(pixel & 1) for pixel in flat]

    # Convert bits to text to find header
    raw_text = bits_to_text(all_bits)

    # Parse header: SHARE:N:LENGTH:
    if not raw_text.startswith("SHARE:"):
        raise ValueError("This image does not contain a valid share. Wrong image?")

    try:
        parts = raw_text.split(":")
        share_num = int(parts[1])
        bit_length = int(parts[2])
    except Exception:
        raise ValueError("Could not parse share header. Image may be corrupted.")

    # Calculate where share data starts
    header_str = f"SHARE:{share_num}:{bit_length}:"
    header_bits_count = len(text_to_bits(header_str))

    # Extract exactly bit_length bits after header
    share_bits = all_bits[header_bits_count:header_bits_count + bit_length]

    if len(share_bits) < bit_length:
        raise ValueError("Could not extract complete share. Image may be too small.")

    return share_num, share_bits


# ── Main Pipeline ─────────────────────────────────────────────────────────────

def create_shares(message: str, image_paths: list, output_dir: str) -> list:
    """
    Full pipeline: split message and embed into 3 images.
    
    Args:
        message     : Secret message to split
        image_paths : List of 3 cover image paths
        output_dir  : Where to save the 3 stego images
        
    Returns:
        List of 3 output stego image paths
    """
    if len(image_paths) != 3:
        raise ValueError("Exactly 3 images are required for secret sharing.")

    os.makedirs(output_dir, exist_ok=True)

    # Split message into 3 shares
    share1, share2, share3 = split_message_into_shares(message)
    shares = [share1, share2, share3]

    output_paths = []
    for i, (img_path, share) in enumerate(zip(image_paths, shares)):
        share_num = i + 1
        filename = f"share_{share_num}_{os.path.basename(img_path).split('.')[0]}.png"
        output_path = os.path.join(output_dir, filename)
        embed_share_in_image(img_path, share, output_path, share_num)
        output_paths.append(output_path)
        print(f"Share {share_num} embedded in: {output_path}")

    return output_paths


def reconstruct_from_share_images(share_image_paths: list) -> str:
    """
    Full pipeline: extract shares from 3 images and reconstruct message.
    
    Args:
        share_image_paths: List of 3 stego image paths (any order)
        
    Returns:
        Reconstructed secret message
    """
    if len(share_image_paths) != 3:
        raise ValueError("Exactly 3 share images are required.")

    # Extract shares (handle any order)
    shares = {}
    for img_path in share_image_paths:
        share_num, share_bits = extract_share_from_image(img_path)
        shares[share_num] = share_bits
        print(f"Extracted share {share_num} from: {img_path}")

    # Verify all 3 shares present
    if sorted(shares.keys()) != [1, 2, 3]:
        missing = [i for i in [1, 2, 3] if i not in shares]
        raise ValueError(f"Missing share(s): {missing}. All 3 images are required!")

    # Verify all shares same length
    lengths = [len(shares[i]) for i in [1, 2, 3]]
    if len(set(lengths)) != 1:
        raise ValueError("Share lengths don't match. Images may be from different sessions.")

    # Reconstruct
    message = reconstruct_message_from_shares(shares[1], shares[2], shares[3])
    return message
