"""
models/cnn_model.py — CNN Architecture for Stego Detection (AIML Module)
=========================================================================
Builds a Convolutional Neural Network to classify images as:
    - Class 0: Normal (Cover) Image
    - Class 1: Stego Image (contains hidden data)

ARCHITECTURE OVERVIEW:
    Input (128×128×3)
         ↓
    [Conv2D 32 filters → BatchNorm → ReLU → MaxPool]   Block 1
         ↓
    [Conv2D 64 filters → BatchNorm → ReLU → MaxPool]   Block 2
         ↓
    [Conv2D 128 filters → BatchNorm → ReLU → MaxPool]  Block 3
         ↓
    [Conv2D 256 filters → BatchNorm → ReLU → MaxPool]  Block 4
         ↓
    [GlobalAveragePooling]
         ↓
    [Dense 256 → Dropout 0.5 → Dense 128 → Dropout 0.3]
         ↓
    [Dense 1 → Sigmoid]  →  Output: P(stego)

WHY THIS ARCHITECTURE:
    - LSB changes are subtle (1-bit per channel); deeper features are needed
    - BatchNorm stabilizes training with small pixel differences
    - GlobalAveragePooling reduces overfitting vs Flatten
    - Sigmoid output → binary probability (0=cover, 1=stego)

Author: AI Steganography System
"""

import tensorflow as tf
from tensorflow.keras import layers, models, regularizers
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import IMG_SIZE, IMG_CHANNELS, LEARNING_RATE


def build_stego_cnn(input_shape: tuple = None) -> tf.keras.Model:
    """
    Build and compile the CNN model for stego image detection.

    Args:
        input_shape: (height, width, channels). Defaults to config values.

    Returns:
        Compiled Keras model ready for training.
    """
    if input_shape is None:
        input_shape = (IMG_SIZE[1], IMG_SIZE[0], IMG_CHANNELS)  # (H, W, C)

    model = models.Sequential([
        # ── Input Layer ──────────────────────────────────────────────────────
        layers.Input(shape=input_shape),

        # ── Block 1: Edge Detection Features ────────────────────────────────
        layers.Conv2D(32, (3, 3), padding='same', kernel_regularizer=regularizers.l2(1e-4)),
        layers.BatchNormalization(),
        layers.Activation('relu'),
        layers.Conv2D(32, (3, 3), padding='same', kernel_regularizer=regularizers.l2(1e-4)),
        layers.BatchNormalization(),
        layers.Activation('relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.2),

        # ── Block 2: Mid-Level Features ──────────────────────────────────────
        layers.Conv2D(64, (3, 3), padding='same', kernel_regularizer=regularizers.l2(1e-4)),
        layers.BatchNormalization(),
        layers.Activation('relu'),
        layers.Conv2D(64, (3, 3), padding='same', kernel_regularizer=regularizers.l2(1e-4)),
        layers.BatchNormalization(),
        layers.Activation('relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.2),

        # ── Block 3: High-Level Features ────────────────────────────────────
        layers.Conv2D(128, (3, 3), padding='same', kernel_regularizer=regularizers.l2(1e-4)),
        layers.BatchNormalization(),
        layers.Activation('relu'),
        layers.Conv2D(128, (3, 3), padding='same', kernel_regularizer=regularizers.l2(1e-4)),
        layers.BatchNormalization(),
        layers.Activation('relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.3),

        # ── Block 4: Abstract Features ───────────────────────────────────────
        layers.Conv2D(256, (3, 3), padding='same', kernel_regularizer=regularizers.l2(1e-4)),
        layers.BatchNormalization(),
        layers.Activation('relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.3),

        # ── Classification Head ──────────────────────────────────────────────
        layers.GlobalAveragePooling2D(),
        layers.Dense(256, activation='relu', kernel_regularizer=regularizers.l2(1e-4)),
        layers.BatchNormalization(),
        layers.Dropout(0.5),
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.3),
        layers.Dense(1, activation='sigmoid'),  # Binary output
    ], name="StegoCNN")

    # ── Compile ───────────────────────────────────────────────────────────────
    optimizer = tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE)
    model.compile(
        optimizer=optimizer,
        loss='binary_crossentropy',
        metrics=['accuracy', tf.keras.metrics.AUC(name='auc')]
    )

    return model


def get_model_summary(model: tf.keras.Model) -> str:
    """Return model architecture as a formatted string."""
    lines = []
    model.summary(print_fn=lambda x: lines.append(x))
    return "\n".join(lines)


if __name__ == "__main__":
    model = build_stego_cnn()
    print("=" * 60)
    print("CNN Architecture: StegoCNN Binary Classifier")
    print("=" * 60)
    model.summary()
    print(f"\nTotal Parameters: {model.count_params():,}")
    print(f"Input Shape: {model.input_shape}")
    print(f"Output Shape: {model.output_shape}")
