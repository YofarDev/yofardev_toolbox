import os
import datetime
import argparse
from pathlib import Path
from PIL import Image

# --- Core Components for UI ---

NAME = "Image Resizer (Fixed Size)"
DESCRIPTION = "Resizes images to a fixed width and height, ignoring original aspect ratio."
INPUT_TYPES = "Images (*.png *.jpg *.jpeg *.webp *.bmp)"

PARAMETERS = [
    {
        "name": "width",
        "type": "int",
        "default": 800,
        "description": "Target width in pixels"
    },
    {
        "name": "height",
        "type": "int",
        "default": 600,
        "description": "Target height in pixels"
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
    script_name_slug = "image_resizer_fixed"
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    output_folder_path = os.path.join(home_dir, "Downloads", script_name_slug, f"{timestamp}_output")
    os.makedirs(output_folder_path, exist_ok=True)

    # Get parameters
    target_width = kwargs.get("width", 800)
    target_height = kwargs.get("height", 600)

    # 2. Process files
    for file_path in file_paths:
        try:
            if not os.path.isfile(file_path):
                continue
                
            with Image.open(file_path) as img:
                # Convert to RGB if necessary (e.g. for RGBA -> JPEG)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                # Resize ignoring aspect ratio
                resized_img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                
                # Prepare output filename
                filename = os.path.basename(file_path)
                save_path = os.path.join(output_folder_path, filename)
                
                # Save the image
                resized_img.save(save_path)
                print(f"Processed: {filename}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    print(f"\nProcessing complete. Output folder: {output_folder_path}")

# --- Command-Line Execution ---

def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("file_paths", nargs="+", help="Paths to input files")
    for param in PARAMETERS:
        parser.add_argument(f'--{param["name"]}', type=eval(param["type"]), default=param["default"])
    args = parser.parse_args()
    kwargs = {param["name"]: getattr(args, param["name"]) for param in PARAMETERS}
    process_files(args.file_paths, **kwargs)

if __name__ == "__main__":
    main()