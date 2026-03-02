/**
 * main.js — Fixed tab switching and frontend interactivity
 */

// ── Tab Switching ─────────────────────────────────────────────────────────────
function switchTab(name) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    // Remove active from all buttons
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

    // Show selected tab content
    const content = document.getElementById('tab-' + name);
    if (content) content.classList.add('active');

    // Set active button by index
    const buttons = document.querySelectorAll('.tab-btn');
    if (name === 'embed'   && buttons[0]) buttons[0].classList.add('active');
    if (name === 'extract' && buttons[1]) buttons[1].classList.add('active');
    if (name === 'about'   && buttons[2]) buttons[2].classList.add('active');
}

// ── Image Preview (Embed) ─────────────────────────────────────────────────────
function previewImage(input) {
    const preview = document.getElementById('imagePreview');
    const prompt  = document.getElementById('uploadPrompt');
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
            if (prompt) prompt.style.display = 'none';
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// ── Image Preview (Extract) ───────────────────────────────────────────────────
function previewExtractImage(input) {
    const preview = document.getElementById('extractPreview');
    const prompt  = document.getElementById('extractPrompt');
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
            if (prompt) prompt.style.display = 'none';
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// ── Character Counter ─────────────────────────────────────────────────────────
function updateCharCount(textarea) {
    const counter = document.getElementById('charCount');
    if (counter) counter.textContent = textarea.value.length;
}

// ── GenAI Preview ─────────────────────────────────────────────────────────────
async function previewAIMessage() {
    const textArea = document.getElementById('userMessage');
    const preview  = document.getElementById('aiPreview');

    if (!textArea || !textArea.value.trim()) {
        alert('Please enter a message first.');
        return;
    }

    const text = textArea.value.trim();
    const modeInput = document.querySelector('input[name="genai_mode"]:checked');
    const mode = modeInput ? modeInput.value : 'standard';

    preview.classList.remove('hidden');
    preview.textContent = 'Generating secure AI message...';

    try {
        const response = await fetch('/generate_message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text, mode: mode })
        });
        const data = await response.json();
        if (data.error) {
            preview.textContent = 'Error: ' + data.error;
        } else {
            preview.textContent = 'AI Message Preview (' + mode + ' mode):\n\n' + data.ai_message;
        }
    } catch (err) {
        preview.textContent = 'Connection error: ' + err.message;
    }
}

// ── On Page Load ──────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {

    // Toggle GenAI mode selector
    const genaiCheckbox = document.getElementById('useGenai');
    const modeSelect    = document.getElementById('modeSelect');
    if (genaiCheckbox && modeSelect) {
        genaiCheckbox.addEventListener('change', function() {
            modeSelect.style.opacity = this.checked ? '1' : '0.4';
            modeSelect.style.pointerEvents = this.checked ? 'auto' : 'none';
        });
    }

    // Drag and drop upload
    const uploadZone = document.getElementById('uploadZone');
    if (uploadZone) {
        uploadZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            uploadZone.style.borderColor = '#06b6d4';
        });
        uploadZone.addEventListener('dragleave', function() {
            uploadZone.style.borderColor = '';
        });
        uploadZone.addEventListener('drop', function(e) {
            e.preventDefault();
            const fileInput = document.getElementById('imageInput');
            if (e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files;
                previewImage(fileInput);
            }
            uploadZone.style.borderColor = '';
        });
    }
});
