# TruthCheck AI — AI-Powered Fake News Detection System

> **AI-powered news verification at your fingertips.**

TruthCheck AI is a full-stack fake news detection web application built with Python Flask, Scikit-learn Machine Learning (TF-IDF + Multinomial Naive Bayes / Calibrated Linear SVM / Logistic Regression), OpenCV + EasyOCR image processing, SQLite scan persistence, and the exact sleek dark-mode glassmorphic user interface.

---

## 🚀 Features

- **Text Verification (`/text-check`)**: Paste any news headline or article to perform instant linguistic veracity analysis.
- **Camera OCR Scanner (`/image-scanner`)**: Live in-browser camera scanning (`navigator.mediaDevices.getUserMedia`) to capture newspaper clippings or digital screens and extract text with OpenCV + EasyOCR.
- **Drag & Drop Image Upload**: Upload news images (`.jpg`, `.jpeg`, `.png`, `.webp`, up to 5 MB) for instant automated OCR & classification.
- **Machine Learning Engine**: Multi-model comparison pipeline comparing Logistic Regression, Multinomial Naive Bayes, and Calibrated Linear SVM with n-gram TF-IDF vectorization.
- **Scan History Database (`/history`)**: Local SQLite persistence with search, filtering by classification category, and full audit logs.
- **About & Architecture (`/about`)**: Interactive visual processing pipelines, metric comparisons, and ethical guidance.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11+, Flask, SQLite
- **Machine Learning**: Scikit-learn, Pandas, NumPy, NLTK, TF-IDF
- **Computer Vision & OCR**: OpenCV, Pillow, EasyOCR / PyTesseract
- **Frontend**: HTML5, Vanilla CSS3 (Dark Glassmorphism, animations, responsive layouts), Vanilla JavaScript (ES6+)
- **Design Tokens**: Geist Pixel Circle / Bubbledot typography, Inter sans-serif, Font Awesome 6 icons

---

## ⚡ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Train the Machine Learning Model
```bash
python model/train_model.py
```

### 3. Launch the Application
```bash
python app.py
```

Open your browser and navigate to:
```text
http://localhost:5000
```

---

## 📂 Project Structure

```text
truthcheck-ai/
│
├── app.py                      # Main Flask application & routing
├── requirements.txt            # Python package dependencies
├── README.md                   # Project documentation & setup guide
├── fake_news.db                # SQLite history database
│
├── model/
│   ├── train_model.py          # ML training & model comparison script
│   ├── fake_news_model.pkl     # Serialized best ML classifier
│   ├── tfidf_vectorizer.pkl    # Serialized TF-IDF feature extractor
│   └── model_metadata.json     # Performance metrics & model parameters
│
├── dataset/
│   └── fake_news.csv           # Multi-category training dataset
│
├── ocr/
│   └── image_processor.py      # OpenCV image filtering & OCR extraction
│
├── database/
│   └── database.py             # SQLite connection & CRUD methods
│
├── templates/
│   ├── base.html               # Master layout with navbar & animated background
│   ├── index.html              # Hero landing page & feature cards
│   ├── text_check.html         # Text analysis form & sample loaders
│   ├── image_scanner.html      # Camera & drag-and-drop OCR scanner
│   ├── result.html             # Classification result & confidence meter
│   ├── history.html            # Scan history list, search & filters
│   ├── history_detail.html     # Single record breakdown
│   └── about.html              # Architecture diagrams & methodology
│
├── static/
│   ├── css/
│   │   └── style.css           # Design tokens, cards, animations & typography
│   ├── js/
│   │   ├── camera.js           # Live camera stream & upload preview
│   │   └── main.js             # Mobile menu, stats counters & utilities
│   ├── fonts/
│   │   └── GeistPixel-Circle.woff2
│   └── images/
│       └── logo.webp
│
└── uploads/                    # Temporary staging for uploaded scans
```
