"""
app.py — Flask Web Application with File Embedding + Secret Sharing
Author: AI Steganography System
"""

import os
import sys
import uuid
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, send_file
from werkzeug.utils import secure_filename

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    SECRET_KEY, UPLOAD_FOLDER, RESULT_FOLDER,
    ALLOWED_EXTENSIONS, MAX_CONTENT_LENGTH
)
from utils.steganography import (
    encode_image, decode_image, get_image_capacity,
    file_to_base64_string, base64_string_to_file
)
from utils.metrics import get_full_metrics, plot_image_comparison
from utils.genai import generate_secure_message

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

ALLOWED_EMBED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'xlsx', 'csv', 'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def allowed_embed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EMBED_EXTENSIONS


def generate_unique_filename(original_filename, prefix=""):
    unique_id = uuid.uuid4().hex[:8]
    return f"{prefix}{unique_id}.png"


# Load CNN model ONCE at startup
_predict_fn = None
try:
    from models.predict import predict_image
    _predict_fn = predict_image
    print("CNN model loaded successfully!")
except Exception as e:
    print("CNN model not loaded:", e)

def load_cnn_model():
    return _predict_fn


# ── Main Routes ───────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/embed', methods=['POST'])
def embed():
    if 'image' not in request.files:
        flash('No image uploaded.', 'error')
        return redirect(url_for('index'))

    file = request.files['image']
    if file.filename == '' or not allowed_file(file.filename):
        flash('Please upload a valid image (PNG, JPG, JPEG, BMP).', 'error')
        return redirect(url_for('index'))

    embed_type = request.form.get('embed_type', 'text')
    secret_message = request.form.get('message', '').strip()
    genai_mode = request.form.get('genai_mode', 'standard')
    use_genai = request.form.get('use_genai', 'on') == 'on'

    try:
        orig_filename = generate_unique_filename(file.filename, "orig_")
        orig_path = os.path.join(UPLOAD_FOLDER, orig_filename)
        file.save(orig_path)
        capacity = get_image_capacity(orig_path)

        embed_file_name = None
        if embed_type == 'file':
            if 'embed_file' not in request.files or request.files['embed_file'].filename == '':
                flash('Please upload a file to embed.', 'error')
                return redirect(url_for('index'))
            embed_file = request.files['embed_file']
            if not allowed_embed_file(embed_file.filename):
                flash('File type not supported.', 'error')
                return redirect(url_for('index'))
            embed_filename = secure_filename(embed_file.filename)
            embed_file_name = embed_filename
            temp_file_path = os.path.join(UPLOAD_FOLDER, embed_filename)
            embed_file.save(temp_file_path)
            secret_message = file_to_base64_string(temp_file_path)
            use_genai = False
            os.remove(temp_file_path)

        ai_message = secret_message
        if use_genai and embed_type == 'text':
            if not secret_message:
                flash('Please enter a secret message.', 'error')
                return redirect(url_for('index'))
            ai_message = generate_secure_message(secret_message, mode=genai_mode)

        if not ai_message:
            flash('Please enter a message or select a file.', 'error')
            return redirect(url_for('index'))

        stego_filename = generate_unique_filename(file.filename, "stego_")
        stego_path = os.path.join(RESULT_FOLDER, stego_filename)
        encode_image(orig_path, ai_message, stego_path)

        metrics = get_full_metrics(orig_path, stego_path)

        comparison_filename = f"comparison_{uuid.uuid4().hex[:8]}.png"
        comparison_path = os.path.join(RESULT_FOLDER, comparison_filename)
        plot_image_comparison(orig_path, stego_path, comparison_path)

        predict_fn = load_cnn_model()
        if predict_fn:
            detection = predict_fn(stego_path)
        else:
            detection = {
                "label": "Model Not Trained",
                "verdict": "Train CNN first: python models/train.py",
                "confidence_pct": "N/A",
                "risk_level": "N/A"
            }

        context = {
            "mode": "embed",
            "embed_type": embed_type,
            "embed_file_name": embed_file_name,
            "original_image": f"uploads/{orig_filename}",
            "stego_image": f"results/{stego_filename}",
            "comparison_image": f"results/{comparison_filename}",
            "original_message": request.form.get('message', ''),
            "ai_message": ai_message if embed_type == 'text' else f"[File embedded: {embed_file_name}]",
            "use_genai": use_genai,
            "genai_mode": genai_mode,
            "metrics": metrics,
            "detection": detection,
            "capacity": capacity,
            "message_length": len(ai_message),
        }
        return render_template('result.html', **context)

    except ValueError as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Unexpected error: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/extract', methods=['POST'])
def extract():
    if 'image' not in request.files:
        flash('No image uploaded.', 'error')
        return redirect(url_for('index'))

    file = request.files['image']
    if file.filename == '' or not allowed_file(file.filename):
        flash('Please upload a valid image.', 'error')
        return redirect(url_for('index'))

    try:
        filename = generate_unique_filename(file.filename, "decode_")
        img_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(img_path)

        decoded_message = decode_image(img_path)
        is_file_payload = decoded_message.startswith("FILE:")
        extracted_file_path = None
        extracted_file_name = None
        decrypted = None

        if is_file_payload:
            extracted_file_path = base64_string_to_file(decoded_message, RESULT_FOLDER)
            extracted_file_name = os.path.basename(extracted_file_path)
        else:
            # Auto-decrypt GenAI packet if present
            try:
                from utils.genai import decrypt_packet, PACKET_START
                if PACKET_START in decoded_message:
                    decrypted = decrypt_packet(decoded_message)
            except Exception:
                decrypted = None

        predict_fn = load_cnn_model()
        if predict_fn:
            detection = predict_fn(img_path)
        else:
            detection = {
                "label": "Model Not Trained",
                "verdict": "Train CNN first.",
                "confidence_pct": "N/A",
                "risk_level": "N/A"
            }

        context = {
            "mode": "extract",
            "stego_image": f"uploads/{filename}",
            "decoded_message": decoded_message if not is_file_payload else f"[File extracted: {extracted_file_name}]",
            "is_file_payload": is_file_payload,
            "extracted_file_name": extracted_file_name,
            "detection": detection,
            "decrypted": decrypted,
        }
        return render_template('result.html', **context)

    except ValueError as e:
        flash(f'No hidden message found: {str(e)}', 'warning')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Extraction error: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/download_extracted/<filename>')
def download_extracted(filename):
    file_path = os.path.join(RESULT_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    flash('File not found.', 'error')
    return redirect(url_for('index'))


@app.route('/generate_message', methods=['POST'])
def generate_message_api():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "No text provided"}), 400
    try:
        mode = data.get('mode', 'standard')
        ai_message = generate_secure_message(data['text'], mode=mode)
        return jsonify({"original": data['text'], "ai_message": ai_message, "mode": mode})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Secret Sharing Routes ─────────────────────────────────────────────────────

@app.route('/secret_sharing')
def secret_sharing_page():
    return render_template('secret_sharing.html')


@app.route('/create_shares', methods=['POST'])
def create_shares_route():
    from utils.secret_sharing import create_shares

    files = [request.files.get(f'image{i}') for i in [1, 2, 3]]
    share_type = request.form.get('share_type', 'text')

    # Validate 3 images
    for i, f in enumerate(files):
        if not f or f.filename == '' or not allowed_file(f.filename):
            flash(f'Please upload a valid image {i+1}.', 'error')
            return redirect(url_for('secret_sharing_page'))

    try:
        # Get message — text or file
        share_filename = None
        if share_type == 'file':
            share_file = request.files.get('share_file')
            if not share_file or share_file.filename == '':
                flash('Please select a file to embed.', 'error')
                return redirect(url_for('secret_sharing_page'))
            share_filename = secure_filename(share_file.filename)
            temp_path = os.path.join(UPLOAD_FOLDER, share_filename)
            share_file.save(temp_path)
            message = file_to_base64_string(temp_path)
            os.remove(temp_path)
        else:
            message = request.form.get('message', '').strip()
            if not message:
                flash('Please enter a secret message.', 'error')
                return redirect(url_for('secret_sharing_page'))

        # Save 3 cover images
        image_paths = []
        for i, f in enumerate(files):
            fname = f"share_cover_{i+1}_{uuid.uuid4().hex[:6]}.png"
            fpath = os.path.join(UPLOAD_FOLDER, fname)
            f.save(fpath)
            image_paths.append(fpath)

        output_paths = create_shares(message, image_paths, RESULT_FOLDER)
        share_filenames = [os.path.basename(p) for p in output_paths]

        return render_template('secret_sharing.html',
            mode='result',
            share_filenames=share_filenames,
            share_type=share_type,
            share_filename=share_filename,
            message_length=len(message),
        )

    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('secret_sharing_page'))


@app.route('/reconstruct_shares', methods=['POST'])
def reconstruct_shares_route():
    from utils.secret_sharing import reconstruct_from_share_images

    files = [request.files.get(f'share{i}') for i in [1, 2, 3]]

    for i, f in enumerate(files):
        if not f or f.filename == '' or not allowed_file(f.filename):
            flash(f'Please upload share image {i+1}.', 'error')
            return redirect(url_for('secret_sharing_page'))

    try:
        share_paths = []
        for i, f in enumerate(files):
            fname = f"recon_share_{i+1}_{uuid.uuid4().hex[:6]}.png"
            fpath = os.path.join(UPLOAD_FOLDER, fname)
            f.save(fpath)
            share_paths.append(fpath)

        message = reconstruct_from_share_images(share_paths)

        is_file = message.startswith("FILE:")
        extracted_file_name = None
        if is_file:
            extracted_path = base64_string_to_file(message, RESULT_FOLDER)
            extracted_file_name = os.path.basename(extracted_path)

        return render_template('secret_sharing.html',
            mode='reconstructed',
            reconstructed_message=message if not is_file else '',
            is_file=is_file,
            extracted_file_name=extracted_file_name,
        )

    except Exception as e:
        flash(f'Reconstruction failed: {str(e)}', 'error')
        return redirect(url_for('secret_sharing_page'))


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("="*60)
    print("StegoAI — Starting Flask Web Application")
    print("Open: http://localhost:5000")
    print("="*60)
    app.run(debug=True, host='0.0.0.0', port=5000)
