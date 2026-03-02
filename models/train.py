"""
models/train.py — CNN Training Pipeline (Data Science + AIML Module)
=====================================================================
Run:  python models/train.py
Author: AI Steganography System
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Compatible TensorFlow imports (works for TF 2.13 on Windows)
import tensorflow as tf
try:
    from tensorflow.keras.preprocessing.image import ImageDataGenerator
    from tensorflow.keras.callbacks import (
        ModelCheckpoint, EarlyStopping, ReduceLROnPlateau, CSVLogger
    )
except ImportError:
    from keras.preprocessing.image import ImageDataGenerator
    from keras.callbacks import (
        ModelCheckpoint, EarlyStopping, ReduceLROnPlateau, CSVLogger
    )

from sklearn.metrics import classification_report, confusion_matrix

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    TRAIN_DIR, VAL_DIR, TEST_DIR, MODEL_PATH, GRAPH_PATH,
    IMG_SIZE, BATCH_SIZE, EPOCHS
)
from models.cnn_model import build_stego_cnn


def create_data_generators():
    train_datagen = ImageDataGenerator(
        rescale=1.0 / 255.0,
        horizontal_flip=True,
        rotation_range=15,
        brightness_range=[0.8, 1.2],
        zoom_range=0.1,
        fill_mode='nearest'
    )
    val_test_datagen = ImageDataGenerator(rescale=1.0 / 255.0)
    target_size = (IMG_SIZE[1], IMG_SIZE[0])

    train_gen = train_datagen.flow_from_directory(
        TRAIN_DIR, target_size=target_size, batch_size=BATCH_SIZE,
        class_mode='binary', classes=['cover', 'stego'], shuffle=True, seed=42
    )
    val_gen = val_test_datagen.flow_from_directory(
        VAL_DIR, target_size=target_size, batch_size=BATCH_SIZE,
        class_mode='binary', classes=['cover', 'stego'], shuffle=False
    )
    test_gen = val_test_datagen.flow_from_directory(
        TEST_DIR, target_size=target_size, batch_size=BATCH_SIZE,
        class_mode='binary', classes=['cover', 'stego'], shuffle=False
    )
    return train_gen, val_gen, test_gen


def create_callbacks(model_path):
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    log_path = model_path.replace('.h5', '_training_log.csv')
    return [
        ModelCheckpoint(filepath=model_path, monitor='val_accuracy', save_best_only=True, verbose=1),
        EarlyStopping(monitor='val_loss', patience=8, restore_best_weights=True, verbose=1),
        ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=4, min_lr=1e-7, verbose=1),
        CSVLogger(log_path, append=False)
    ]


def plot_training_history(history, save_path):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("CNN Training Analysis - StegoCNN Binary Classifier", fontsize=13, fontweight='bold')
    epochs_range = range(1, len(history.history['accuracy']) + 1)

    axes[0].plot(epochs_range, history.history['accuracy'], 'b-o', label='Training Accuracy', linewidth=2, markersize=4)
    axes[0].plot(epochs_range, history.history['val_accuracy'], 'r-s', label='Validation Accuracy', linewidth=2, markersize=4)
    axes[0].set_title('Model Accuracy'); axes[0].set_xlabel('Epoch'); axes[0].set_ylabel('Accuracy')
    axes[0].legend(); axes[0].grid(True, alpha=0.3); axes[0].set_ylim([0, 1.05])

    best_val_acc = max(history.history['val_accuracy'])
    best_epoch = history.history['val_accuracy'].index(best_val_acc) + 1
    axes[0].annotate(f'Best: {best_val_acc:.4f} (Epoch {best_epoch})',
        xy=(best_epoch, best_val_acc), xytext=(best_epoch+1, best_val_acc-0.05),
        arrowprops=dict(arrowstyle='->', color='green'), color='green', fontsize=9)

    axes[1].plot(epochs_range, history.history['loss'], 'b-o', label='Training Loss', linewidth=2, markersize=4)
    axes[1].plot(epochs_range, history.history['val_loss'], 'r-s', label='Validation Loss', linewidth=2, markersize=4)
    axes[1].set_title('Model Loss (Binary Cross-Entropy)'); axes[1].set_xlabel('Epoch'); axes[1].set_ylabel('Loss')
    axes[1].legend(); axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f"Training graph saved: {save_path}")


def plot_confusion_matrix(y_true, y_pred, save_path):
    try:
        import seaborn as sns
        cm = confusion_matrix(y_true, y_pred)
        fig, ax = plt.subplots(figsize=(6, 5))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=['Cover', 'Stego'], yticklabels=['Cover', 'Stego'], ax=ax)
        ax.set_title('Confusion Matrix', fontweight='bold')
        ax.set_xlabel('Predicted'); ax.set_ylabel('True')
        plt.tight_layout()
        cm_path = save_path.replace('training_graph', 'confusion_matrix')
        plt.savefig(cm_path, dpi=120, bbox_inches='tight')
        plt.close()
        print(f"Confusion matrix saved: {cm_path}")
    except ImportError:
        print("Install seaborn for confusion matrix: pip install seaborn")


def train():
    print("=" * 60)
    print("StegoCNN Training Pipeline")
    print("=" * 60)

    for d in [TRAIN_DIR, VAL_DIR, TEST_DIR]:
        if not os.path.exists(d):
            print(f"Dataset not found: {d}")
            print("Run 'python utils/dataset_builder.py' first!")
            sys.exit(1)

    print("\nLoading dataset...")
    train_gen, val_gen, test_gen = create_data_generators()
    print(f"  Train: {train_gen.samples} | Val: {val_gen.samples} | Test: {test_gen.samples}")
    print(f"  Classes: {train_gen.class_indices}")

    print("\nBuilding CNN model...")
    model = build_stego_cnn()
    model.summary()

    callbacks = create_callbacks(MODEL_PATH)

    print(f"\nTraining for up to {EPOCHS} epochs...")
    history = model.fit(
        train_gen, epochs=EPOCHS, validation_data=val_gen,
        callbacks=callbacks, verbose=1
    )

    print("\nGenerating training graphs...")
    plot_training_history(history, GRAPH_PATH)

    print("\nEvaluating on test set...")
    results = model.evaluate(test_gen, verbose=0)
    print(f"\n{'='*40}")
    print(f"TEST RESULTS:")
    print(f"  Accuracy : {results[1]:.4f} ({results[1]*100:.2f}%)")
    print(f"  Loss     : {results[0]:.4f}")
    print(f"{'='*40}")

    test_gen.reset()
    y_pred = (model.predict(test_gen, verbose=0) > 0.5).astype(int).flatten()
    y_true = test_gen.classes
    print("\nClassification Report:")
    print(classification_report(y_true, y_pred, target_names=['Cover', 'Stego']))
    plot_confusion_matrix(y_true, y_pred, GRAPH_PATH)

    print(f"\nModel saved: {MODEL_PATH}")
    print("Training complete! Run 'python app.py' to launch the web app.")
    return history


if __name__ == "__main__":
    train()
