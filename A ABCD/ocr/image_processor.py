import os
import re
import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Dict, Any
import pytesseract

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
    try:
        # Tesseract का उपयोग करके इमेज से टेक्स्ट निकालें
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        cleaned_text = text.strip()
        
        if len(cleaned_text) > 5:
            return {
                "success": True, 
                "extracted_text": cleaned_text,
                "raw_text": text,
                "confidence": 1.0,
                "message": ""
            }
        else:
            return {
                "success": False, 
                "message": "No readable news text was detected. Please take a clearer photo.",
                "confidence": 0.0
            }
            
    except Exception as e:
        print(f"OCR Error: {e}")
        return {
            "success": False, 
            "message": str(e),
            "confidence": 0.0
        }
