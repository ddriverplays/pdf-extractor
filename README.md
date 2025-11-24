Concurrent PDF OCR Extractor

This powerful tool is essential for writers, researchers, journalists, and the OSINT (Open-Source Intelligence) community who need to quickly and accurately extract actionable text from large volumes of scanned or image-based PDF documents. By leveraging concurrent processing and high-DPI rendering, it transforms unsearchable PDFs into usable, indexed text for analysis and citation.

---

A robust Python script that extracts text from PDF files by converting pages to high-DPI images and performing Optical Character Recognition (OCR) using Tesseract. This tool uses concurrent processing for speed and supports resuming interrupted jobs.

---

## Features

* Concurrent Processing: Utilizes multiple CPU cores to process pages simultaneously, significantly reducing extraction time.
* High Accuracy: Renders PDF pages to high-resolution PNGs (default 300 DPI) for improved OCR results.
* Resume Capability: Automatically detects partial output and allows the user to resume processing from the last successfully completed page.
* Command-Line Interface (CLI): Supports easy configuration via command-line arguments.
* Output Consolidation: Merges all successfully extracted text into a single combined_output.txt file.

---

## Prerequisites

You must have the following software installed on your system before running the script:

### 1. Python 3

The script requires Python 3.8 or newer.

### 2. Tesseract OCR Engine

Tesseract is the core OCR engine used by the script.

* Installation: Install Tesseract via your system's package manager.
    * macOS (using Homebrew):
        brew install tesseract
    * Linux (using apt):
        sudo apt install tesseract-ocr
    * Windows: Download the installer from the Tesseract GitHub. You will need to note the installation path for the --tesseract-path argument later.
* Language Packs: If you need to process languages other than English (eng), you must install the corresponding Tesseract language packs (e.g., tesseract-ocr-fra for French, tesseract-ocr-deu for German).

### 3. Required Python Libraries

The script relies on PyMuPDF (for PDF rendering) and Pillow/pytesseract (for OCR).

---

## Installation & Setup

### A. Clone the Repository

Assuming your script is named pdf_extractor.py, navigate to the directory where you saved it.

### B. Setup Python Environment

It is highly recommended to use a virtual environment.

# 1. Create a virtual environment
python3 -m venv venv

# 2. Activate the virtual environment
# On Linux/macOS
source venv/bin/activate
# On Windows (CMD)
venv\Scripts\activate
# On Windows (PowerShell)
.\venv\Scripts\Activate.ps1


### C. Install Dependencies

pip install PyMuPDF pytesseract Pillow


### Automated Setup (Recommended)

Run the simple installation script to check for Python dependencies.

chmod +x install.sh
./install.sh


---

## Usage

The script can be run using a single required argument (the PDF path) and several optional arguments.

### Basic Execution

Run the script, providing the path to your PDF file:

python pdf_extractor.py path/to/your/document.pdf

Upon execution, the script will:
1. Check for previous progress.
2. Prompt you to choose to process all pages, resume from the last page, or select a specific range.

### Example: Resume an Interrupted Job

If you stopped processing a 100-page document at page 50, rerunning the command will let you resume:

python pdf_extractor.py my_long_report.pdf

# Output will prompt:
Found existing files. Last successfully processed page was 50 of 100.
Enter 'r' to resume at page 51, 'a' for all, 'n' for a new range, or 'q' to quit: r


### Advanced Arguments

You can override the default configuration using the following flags:

| Argument | Default | Description |
| :--- | :--- | :--- |
| **[PDF_PATH]** | N/A | **Required**. Path to the input PDF file. |
| --output-dir | . | The base directory where the processing folder will be created. |
| --dpi | 300 | Rendering quality (DPI). Higher values lead to better OCR but slower processing. |
| --lang | eng | Tesseract language code(s). Use + to combine (e.g., eng+deu). |
| --tesseract-path | /usr/bin/tesseract | Full path to the Tesseract executable. Crucial for Windows/non-standard installs. |

### Command Examples

**1. Process a range with high quality (600 DPI) using English and French:**

First, start the script. When prompted, enter the range (n or 1-50):

python pdf_extractor.py thesis.pdf --dpi 600 --lang eng+fra

# When prompted
Enter 'a' for all pages, 'r' for a new range (e.g., 5-10), or 'q' to quit: n
Enter page range (e.g., 5-10): 1-50

**2. Specify the Tesseract path for a Windows installation:**

python pdf_extractor.py my_doc.pdf --tesseract-path "C:\Program Files\Tesseract-OCR\tesseract.exe"

---

# Output Structure

A new directory named <pdf_name>_processed will be created inside your chosen output directory.

<pdf_name>_processed/
├── combined_output.txt      # The final merged text document.
├── png_images/
│   ├── 0001.png
│   ├── 0002.png
│   └── ...
└── text_files/
    ├── 0001.txt             # Text output for page 1.
    ├── 0002.txt             # Text output for page 2.
    └── ...

> Note: If a page fails OCR, its corresponding .txt file will contain an "OCR FAILED" marker along with the error message. Failed pages are automatically skipped during the consolidation into combined_output.txt.
