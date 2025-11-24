#!/bin/bash

# install.sh
# Installation script for the Concurrent PDF OCR Extractor.
# Checks for Python and installs required Python libraries.

echo "--- Concurrent PDF OCR Extractor Setup ---"

# --- 1. Check for Python ---
PYTHON_CMD="python3"
if ! command -v $PYTHON_CMD &> /dev/null
then
    PYTHON_CMD="python"
    if ! command -v $PYTHON_CMD &> /dev/null
    then
        echo "Error: Python 3 is not found. Please install Python 3.8+."
        exit 1
    fi
fi

echo "✅ Found Python interpreter: $PYTHON_CMD"


# --- 2. Check for Tesseract (Advisory) ---
TESSERACT_CMD="tesseract"
if ! command -v $TESSERACT_CMD &> /dev/null
then
    echo "⚠️ Warning: Tesseract OCR engine was not found in your system PATH."
    echo "You must install Tesseract (e.g., 'brew install tesseract' or 'sudo apt install tesseract-ocr')."
    echo "If Tesseract is installed in a non-standard location, you must use the '--tesseract-path' argument when running the script."
else
    echo "✅ Found Tesseract OCR engine."
    # Check for Tesseract version and config
    TESSERACT_VERSION=$($TESSERACT_CMD --version 2>&1 | head -n 1)
    echo "   Version: $TESSERACT_VERSION"
fi


# --- 3. Check/Create Virtual Environment ---
if [ ! -d "venv" ]; then
    echo "Creating virtual environment 'venv'..."
    $PYTHON_CMD -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error creating virtual environment."
        exit 1
    fi
fi

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    VENV_ACTIVE=1
elif [ -f "venv/Scripts/activate" ]; then
    # Windows compatibility (CMD/PS will handle activation, but we install here)
    echo "Note: Virtual environment needs manual activation on Windows."
else
    echo "Warning: Could not activate virtual environment."
fi

# --- 4. Install Python Dependencies ---
echo "Installing Python dependencies from requirements.txt..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error installing Python dependencies. Check your internet connection or virtual environment setup."
    # Deactivate if it was activated
    if [ "$VENV_ACTIVE" = 1 ]; then
        deactivate
    fi
    exit 1
fi

echo "✅ All Python dependencies installed successfully."

# --- 5. Download spaCy Language Model ---
echo "Downloading spaCy English language model for proper name detection..."
$PYTHON_CMD -m spacy download en_core_web_sm

if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Failed to download spaCy language model."
    echo "   Proper name detection will be disabled."
    echo "   You can manually install it later with: python -m spacy download en_core_web_sm"
else
    echo "✅ spaCy language model installed successfully."
fi

# --- 6. Final Instructions ---
echo -e "\n--- Setup Complete ---"
echo "To run the script, make sure your virtual environment is active, then execute:"
echo "python pdf_extractor.py <path_to_your_pdf> [options]"

# Deactivate if it was activated
if [ "$VENV_ACTIVE" = 1 ]; then
    deactivate
    echo "Deactivated virtual environment. Run 'source venv/bin/activate' to re-enable it."
fi
