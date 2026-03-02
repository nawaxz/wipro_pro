"""
config.py — Global Configuration & Hyperparameters
====================================================
Central place for all project-wide settings.
Modify values here to tune the system without touching core logic.
"""

import os

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR     = os.path.join(BASE_DIR, "dataset")
COVER_DIR       = os.path.join(DATASET_DIR, "cover")
STEGO_DIR       = os.path.join(DATASET_DIR, "stego")
TRAIN_DIR       = os.path.join(DATASET_DIR, "train")
VAL_DIR         = os.path.join(DATASET_DIR, "val")
TEST_DIR        = os.path.join(DATASET_DIR, "test")
MODEL_PATH      = os.path.join(BASE_DIR, "models", "stego_cnn.h5")
UPLOAD_FOLDER   = os.path.join(BASE_DIR, "static", "uploads")
RESULT_FOLDER   = os.path.join(BASE_DIR, "static", "results")
GRAPH_PATH      = os.path.join(BASE_DIR, "static", "results", "training_graph.png")

# ─── Image Settings ───────────────────────────────────────────────────────────
IMG_SIZE        = (128, 128)          # Resize all images to this (W x H)
IMG_CHANNELS    = 3                   # RGB

# ─── CNN Hyperparameters ──────────────────────────────────────────────────────
BATCH_SIZE      = 32
EPOCHS          = 20
LEARNING_RATE   = 0.001
VALIDATION_SPLIT = 0.2

# ─── Dataset Generation ───────────────────────────────────────────────────────
NUM_COVER_IMAGES = 200                # Synthetic cover images to generate
SAMPLE_MESSAGES  = [
    "CLASSIFIED: Operation Phoenix — Do not distribute.",
    "Encrypted payload: Alpha-7 secure handshake initiated.",
    "CONFIDENTIAL: Transfer code 9X44-ZETA approved.",
    "SECRET: Meeting at coordinates 28.7N, 77.1E at 0300hrs.",
    "PRIVATE: Patient ID 8821 — Diagnosis code A41.9.",
]

# ─── Steganography ────────────────────────────────────────────────────────────
DELIMITER       = "####"              # End-of-message marker

# ─── Flask ────────────────────────────────────────────────────────────────────
SECRET_KEY      = "stego_secure_2024"
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp"}
