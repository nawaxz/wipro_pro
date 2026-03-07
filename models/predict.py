"""
models/predict.py — Stego Detection Inference Module
======================================================
"""

import os
import sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MODEL_PATH, IMG_SIZE


# Lazy-load the model (singleton pattern — load once, reuse)
_model = None
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True


def _load_model():
    """Load the CNN model from disk. Cached after first call."""
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Trained model not found at: {MODEL_PATH}\n"
                "Please run 'python models/train.py' first."
            )
        import tensorflow as tf
        _model = tf.keras.models.load_model(MODEL_PATH)
        print(f"✅ Model loaded from: {MODEL_PATH}")
    return _model


def preprocess_image(image_path: str) -> np.ndarray:
    """
    Load and preprocess an image for CNN inference.

    Steps:
        1. Open image and convert to RGB
        2. Resize to model input size (128×128)
        3. Normalize pixel values to [0, 1]
        4. Add batch dimension → shape (1, 128, 128, 3)

    Returns:
        numpy array ready for model.predict()
    """
    img = Image.open(image_path).convert("RGB")
    img = img.resize((IMG_SIZE[0], IMG_SIZE[1]), Image.LANCZOS)
    img_array = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(img_array, axis=0)  # Add batch dim


def predict_image(image_path: str) -> dict:
   
    model = _load_model()
    img_array = preprocess_image(image_path)

    # Get raw probability from sigmoid output
    raw_prob = float(model.predict(img_array, verbose=0)[0][0])

    # Binary classification threshold
    threshold = 0.5
    class_id = 1 if raw_prob >= threshold else 0
    label = "Stego" if class_id == 1 else "Cover"
    confidence = raw_prob if class_id == 1 else (1.0 - raw_prob)

    # Risk level assessment
    if confidence > 0.90:
        risk_level = "High" if class_id == 1 else "Very Low"
    elif confidence > 0.70:
        risk_level = "Medium" if class_id == 1 else "Low"
    else:
        risk_level = "Uncertain"

    # Human-readable verdict
    if class_id == 1:
        if confidence > 0.90:
            verdict = "⚠️ HIGH CONFIDENCE: Hidden data detected in this image!"
        else:
            verdict = "⚠️ Possible hidden data detected (moderate confidence)."
    else:
        if confidence > 0.90:
            verdict = "✅ HIGH CONFIDENCE: No hidden data detected. Image appears clean."
        else:
            verdict = "✅ No hidden data detected (moderate confidence)."

    return {
        "label": label,
        "confidence": round(confidence, 4),
        "probability": round(raw_prob, 4),
        "class_id": class_id,
        "verdict": verdict,
        "risk_level": risk_level,
        "confidence_pct": f"{confidence * 100:.1f}%"
    }


def batch_predict(image_paths: list) -> list:
    """
    Predict stego status for a list of images.

    Args:
        image_paths: List of image file paths

    Returns:
        List of prediction dictionaries
    """
    results = []
    for path in image_paths:
        try:
            result = predict_image(path)
            result["image_path"] = path
            results.append(result)
        except Exception as e:
            results.append({
                "image_path": path,
                "error": str(e),
                "label": "Error",
                "confidence": 0
            })
    return results


if __name__ == "__main__":
    # Quick test
    import sys
    if len(sys.argv) > 1:
        img_path = sys.argv[1]
        print(f"🔍 Analyzing: {img_path}")
        result = predict_image(img_path)
        print("\n" + "="*40)
        print("PREDICTION RESULT")
        print("="*40)
        for k, v in result.items():
            print(f"  {k:15s}: {v}")
    else:
        print("Usage: python predict.py <image_path>")
