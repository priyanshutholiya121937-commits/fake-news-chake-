#!/usr/bin/env bash
set -o errexit

# Install tesseract binary on Linux
apt-get update && apt-get install -y tesseract-ocr

# Install python dependencies
pip install -r requirements.txt
