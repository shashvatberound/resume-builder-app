# pdf_to_json_extractor.py

import fitz  # PyMuPDF
import os
import argparse
import json  # NEW: Import the json library
from datetime import datetime, timezone # NEW: For timestamping

def extract_pdf_data_as_json(pdf_path):
    """
    Opens a PDF and extracts its text into a structured dictionary.

    Args:
        pdf_path (str): The full path to the PDF file.

    Returns:
        dict: A dictionary containing metadata and extracted text, or None on error.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at '{pdf_path}'")
        return None

    try:
        doc = fitz.open(pdf_path)
        
        content_by_page = {}
        all_text_parts = []
        
        # Loop through each page to extract text page by page
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text("text")
            # Store text for the current page
            content_by_page[f"page_{page_num + 1}"] = page_text
            all_text_parts.append(page_text)
        
        doc.close()

        # Combine all parts into a single string
        full_text = "\n".join(all_text_parts)

        # Create the final structured dictionary (JSON object)
        output_data = {
            "metadata": {
                "source_file": os.path.basename(pdf_path),
                "total_pages": len(content_by_page),
                "extraction_timestamp_utc": datetime.now(timezone.utc).isoformat()
            },
            "content_by_page": content_by_page,
            "full_text": full_text.strip()
        }
        
        return output_data
        
    except Exception as e:
        print(f"An error occurred while processing the PDF: {e}")
        return None

def save_data_to_json(data, output_path):
    """Saves the structured data to a .json file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            # Use indent=4 for a human-readable, pretty-printed JSON file
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"\n✅ JSON data successfully saved to: {output_path}")
    except Exception as e:
        print(f"\n❌ Error: Could not save data to JSON file '{output_path}': {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A command-line tool to extract all text from a PDF file into JSON format."
    )
    
    parser.add_argument(
        "pdf_path", 
        help="The full path to the PDF file you want to extract text from."
    )
    
    # UPDATED: The help text now specifies a .json file
    parser.add_argument(
        "-o", "--output", 
        help="Optional: The path to a .json file to save the extracted data."
    )
    
    args = parser.parse_args()

    # --- SCRIPT EXECUTION ---
    print(f"Processing file: {args.pdf_path}")
    
    extracted_data = extract_pdf_data_as_json(args.pdf_path)
    
    if extracted_data:
        # If an output file is specified, save the JSON to that file
        if args.output:
            save_data_to_json(extracted_data, args.output)
        # Otherwise, print the JSON directly to the console
        else:
            print("\n" + "="*25 + " EXTRACTED JSON DATA " + "="*25 + "\n")
            # Use json.dumps with indent=2 for a nice-looking print in the terminal
            print(json.dumps(extracted_data, indent=2))
            print("\n" + "="*71 + "\n")