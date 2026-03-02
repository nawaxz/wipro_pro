# AI-Powered Secure Image Steganography
### Final Year Engineering Project
**Domains Covered:** Computer Vision | Data Science | AI/ML | Generative AI

---

## 📁 Project Structure

```
stego_project/
├── app.py                    # Flask web application (main entry point)
├── config.py                 # Global configuration & hyperparameters
├── requirements.txt          # Python dependencies
│
├── utils/
│   ├── steganography.py      # CV: LSB encode/decode logic
│   ├── metrics.py            # DS: MSE, PSNR calculations
│   ├── genai.py              # GenAI: secret message generator
│   └── dataset_builder.py   # Creates cover/stego dataset
│
├── models/
│   ├── cnn_model.py          # AIML: CNN architecture definition
│   ├── train.py              # CNN training pipeline
│   └── predict.py            # Inference / prediction
│
├── dataset/
│   ├── cover/                # Original images
│   ├── stego/                # Stego images (auto-generated)
│   ├── train/cover | stego
│   ├── val/cover  | stego
│   └── test/cover  | stego
│
├── static/
│   ├── css/style.css         # Web UI styling
│   ├── js/main.js            # Frontend interactivity
│   ├── uploads/              # User-uploaded images
│   └── results/              # Processed output images
│
└── templates/
    ├── index.html            # Main web page
    └── result.html           # Result display page
```

---

## 🚀 Setup & Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate dataset (cover + stego images)
python utils/dataset_builder.py

# 3. Train the CNN model
python models/train.py

# 4. Launch the Flask web app
python app.py
```
Then open: **http://localhost:5000**

---

## 🔄 System Workflow

```
User Input (Image + Text)
        ↓
[GenAI Module] → Reformats/secures the message
        ↓
[LSB Steganography] → Embeds message into image pixels
        ↓
[Metrics Module] → Calculates PSNR / MSE
        ↓
[CNN Model] → Predicts: Stego (1) or Normal (0)
        ↓
Web UI displays: Stego image + PSNR + Prediction
```

---

## 📊 Key Metrics

| Metric | Meaning | Good Range |
|--------|---------|------------|
| MSE    | Pixel-level distortion | < 1.0 |
| PSNR   | Image quality (dB)     | > 40 dB |
| CNN Accuracy | Detection accuracy | > 90% |

---

## 🎓 Domain Mapping

| Domain          | Component |
|--------         |-----------|
| Computer Vision | LSB steganography, OpenCV/Pillow processing |
| Data Science    | MSE/PSNR metrics, training graphs |
| AI/ML           | CNN binary classifier (cover vs stego) |
| Generative AI   | Prompt-based message transformation |
