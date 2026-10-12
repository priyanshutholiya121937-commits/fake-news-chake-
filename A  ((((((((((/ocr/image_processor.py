import os
import re
import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Dict, Any

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

# Lazy loader for EasyOCR reader to optimize startup latency
_easyocr_reader = None

def get_easyocr_reader():
    global _easyocr_reader
    if _easyocr_reader is None:
        try:
            import easyocr
            # Initialize with English, CPU mode by default
            _easyocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        except Exception as e:
            print(f"EasyOCR initialization warning: {e}")
            _easyocr_reader = False
    return _easyocr_reader if _easyocr_reader is not False else None

def is_allowed_file(filename: str) -> bool:
    """Check if the filename has an authorized image extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_image(file_path: str) -> Tuple[bool, str]:
    """Validate image file existence, size, and readable image data."""
    if not os.path.exists(file_path):
        return False, "Image file does not exist."
    
    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE_BYTES:
        return False, f"Image exceeds maximum permitted file size of 5 MB ({round(file_size / (1024*1024), 2)} MB)."

    try:
        with Image.open(file_path) as img:
            img.verify()
    except Exception:
        return False, "File is corrupted or not a valid image format."
    
    return True, "Valid"

def preprocess_image(image_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load and preprocess image using OpenCV pipeline:
    Resize -> Grayscale -> Contrast Enhancement (CLAHE) -> Denoise -> Adaptive Threshold
    """
    # Read image using OpenCV
    img = cv2.imread(image_path)
    if img is None:
        # Fallback reading with PIL in case of exotic color spaces
        pil_img = Image.open(image_path).convert('RGB')
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    # 1. Resize if too large or too small for optimal OCR
    h, w = img.shape[:2]
    max_dim = 1800
    min_dim = 600
    scale = 1.0

    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
    elif min(h, w) < min_dim:
        scale = min_dim / min(h, w)

    if scale != 1.0:
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC)

    # 2. Convert to Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 3. Contrast Enhancement via CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # 4. Bilateral Denoising (preserves sharp text edges while suppressing background noise)
    denoised = cv2.bilateralFilter(enhanced, d=9, sigmaColor=75, sigmaSpace=75)

    # 5. Adaptive Thresholding (Otsu & Gaussian combined)
    thresh = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 10
    )

    return gray, thresh

def clean_ocr_text(raw_text: str) -> str:
    """Clean and normalize text extracted via OCR."""
    if not raw_text:
        return ""
    # Normalize whitespace
    text = re.sub(r'[\r\n\t]+', ' ', raw_text)
    # Remove control characters and non-printable noise
    text = ''.join(ch for ch in text if ch.isprintable() or ch == ' ')
    # Fix repeated punctuation or fragmented OCR symbols
    text = re.sub(r'[_~|`\^]+', ' ', text)
    # Normalize multiple spaces
    text = re.sub(r'\s{2,}', ' ', text).strip()
    return text

def extract_text_from_image(image_path: str) -> Dict[str, Any]:
    """
    Run OCR on image file using EasyOCR (with PyTesseract fallback).
    Returns dict with extracted_text, raw_text, success, message, confidence.
    """
    valid, message = validate_image(image_path)
    if not valid:
        return {
            "success": False,
            "extracted_text": "",
            "message": message,
            "confidence": 0.0
        }

    try:
        gray, thresh = preprocess_image(image_path)
        extracted_segments = []
        confidences = []

        # 1. Try EasyOCR
        reader = get_easyocr_reader()
        if reader is not None:
            # Perform OCR on enhanced grayscale
            results = reader.readtext(gray)
            for (bbox, text, conf) in results:
                if text.strip() and conf > 0.2:
                    extracted_segments.append(text.strip())
                    confidences.append(float(conf))

            # If grayscale yielded few tokens, try thresholded image
            if len(" ".join(extracted_segments).split()) < 5:
                thresh_results = reader.readtext(thresh)
                thresh_segments = [t.strip() for (_, t, c) in thresh_results if t.strip() and c > 0.2]
                if len(" ".join(thresh_segments).split()) > len(" ".join(extracted_segments).split()):
                    extracted_segments = thresh_segments
                    confidences = [float(c) for (_, _, c) in thresh_results if c > 0.2]

        # 2. Fallback to PyTesseract if EasyOCR produced nothing or was unavailable
        if not extracted_segments:
            try:
                import pytesseract
                # Test pytesseract
                tess_text = pytesseract.image_to_string(gray)
                if tess_text.strip():
                    extracted_segments.append(tess_text.strip())
                    confidences.append(0.75)
            except Exception as tess_err:
                pass

        raw_combined = " ".join(extracted_segments)
        cleaned_text = clean_ocr_text(raw_combined)
        avg_confidence = round(float(np.mean(confidences)) * 100, 2) if confidences else 0.0

        if not cleaned_text or len(cleaned_text.split()) < 3:
            return {
                "success": False,
                "extracted_text": cleaned_text,
                "raw_text": raw_combined,
                "message": "No readable news text was detected. Please take a clearer photo with good lighting and centered text.",
                "confidence": avg_confidence
            }

        return {
            "success": True,
            "extracted_text": cleaned_text,
            "raw_text": raw_combined,
            "message": f"Successfully extracted {len(cleaned_text.split())} words from photo.",
            "confidence": avg_confidence
        }

    except Exception as e:
        return {
            "success": False,
            "extracted_text": "",
            "raw_text": "",
            "message": f"OCR extraction error: {str(e)}",
            "confidence": 0.0
        }
