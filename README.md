# Concurrent PDF OCR Extractor

### This powerful tool is essential for writers, researchers, journalists, and the OSINT (Open-Source Intelligence) community who need to quickly and accurately extract actionable text from large volumes of scanned or image-based PDF documents. By leveraging concurrent processing and high-DPI rendering, it transforms unsearchable PDFs into usable, indexed text for analysis and citation.

---

A robust Python script that extracts text from PDF files by converting pages to high-DPI images and performing Optical Character Recognition (OCR) using Tesseract. This tool uses concurrent processing for speed and supports resuming interrupted jobs.

---

## Features

* **Concurrent Processing**: Utilizes multiple CPU cores to process pages simultaneously, significantly reducing extraction time.
* **High Accuracy**: Renders PDF pages to high-resolution PNGs (default 300 DPI) for improved OCR results.
* **Resume Capability**: Automatically detects partial output and allows the user to resume processing from the last successfully completed page.
* **Command-Line Interface (CLI)**: Supports easy configuration via command-line arguments.
* **Output Consolidation**: Merges all successfully extracted text into a single `combined_output.txt` file.
* **Word Count Analysis**: Generates comprehensive CSV reports with:
  - Total document word count
  - Per-page word counts
  - Individual word occurrence tracking with page numbers
* **Proper Name Detection**: Uses AI-powered Named Entity Recognition (NER) to identify and track person names with:
  - Occurrence counts for each name
  - Page numbers where each name appears
  - Exported to CSV for easy analysis

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

The script relies on several Python libraries:

* **PyMuPDF** (fitz): For PDF rendering
* **Pillow/pytesseract**: For OCR processing
* **spaCy**: For Named Entity Recognition (proper name detection)

All dependencies are listed in `requirements.txt` and will be installed automatically by the setup script.

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

Install all required Python libraries from the requirements file:

```bash
pip install -r requirements.txt
```

Then download the spaCy language model for proper name detection:

```bash
python -m spacy download en_core_web_sm
```

### Automated Setup (Recommended)

Run the installation script to automatically set up the environment:

```bash
chmod +x install.sh
./install.sh
```

This script will:
- Check for Python and Tesseract
- Create a virtual environment
- Install all dependencies from `requirements.txt`
- Download the spaCy language model


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

A new directory named `<pdf_name>_processed` will be created inside your chosen output directory.

```
<pdf_name>_processed/
├── combined_output.txt          # The final merged text document
├── word_count_report.csv        # Word count analysis (NEW)
├── proper_names_report.csv      # Proper names detected (NEW)
├── png_images/
│   ├── 0001.png
│   ├── 0002.png
│   └── ...
└── text_files/
    ├── 0001.txt                 # Text output for page 1
    ├── 0002.txt                 # Text output for page 2
    └── ...
```

> **Note**: If a page fails OCR, its corresponding `.txt` file will contain an "OCR FAILED" marker along with the error message. Failed pages are automatically skipped during consolidation.

---

## CSV Reports

The extractor automatically generates two CSV reports for analysis:

### 1. Word Count Report (`word_count_report.csv`)

Provides comprehensive word statistics:

**Document Summary Section:**
- Total word count across all pages
- Number of pages analyzed
- Count of unique words

**Per-Page Word Counts:**
- Individual word count for each page

**Word Occurrence Details:**
- Every unique word (3+ characters)
- Total occurrences
- All page numbers where it appears

**Example:**
```csv
Word,Total Occurrences,Pages
dog,75,"3, 36, 73, 89, 102"
cat,42,"5, 12, 89"
```

### 2. Proper Names Report (`proper_names_report.csv`)

Identifies person names using AI-powered Named Entity Recognition:

**Contents:**
- Person names detected in the document
- Total occurrences for each name
- All page numbers where the name appears
- Sorted by frequency (most common first)

**Example:**
```csv
Name,Total Occurrences,Pages
John Smith,92,"254, 340, 533, 678"
Jane Doe,45,"12, 89, 234, 456"
```

> **Note**: Proper name detection requires spaCy and the English language model. If not installed, this feature will be skipped with a warning message.
