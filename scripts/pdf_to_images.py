import os
import datetime
import argparse
from pathlib import Path

# Import any external packages you need
import fitz  # PyMuPDF - requires: pip install pymupdf

# --- Core Components for UI ---

NAME = "PDF to Images"
DESCRIPTION = "Convert PDF documents to image files (PNG, JPEG, etc.)"
INPUT_TYPES = "PDF Files (*.pdf)"

PARAMETERS = [
    {
        "name": "image_format",
        "type": "str",
        "default": "PNG",
        "description": "Output image format: PNG, JPEG, JPG, BMP, WEBP"
    },
    {
        "name": "dpi",
        "type": "int",
        "default": 300,
        "description": "Resolution in DPI (higher = better quality but larger files)"
    },
    {
        "name": "start_page",
        "type": "int",
        "default": 1,
        "description": "Starting page number (1-indexed, 0 = first page)"
    },
    {
        "name": "end_page",
        "type": "int",
        "default": 0,
        "description": "Ending page number (0 = all pages)"
    },
    {
        "name": "prefix",
        "type": "str",
        "default": "",
        "description": "Custom prefix for output filenames (optional)"
    }
]

# --- Script Logic ---

def process_files(file_paths, **kwargs):
    '''
    Main processing logic.

    Args:
        file_paths: List of input file paths
        **kwargs: Parameter values from UI
    '''
    # 1. Create output directory
    home_dir = os.path.expanduser("~")
    script_name_slug = NAME.lower().replace(" ", "_")
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    output_folder_path = os.path.join(home_dir, "Downloads", script_name_slug, f"{timestamp}_output")
    os.makedirs(output_folder_path, exist_ok=True)

    # 2. Get parameters
    image_format = kwargs.get("image_format", "PNG").upper()
    dpi = kwargs.get("dpi", 300)
    start_page = kwargs.get("start_page", 1)
    end_page = kwargs.get("end_page", 0)
    prefix = kwargs.get("prefix", "")
    
    # Validate format
    valid_formats = ["PNG", "JPEG", "JPG", "BMP", "WEBP"]
    if image_format not in valid_formats:
        print(f"Warning: Invalid format '{image_format}', using PNG")
        image_format = "PNG"
    
    # Map format to PyMuPDF output format
    format_map = {
        "PNG": "png",
        "JPEG": "jpeg",
        "JPG": "jpeg",
        "BMP": "bmp",
        "WEBP": "webp"
    }
    output_ext = format_map.get(image_format, "png")
    
    # 3. Process files
    total_pages = 0
    total_files = 0
    
    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"Skipping - file not found: {file_path}")
            continue
            
        try:
            # Open PDF
            pdf_doc = fitz.open(file_path)
            pdf_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # Determine page range
            page_count = pdf_doc.page_count
            start_idx = max(0, start_page - 1)  # Convert to 0-indexed
            end_idx = page_count if end_page == 0 else min(end_page, page_count)
            
            if start_idx >= page_count:
                print(f"Warning: Start page {start_page} exceeds page count for {file_path}")
                pdf_doc.close()
                continue
            
            # Convert each page
            for page_num in range(start_idx, end_idx):
                page = pdf_doc[page_num]
                
                # Create output filename
                page_num_display = page_num + 1
                if prefix:
                    output_filename = f"{prefix}_{pdf_name}_page_{page_num_display}.{output_ext}"
                else:
                    output_filename = f"{pdf_name}_page_{page_num_display}.{output_ext}"
                
                output_path = os.path.join(output_folder_path, output_filename)
                
                # Render page to image
                pix = page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72))
                pix.save(output_path)
                
                total_pages += 1
                print(f"Saved: {output_filename}")
            
            pdf_doc.close()
            total_files += 1
            
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    print(f"\nProcessing complete!")
    print(f"Files processed: {total_files}")
    print(f"Pages converted: {total_pages}")
    print(f"Output folder: {output_folder_path}")

# --- Command-Line Execution ---

def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("file_paths", nargs="+", help="Paths to input PDF files")
    for param in PARAMETERS:
        if param["type"] == "str":
            parser.add_argument(f'--{param["name"]}', type=str, default=param["default"])
        elif param["type"] == "int":
            parser.add_argument(f'--{param["name"]}', type=int, default=param["default"])
        elif param["type"] == "float":
            parser.add_argument(f'--{param["name"]}', type=float, default=param["default"])
        elif param["type"] == "bool":
            parser.add_argument(f'--{param["name"]}', type=bool, default=param["default"])
    args = parser.parse_args()
    
    # Build kwargs dict
    kwargs = {}
    for param in PARAMETERS:
        kwargs[param["name"]] = getattr(args, param["name"])
    
    process_files(args.file_paths, **kwargs)

if __name__ == "__main__":
    main()
