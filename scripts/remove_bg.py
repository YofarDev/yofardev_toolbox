import os
import datetime
import argparse
from pathlib import Path
from PIL import Image
from rembg import remove

# --- Core Components for UI ---

NAME = "Background Remover"
DESCRIPTION = "Automatically removes backgrounds from images using AI (rembg/U^2-Net)."
INPUT_TYPES = "Images (*.png *.jpg *.jpeg *.webp *.bmp)"

PARAMETERS = [
    {
        "name": "alpha_matting", 
        "type": "str", 
        "default": "False", 
        "description": "Use alpha matting? (True/False). Better for hair/fur but slower."
    },
    {
        "name": "post_process_mask", 
        "type": "str", 
        "default": "False", 
        "description": "Post-process the mask to smooth edges? (True/False)."
    }
]

# --- Script Logic ---

def get_image_files(paths):
    """
    Recursively finds image files if a folder is passed, 
    or returns the path if it's a file.
    """
    valid_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff'}
    images = []

    for path_str in paths:
        path = Path(path_str)
        if path.is_file():
            if path.suffix.lower() in valid_extensions:
                images.append(path)
        elif path.is_dir():
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.suffix.lower() in valid_extensions:
                        images.append(file_path)
    return images

def str_to_bool(v):
    """Helper to convert string parameters to boolean."""
    return str(v).lower() in ("yes", "true", "t", "1")

def process_files(file_paths, alpha_matting, post_process_mask):
    """
    Main processing logic.
    """
    # Convert string args to booleans
    use_alpha = str_to_bool(alpha_matting)
    use_post = str_to_bool(post_process_mask)

    home_dir = os.path.expanduser("~")
    script_name_slug = NAME.lower().replace(" ", "_")
    
    # 1. Create a unique output directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    output_folder_name = f"{timestamp}_output"
    output_folder_path = os.path.join(home_dir, "Downloads", script_name_slug, output_folder_name)
    os.makedirs(output_folder_path, exist_ok=True)
    
    # Collect actual image files from inputs (handles folders)
    target_images = get_image_files(file_paths)

    print(f"Found {len(target_images)} image(s) to process.")
    print(f"Alpha Matting: {use_alpha}")
    print(f"Post Process Mask: {use_post}")
    print(f"Output location: {output_folder_path}")

    success_count = 0

    for img_path in target_images:
        try:
            filename = img_path.name
            print(f"-> Processing: {filename}")
            
            # Open the image
            with open(img_path, 'rb') as i:
                input_data = i.read()
                
            # Process with rembg
            # We treat the input as binary data and receive binary data back
            output_data = remove(
                input_data, 
                alpha_matting=use_alpha,
                post_process_mask=use_post
            )

            # Determine output filename (Ensure it is PNG for transparency)
            name_without_ext = img_path.stem
            output_filename = f"{name_without_ext}_nobg.png"
            output_path = os.path.join(output_folder_path, output_filename)

            # Save the file
            with open(output_path, 'wb') as o:
                o.write(output_data)
            
            success_count += 1

        except Exception as e:
            print(f"!! Error processing {img_path.name}: {e}")

    print("-" * 30)
    print(f"Processing complete. {success_count}/{len(target_images)} images saved.")
    print(f"Folder: {output_folder_path}")


# --- Command-Line Execution ---

def main():
    """
    Parses command-line arguments and runs the script.
    """
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    
    # Default argument for input files
    parser.add_argument("file_paths", nargs="+", help="Paths to the input files to process.")
    
    # Add arguments for each parameter defined in PARAMETERS
    for param in PARAMETERS:
        parser.add_argument(
            f'--{param["name"]}',
            type=eval(param["type"]), # Use eval to dynamically set the type
            default=param["default"],
            help=f'Default: {param["default"]}'
        )
    
    args = parser.parse_args()
    
    # Convert argument names to a dictionary of keyword arguments
    kwargs = {param["name"]: getattr(args, param["name"]) for param in PARAMETERS}
    
    process_files(args.file_paths, **kwargs)

if __name__ == "__main__":
    main()