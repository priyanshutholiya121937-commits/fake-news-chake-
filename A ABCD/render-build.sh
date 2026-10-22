#!/usr/bin/env bash
set -o errexit

# Pip packages इंस्टॉल करें
pip install -r requirements.txt

# Render पर बिना root के tesseract डाउनलोड और सेटअप करें
STORAGE_DIR="/opt/render/project/src/.tesseract"
mkdir -p "$STORAGE_DIR"

if [ ! -f "$STORAGE_DIR/bin/tesseract" ]; then
  echo "Downloading standalone tesseract..."
  curl -L -o tesseract.deb http://archive.ubuntu.com/ubuntu/pool/universe/t/tesseract/tesseract-ocr-bin_5.3.4-1build1_amd64.deb || true
  curl -L -o libtesseract.deb http://archive.ubuntu.com/ubuntu/pool/universe/t/tesseract/libtesseract5_5.3.4-1build1_amd64.deb || true
  curl -L -o tessdata.deb http://archive.ubuntu.com/ubuntu/pool/universe/t/tesseract-lang/tesseract-ocr-eng_4.1.0-2_all.deb || true

  dpkg -x tesseract.deb "$STORAGE_DIR" || true
  dpkg -x libtesseract.deb "$STORAGE_DIR" || true
  dpkg -x tessdata.deb "$STORAGE_DIR" || true
  rm -f *.deb
fi
