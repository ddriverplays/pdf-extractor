import os
import pathlib
import fitz # PyMuPDF library for PDF manipulation
import pytesseract # Python wrapper for Tesseract OCR
from PIL import Image # Pillow library for image handling (used by pytesseract)
import time
import sys # Used for exiting the script
import concurrent.futures # Used for multithreaded processing
import argparse # NEW: For command-line arguments
import contextlib # NEW: For suppressing warnings

# --- Configuration Defaults (used if not overridden by CLI) ---
DEFAULT_TESSERACT_PATH = '/usr/bin/tesseract' 
DEFAULT_LANGUAGES = 'eng'
DEFAULT_DPI = 300 # Equivalent to zoom=4 (300/72 ~ 4.16)

# Global configuration dictionary populated by argparse and the interactive loop
GLOBAL_CONFIG = {
    'pdf_path': None,
    'output_dir': '.',
    'dpi': DEFAULT_DPI,
    'languages': DEFAULT_LANGUAGES,
    'tesseract_path': DEFAULT_TESSERACT_PATH,
    'start_page': 1,
    'end_page': None
}

# --- Tesseract Warning Suppression Context Manager (Suggestion 3) ---
@contextlib.contextmanager
def suppress_stderr():
    """Context manager to suppress stderr output (Tesseract warnings)."""
    # Save the current stderr
    original_stderr = sys.stderr
    try:
        # Redirect stderr to /dev/null
        sys.stderr = open(os.devnull, 'w')
        yield
    finally:
        # Restore the original stderr
        sys.stderr.close()
        sys.stderr = original_stderr


# Function to encapsulate single-page processing for concurrency
def process_page_task(pdf_path: str, page_num: int, output_dir: pathlib.Path, matrix: fitz.Matrix, languages: str) -> tuple[bool, int, str]:
    """
    Handles the PNG extraction and OCR for a single, 0-based page index.
    Returns (success_status, page_index, error_message or None). (Suggestion 1)
    """
    page_index = page_num + 1 # 1-based index for naming and logging
    
    # Directory setup (assuming they exist from process_pdf)
    png_dir = output_dir / "png_images"
    txt_dir = output_dir / "text_files"
    
    png_filepath = png_dir / f"{page_index:04d}.png"
    txt_filepath = txt_dir / f"{page_index:04d}.txt"

    # Optimization: Skip if page is already fully processed
    if png_filepath.exists() and txt_filepath.exists():
        return (True, page_index, None)
    
    doc = None # Initialize outside try
    try:
        # Load page from PDF (must be done inside the thread)
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_num)
        
        # --- 1. Extract Page as PNG ---
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        pix.save(str(png_filepath))
        
        # --- 2. Convert PNG to TXT using OCR (with warning suppression) ---
        with suppress_stderr(): # Suggestion 3 implemented
            text = pytesseract.image_to_string(str(png_filepath), lang=languages)

        with open(txt_filepath, 'w', encoding='utf-8') as f:
            f.write(text.strip())
        
        return (True, page_index, None)

    except Exception as e:
        # Suggestion 1: Capture specific error details
        error_msg = f"OCR failed: {type(e).__name__}: {str(e)}"
        # Create a failure file for tracking
        with open(txt_filepath, 'w', encoding='utf-8') as f:
            f.write(f"OCR FAILED FOR THIS PAGE: {error_msg}")
        return (False, page_index, error_msg)

    finally:
        if doc:
            doc.close()


def get_last_processed_page(output_dir: pathlib.Path) -> int:
    """
    Checks the output directory for existing PNG and TXT files in their respective
    subdirectories to determine the last successfully processed page number.
    Returns 0 if no files are found.
    """
    png_dir = output_dir / "png_images"
    txt_dir = output_dir / "text_files"
    
    if not png_dir.exists() or not txt_dir.exists():
        return 0

    processed_pages = set()
    
    for f in png_dir.iterdir():
        if f.suffix == '.png' and f.stem.isdigit():
            page_num_str = f.stem
            txt_path = txt_dir / f"{page_num_str}.txt"
            
            # A page is considered complete only if both files exist
            if txt_path.exists():
                processed_pages.add(int(page_num_str))

    if not processed_pages:
        return 0
    
    return max(processed_pages)

def combine_text_files(output_dir: pathlib.Path, start_page: int, end_page: int):
    """
    Merges all successfully extracted text files in the range into one master file.
    """
    txt_dir = output_dir / "text_files"
    master_file = output_dir / "combined_output.txt"
    
    print(f"\n--- Combining Text Output (Pages {start_page}-{end_page}) ---")
    
    sorted_files = []
    # Only iterate through the files that were part of the current run's page range
    for page_index in range(start_page, end_page + 1):
        filename = f"{page_index:04d}.txt"
        filepath = txt_dir / filename
        
        # Check if the file exists AND if it contains the failure marker
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read(50) # Read first 50 chars to check for error
                    if "OCR FAILED" not in content:
                        sorted_files.append(filepath)
            except Exception as e:
                 print(f"Warning: Could not read file {filepath.name} for combination check: {e}")

    if not sorted_files:
        print("No successful text files found to combine in this range.")
        return

    try:
        with open(master_file, 'w', encoding='utf-8') as outfile:
            for filepath in sorted_files:
                outfile.write(f"\n\n==================== PAGE {int(filepath.stem)} ====================\n\n")
                with open(filepath, 'r', encoding='utf-8') as infile:
                    outfile.write(infile.read())
        
        print(f"Successfully merged {len(sorted_files)} pages into: {master_file.name}")
    except Exception as e:
        print(f"ERROR combining files: {e}")

# Main Processing Function
def process_pdf(config: dict):
    """
    Extracts pages concurrently using a ThreadPoolExecutor based on provided configuration.
    """
    pdf_path = config['pdf_path']
    output_dir_base = config['output_dir']
    start_page = config['start_page']
    end_page = config['end_page']
    dpi = config['dpi']
    languages = config['languages']
    tesseract_path = config['tesseract_path']
    
    # 1. Setup paths
    pdf_file = pathlib.Path(pdf_path)
    safe_name = pdf_file.stem.replace(' ', '_')
    output_dir = pathlib.Path(output_dir_base) / f"{safe_name}_processed"
    
    png_dir = output_dir / "png_images"
    txt_dir = output_dir / "text_files"

    png_dir.mkdir(parents=True, exist_ok=True)
    txt_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Set Tesseract command
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

    print(f"Output directory: {output_dir}")
    print(f"Images will be saved to: {png_dir.name}/")
    print(f"Text will be saved to: {txt_dir.name}/")
    print(f"Rendering DPI: {dpi}")
    print(f"OCR Languages: {languages}")
    print(f"Processing range: Page {start_page} to Page {end_page}")

    # 3. Check Tesseract setup
    try:
        pytesseract.get_tesseract_version()
    except pytesseract.TesseractNotFoundError:
        print("\n--- CRITICAL ERROR ---")
        print("Tesseract executable not found.")
        print(f"Path currently set to: {tesseract_path}")
        print("Please ensure Tesseract is installed and the correct path is provided via --tesseract-path.")
        return

    try:
        # 4. Define the rendering matrix (Suggestion 2: DPI Configuration)
        zoom = dpi / 72.0 
        matrix = fitz.Matrix(zoom, zoom)

        start_time = time.time()
        
        # PyMuPDF uses 0-based indexing for the internal pages list
        pages_to_process_indices = range(start_page - 1, end_page)
        pages_to_process_count = len(pages_to_process_indices)

        print(f"\nStarting concurrent processing of {pages_to_process_count} pages...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
            
            # Submit tasks for each page index
            futures = [
                executor.submit(process_page_task, pdf_path, page_num, output_dir, matrix, languages)
                for page_num in pages_to_process_indices
            ]
            
            # Wait for all futures to complete (Suggestion 1: detailed error logging)
            success_count = 0
            failure_count = 0
            failure_messages = []
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    success, page_index, error_msg = future.result()
                    if success:
                        # Avoid printing success messages from threads, rely on final count
                        if error_msg is None: # Only count as success if it wasn't a skipped, already-processed page
                            success_count += 1 
                        # Print progress for pages that actually needed processing
                        print(f"  [SUCCESS] Page {page_index:04d} processed.")

                    else:
                        failure_count += 1
                        failure_messages.append(f"Page {page_index:04d}: {error_msg}")
                        print(f"  [FAILURE] Page {page_index:04d} failed. See full details below.")
                except Exception as e:
                    print(f"A thread encountered an unexpected execution error: {e}")
                    failure_count += 1

        end_time = time.time()
        duration = end_time - start_time
        print("\n--- Processing Complete ---")
        print(f"Total time: {duration:.2f} seconds.")
        print(f"Pages successful: {success_count}. Pages failed: {failure_count}.")
        
        # Log all specific failures (Suggestion 1 continued)
        if failure_messages:
            print("\n--- DETAILED FAILURE REPORT ---")
            for msg in failure_messages:
                print(f"- {msg}")
            print("-------------------------------\n")


        # Run the combination step only if there were successful extractions
        if success_count > 0:
            combine_text_files(output_dir, start_page, end_page)

    except Exception as e:
        print(f"\nAn unexpected error occurred during main execution: {e}")


def setup_and_run():
    """Handles command-line parsing and main interactive loop."""
    
    # Setup Argument Parser (Suggestion 4: Argparse)
    parser = argparse.ArgumentParser(
        description="Concurrent PDF to PNG and OCR Text Extractor with resume support.",
        epilog="Example: python pdf_extractor.py my_book.pdf --dpi 600 --lang eng+deu",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        'pdf_path',
        type=str,
        help="Path to the input PDF file (e.g., 'document.pdf')."
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='.',
        help="Base directory for output (default: current directory). Output folder is '<pdf_name>_processed'."
    )
    parser.add_argument(
        '--dpi',
        type=int,
        default=DEFAULT_DPI,
        help=f"Rendering quality in DPI (default: {DEFAULT_DPI}). Higher DPI = better OCR but slower processing."
    )
    parser.add_argument(
        '--lang',
        type=str,
        default=DEFAULT_LANGUAGES,
        help=f"Tesseract languages (default: '{DEFAULT_LANGUAGES}'). Use '+' to combine (e.g., 'eng+fra'). Requires language packs to be installed."
    )
    parser.add_argument(
        '--tesseract-path',
        type=str,
        default=DEFAULT_TESSERACT_PATH,
        help=f"Full path to the Tesseract executable (default: '{DEFAULT_TESSERACT_PATH}')."
    )

    args = parser.parse_args()

    # Apply parsed arguments to config
    GLOBAL_CONFIG['pdf_path'] = args.pdf_path
    GLOBAL_CONFIG['output_dir'] = args.output_dir
    GLOBAL_CONFIG['dpi'] = args.dpi
    GLOBAL_CONFIG['languages'] = args.lang
    GLOBAL_CONFIG['tesseract_path'] = args.tesseract_path
    
    # --- File/Directory Checks ---
    pdf_file = pathlib.Path(GLOBAL_CONFIG['pdf_path'])
    if not pdf_file.exists():
        print(f"Error: PDF file not found at '{GLOBAL_CONFIG['pdf_path']}'.")
        sys.exit(1)

    safe_name = pdf_file.stem.replace(' ', '_')
    output_dir = pathlib.Path(GLOBAL_CONFIG['output_dir']) / f"{safe_name}_processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n--- PDF Extractor Setup ---")
    
    # Get total pages and last processed page
    try:
        doc = fitz.open(GLOBAL_CONFIG['pdf_path'])
        total_pages = len(doc)
        doc.close()
    except Exception as e:
        print(f"Error reading PDF: {e}")
        sys.exit(1)

    GLOBAL_CONFIG['end_page'] = total_pages
    last_page = get_last_processed_page(output_dir)
    
    # Interactive menu for range/resume selection
    if last_page > 0:
        print(f"Found existing files. Last successfully processed page was {last_page} of {total_pages}.")
        mode_prompt = f"Enter 'r' to resume at page {last_page + 1}, 'a' for all, 'n' for a new range, or 'q' to quit: "
    else:
        print(f"PDF contains {total_pages} pages. No existing output found.")
        mode_prompt = "Enter 'a' for all pages, 'r' for a range (e.g., 5-10), or 'q' to quit: "

    
    while True:
        try:
            mode = input(mode_prompt).strip().lower()
            
            start_page = 1
            
            if mode == 'q':
                print("Exiting script.")
                sys.exit(0)
            
            elif mode == 'r':
                if last_page > 0:
                    start_page = last_page + 1
                    if start_page > total_pages:
                        print("All pages already processed!")
                        sys.exit(0)
                    print(f"RESUMING processing from page {start_page} to {total_pages}.")
                    break
                else:
                    print("No previous progress found. Please choose 'a' or enter a range.")
                    # Fallback to the initial prompt if 'r' is chosen with no history
                    mode_prompt = "Enter 'a' for all pages, 'r' for a range (e.g., 5-10), or 'q' to quit: "
                    continue
            
            elif mode == 'a':
                start_page = 1
                print(f"Processing ALL pages: 1 to {total_pages}.")
                break

            elif mode == 'n' or ('-' in mode and mode != 'r'):
                if mode == 'n':
                    range_input = input(f"Enter new page range (e.g., '1-{total_pages}'): ").strip()
                else:
                    range_input = mode
                    
                start_str, end_str = range_input.split('-')
                start_page_input = int(start_str)
                end_page_input = int(end_str)

                # Validation against PDF limits
                if not (1 <= start_page_input <= end_page_input <= total_pages):
                    print(f"Error: Invalid page range '{range_input}'. Range must be between 1 and {total_pages}.")
                    continue
                
                start_page = start_page_input
                GLOBAL_CONFIG['end_page'] = end_page_input # Override end_page for this specific range
                print(f"Processing selected range: Page {start_page} to {end_page_input}.")
                break

            else:
                print("Invalid command.")
                
        except ValueError:
            print("Invalid input for range. Please use format 'START-END' or a command like 'a', 'r', 'n', or 'q'.")
        except Exception as e:
            print(f"An error occurred during setup: {e}")
            sys.exit(1)

    GLOBAL_CONFIG['start_page'] = start_page
    # Run the main processing function
    process_pdf(GLOBAL_CONFIG)


if __name__ == "__main__":
    setup_and_run()
