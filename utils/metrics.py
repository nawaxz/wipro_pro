"""
utils/metrics.py — Data Science Image Quality Metrics
Author: AI Steganography System
"""

import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os


def calculate_mse(original_path: str, stego_path: str) -> float:
    orig  = np.array(Image.open(original_path).convert("RGB"), dtype=np.float64)
    stego = np.array(Image.open(stego_path).convert("RGB"), dtype=np.float64)

    if orig.shape != stego.shape:
        stego_img = Image.open(stego_path).convert("RGB").resize(
            (orig.shape[1], orig.shape[0]), Image.LANCZOS
        )
        stego = np.array(stego_img, dtype=np.float64)

    mse = np.mean((orig - stego) ** 2)
    return round(float(mse), 6)


def calculate_psnr(original_path: str, stego_path: str) -> float:
    mse = calculate_mse(original_path, stego_path)
    if mse == 0:
        return float('inf')
    MAX_PIXEL = 255.0
    psnr = 10 * np.log10((MAX_PIXEL ** 2) / mse)
    return round(float(psnr), 4)


def get_full_metrics(original_path: str, stego_path: str) -> dict:
    mse  = calculate_mse(original_path, stego_path)
    psnr = calculate_psnr(original_path, stego_path)

    if psnr == float('inf') or psnr > 50:
        quality = "Excellent - Imperceptible"
    elif psnr >= 40:
        quality = "Very Good - Visually Identical"
    elif psnr >= 30:
        quality = "Good - Minor Distortion"
    else:
        quality = "Poor - Noticeable Distortion"

    return {
        "mse": mse,
        "psnr": psnr,
        "quality_rating": quality
    }


def plot_image_comparison(original_path: str, stego_path: str, save_path: str) -> str:
    orig  = np.array(Image.open(original_path).convert("RGB"))
    stego = np.array(Image.open(stego_path).convert("RGB"))

    if orig.shape != stego.shape:
        stego = np.array(
            Image.open(stego_path).convert("RGB").resize(
                (orig.shape[1], orig.shape[0]), Image.LANCZOS
            )
        )

    diff = np.abs(orig.astype(np.int32) - stego.astype(np.int32))
    diff_amplified = np.clip(diff * 50, 0, 255).astype(np.uint8)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("Image Quality Analysis: Original vs Stego", fontsize=14, fontweight='bold')

    axes[0].imshow(orig)
    axes[0].set_title("Original (Cover) Image", fontsize=11)
    axes[0].axis('off')

    axes[1].imshow(stego)
    axes[1].set_title("Stego Image (Hidden Message)", fontsize=11)
    axes[1].axis('off')

    axes[2].imshow(diff_amplified)
    axes[2].set_title("Difference Map (x50 amplified)", fontsize=11)
    axes[2].axis('off')

    metrics = get_full_metrics(original_path, stego_path)
    fig.text(
        0.5, 0.01,
        f"MSE: {metrics['mse']}  |  PSNR: {metrics['psnr']} dB  |  Quality: {metrics['quality_rating']}",
        ha='center', fontsize=10, color='darkblue'
    )

    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=100, bbox_inches='tight')
    plt.close()
    return save_path
