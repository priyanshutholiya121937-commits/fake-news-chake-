import os
import re
import json
import string
import joblib
import numpy as np
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash

from database.database import init_db, save_scan, get_history, get_scan, delete_scan
from ocr.image_processor import extract_text_from_image, is_allowed_file, clean_ocr_text

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB limit

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
init_db()

# Model and vectorizer caching
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model', 'fake_news_model.pkl')
VECTORIZER_PATH = os.path.join(os.path.dirname(__file__), 'model', 'tfidf_vectorizer.pkl')
METADATA_PATH = os.path.join(os.path.dirname(__file__), 'model', 'model_metadata.json')

_model = None
_vectorizer = None
_metadata = None

def load_ml_assets():
    global _model, _vectorizer, _metadata
    if _model is None and os.path.exists(MODEL_PATH):
        try:
            _model = joblib.load(MODEL_PATH)
        except Exception as e:
            print(f"Error loading model: {e}")
    if _vectorizer is None and os.path.exists(VECTORIZER_PATH):
        try:
            _vectorizer = joblib.load(VECTORIZER_PATH)
        except Exception as e:
            print(f"Error loading vectorizer: {e}")
    if _metadata is None and os.path.exists(METADATA_PATH):
        try:
            with open(METADATA_PATH, 'r') as f:
                _metadata = json.load(f)
        except Exception as e:
            print(f"Error loading metadata: {e}")
    return _model, _vectorizer, _metadata

def preprocess_for_prediction(text: str) -> str:
    """Preprocess text for vectorization."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'<.*?>', '', text)
    text = text.translate(str.maketrans('', '', string.punctuation))
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def predict_fake_news(headline: str, article_text: str):
    """
    Predict whether given headline + article is Real or Fake using ML model.
    Returns: (prediction_label, confidence_percentage, model_name, analysis_details)
    """
    model, vectorizer, meta = load_ml_assets()

    combined = f"{headline.strip()} {article_text.strip()}".strip()
    cleaned = preprocess_for_prediction(combined)

    if not model or not vectorizer:
        # Fallback heuristic analysis if model is compiling
        model_name = "Rule-based Fallback Model"
        sensational_words = {'shocking', 'secret', 'miracle', 'cure', 'banned', 'exposed', 'aliens', 'unbelievable', 'conspiracy', 'whistleblower', 'exploding', 'reptilians', 'nanobots'}
        words = set(cleaned.split())
        match_count = len(words.intersection(sensational_words))
        if match_count >= 2:
            pred_label = "LIKELY FAKE"
            confidence = min(75.0 + match_count * 5.0, 96.5)
        elif len(words) < 5:
            pred_label = "UNCERTAIN"
            confidence = 50.0
        else:
            pred_label = "LIKELY REAL"
            confidence = 82.5
        return pred_label, confidence, model_name, {"cleaned_tokens": len(words), "features_matched": match_count}

    model_name = meta.get("best_model", "Calibrated Fake News Classifier") if meta else "Calibrated ML Classifier"

    # Vectorize
    vec = vectorizer.transform([cleaned])

    # Check for empty / very low content
    tokens = cleaned.split()
    if len(tokens) < 3:
        return "UNCERTAIN", 50.0, model_name, {"word_count": len(tokens)}

    # Predict
    pred_class = model.predict(vec)[0]  # 0: Real, 1: Fake

    # Confidence calculation
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(vec)[0]
        prob_fake = float(probabilities[1])
        prob_real = float(probabilities[0])

        if 0.44 <= prob_fake <= 0.56:
            pred_label = "UNCERTAIN"
            confidence = round(max(prob_fake, prob_real) * 100, 2)
        elif prob_fake > 0.5:
            pred_label = "LIKELY FAKE"
            confidence = round(prob_fake * 100, 2)
        else:
            pred_label = "LIKELY REAL"
            confidence = round(prob_real * 100, 2)
    elif hasattr(model, "decision_function"):
        score = float(model.decision_function(vec)[0])
        prob = 1.0 / (1.0 + np.exp(-score))
        if 0.44 <= prob <= 0.56:
            pred_label = "UNCERTAIN"
            confidence = 50.0
        elif score > 0:
            pred_label = "LIKELY FAKE"
            confidence = round(prob * 100, 2)
        else:
            pred_label = "LIKELY REAL"
            confidence = round((1 - prob) * 100, 2)
    else:
        pred_label = "LIKELY FAKE" if pred_class == 1 else "LIKELY REAL"
        confidence = 85.0

    return pred_label, confidence, model_name, {"word_count": len(tokens)}

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Render home landing page."""
    return render_template('index.html', active_page='home')

@app.route('/text-check')
def text_check():
    """Render news text submission page."""
    return render_template('text_check.html', active_page='text_check')

@app.route('/analyze-text', methods=['POST'])
def analyze_text():
    """Handle text fake news classification POST."""
    headline = request.form.get('headline', '').strip()
    article_text = request.form.get('article_text', '').strip()

    if not headline and not article_text:
        flash("Please provide a news headline or article text to analyze.", "error")
        return redirect(url_for('text_check'))

    full_text = f"{headline}\n\n{article_text}".strip() if headline else article_text
    
    # Run prediction
    prediction, confidence, model_name, details = predict_fake_news(headline, article_text)

    # Save to SQLite database
    scan_id = save_scan(
        input_type='text',
        original_text=full_text,
        extracted_text=None,
        prediction=prediction,
        confidence=confidence,
        model_used=model_name
    )

    return render_template(
        'result.html',
        active_page='text_check',
        scan_id=scan_id,
        input_type='Text Submission',
        original_text=full_text,
        extracted_text=None,
        prediction=prediction,
        confidence=confidence,
        model_used=model_name,
        timestamp=datetime.now().strftime("%B %d, %Y - %I:%M %p")
    )

@app.route('/image-scanner')
def image_scanner():
    """Render camera scanning and image upload page."""
    return render_template('image_scanner.html', active_page='scan_news')

@app.route('/analyze-image', methods=['POST'])
def analyze_image():
    """Handle OCR scanning from file upload or camera base64 data."""
    # Handle camera snapshot (dataURL) or file upload
    camera_data = request.form.get('camera_image_data', '')
    uploaded_file = request.files.get('image_file')

    temp_image_path = None

    try:
        if camera_data and camera_data.startswith('data:image'):
            import base64
            header, encoded = camera_data.split(',', 1)
            file_ext = 'png'
            if 'jpeg' in header or 'jpg' in header:
                file_ext = 'jpg'
            elif 'webp' in header:
                file_ext = 'webp'
            
            filename = f"cam_{int(datetime.now().timestamp())}_{os.urandom(4).hex()}.{file_ext}"
            temp_image_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
            with open(temp_image_path, "wb") as fh:
                fh.write(base64.b64decode(encoded))
            input_type_label = 'camera'
        elif uploaded_file and uploaded_file.filename:
            if not is_allowed_file(uploaded_file.filename):
                flash("Unsupported file format. Please upload JPG, JPEG, PNG, or WEBP.", "error")
                return redirect(url_for('image_scanner'))
            
            ext = uploaded_file.filename.rsplit('.', 1)[1].lower()
            filename = f"upload_{int(datetime.now().timestamp())}_{os.urandom(4).hex()}.{ext}"
            temp_image_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
            uploaded_file.save(temp_image_path)
            input_type_label = 'upload'
        else:
            flash("Please capture a photo using your camera or upload an image file.", "error")
            return redirect(url_for('image_scanner'))

        # Run OCR extraction pipeline
        ocr_result = extract_text_from_image(temp_image_path)

        if not ocr_result.get('success') or not ocr_result.get('extracted_text'):
            flash(ocr_result.get('message', "No readable news text was detected. Please take a clearer photo."), "warning")
            return redirect(url_for('image_scanner'))

        extracted_text = ocr_result['extracted_text']

        # Run ML Fake News Classification on extracted text
        prediction, confidence, model_name, details = predict_fake_news("", extracted_text)

        # Save to SQLite database
        scan_id = save_scan(
            input_type=input_type_label,
            original_text="[Image Scan]",
            extracted_text=extracted_text,
            prediction=prediction,
            confidence=confidence,
            model_used=model_name
        )

        return render_template(
            'result.html',
            active_page='scan_news',
            scan_id=scan_id,
            input_type=f"Photo Scan ({input_type_label.capitalize()})",
            original_text=None,
            extracted_text=extracted_text,
            prediction=prediction,
            confidence=confidence,
            model_used=model_name,
            timestamp=datetime.now().strftime("%B %d, %Y - %I:%M %p")
        )

    except Exception as e:
        flash(f"Error processing image: {str(e)}", "error")
        return redirect(url_for('image_scanner'))
    finally:
        # Clean up temporary uploaded image file for disk hygiene
        if temp_image_path and os.path.exists(temp_image_path):
            try:
                os.remove(temp_image_path)
            except Exception:
                pass

@app.route('/history')
def history():
    """Render scan history with search and category filters."""
    search_q = request.args.get('q', '').strip()
    filter_pred = request.args.get('pred', 'ALL').strip()
    filter_type = request.args.get('type', 'ALL').strip()

    records = get_history(search=search_q if search_q else None, filter_pred=filter_pred, filter_type=filter_type)
    return render_template(
        'history.html',
        active_page='history',
        records=records,
        search_query=search_q,
        current_pred=filter_pred,
        current_type=filter_type
    )

@app.route('/history/<int:scan_id>')
def history_detail(scan_id: int):
    """View details of a specific past scan record."""
    record = get_scan(scan_id)
    if not record:
        flash("Scan record not found.", "error")
        return redirect(url_for('history'))

    return render_template(
        'history_detail.html',
        active_page='history',
        record=record
    )

@app.route('/history/delete/<int:scan_id>', methods=['POST', 'GET'])
def delete_history_item(scan_id: int):
    """Delete a past verification record."""
    deleted = delete_scan(scan_id)
    if deleted:
        flash("Scan record removed from history.", "success")
    else:
        flash("Scan record could not be deleted or does not exist.", "error")
    return redirect(url_for('history'))

@app.route('/about')
def about():
    """Render About page with ML architecture, TF-IDF, OCR, and ethics."""
    _, _, meta = load_ml_assets()
    return render_template('about.html', active_page='about', metadata=meta)

if __name__ == '__main__':
    print("Starting TruthCheck AI Server...")
    load_ml_assets()
    port = int(os.environ.get("PORT", 5000))
    print(f"TruthCheck AI is live at http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
