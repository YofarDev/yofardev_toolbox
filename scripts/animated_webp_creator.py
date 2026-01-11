import os
import datetime
import argparse
from PIL import Image

# --- Core Components for UI ---

NAME = "Animated WebP Creator"
DESCRIPTION = "Creates high-quality animated WebP from a batch of images with customizable settings."
INPUT_TYPES = "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.webp)"
PARAMETERS = [
    {"name": "duration", "type": "int", "default": 100, "description": "Duration of each frame in milliseconds."},
    {"name": "loop", "type": "int", "default": 0, "description": "Number of loops (0 = infinite loop)."},
    {"name": "quality", "type": "int", "default": 90, "description": "Output quality (0-100, higher is better)."},
    {"name": "method", "type": "int", "default": 6, "description": "Compression method (0-6, higher is slower but better quality)."},
    {"name": "lossless", "type": "int", "default": 0, "description": "Use lossless compression (0 = lossy, 1 = lossless)."},
]

# --- Script Logic ---

def process_files(file_paths, duration, loop, quality, method, lossless):
    """
    Creates an animated WebP from a batch of images.
    """
    home_dir = os.path.expanduser("~")
    script_name_slug = NAME.lower().replace(" ", "_")
    
    # 1. Create a unique output directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    output_folder_name = f"{timestamp}_output"
    output_folder_path = os.path.join(home_dir, "Downloads", script_name_slug, output_folder_name)
    os.makedirs(output_folder_path, exist_ok=True)
    
    # 2. Expand directories to get actual image files
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp'}
    actual_files = []
    
    for path in file_paths:
        if os.path.isdir(path):
            # If it's a directory, get all image files from it
            print(f"Scanning directory: {path}")
            for root, dirs, files in os.walk(path):
                for file in files:
                    if os.path.splitext(file)[1].lower() in image_extensions:
                        actual_files.append(os.path.join(root, file))
        elif os.path.isfile(path):
            # If it's a file, add it directly
            actual_files.append(path)
    
    # Sort file paths to ensure consistent order
    file_paths = sorted(actual_files)
    
    print(f"Processing {len(file_paths)} image(s)...")
    print(f"Duration per frame: {duration}ms")
    print(f"Loop count: {'infinite' if loop == 0 else loop}")
    print(f"Quality: {quality}")
    print(f"Method: {method}")
    print(f"Lossless: {'Yes' if lossless == 1 else 'No'}")
    print(f"Output will be saved to: {output_folder_path}")
    
    # 3. Load all images
    images = []
    print("\nLoading images...")
    for file_path in file_paths:
        try:
            img = Image.open(file_path)
            # Convert to RGBA for consistent handling
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            images.append(img)
            print(f"✓ Loaded: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"✗ Failed to load {file_path}: {e}")
    
    if not images:
        print("\nError: No valid images to process.")
        return
    
    # 4. Create animated WebP
    output_path = os.path.join(output_folder_path, "output.webp")
    
    print(f"\nCreating animated WebP with {len(images)} frames...")
    
    try:
        # Save as animated WebP
        images[0].save(
            output_path,
            format='WEBP',
            save_all=True,
            append_images=images[1:],
            duration=duration,
            loop=loop,
            quality=quality,
            method=method,
            lossless=bool(lossless)
        )
        
        # Get file size
        file_size = os.path.getsize(output_path)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"\n✓ Successfully created animated WebP!")
        print(f"  Output: {output_path}")
        print(f"  File size: {file_size_mb:.2f} MB")
        print(f"  Frames: {len(images)}")
        print(f"  Total duration: {len(images) * duration / 1000:.2f} seconds")
        
    except Exception as e:
        print(f"\n✗ Error creating animated WebP: {e}")
    finally:
        # Close all images
        for img in images:
            img.close()

    print("\nProcessing complete.")


# --- Command-Line Execution ---

def main():
    """
    Parses command-line arguments and runs the script.
    """
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    
    # Default argument for input files
    parser.add_argument("file_paths", nargs="+", help="Paths to the input image files to process.")
    
    # Add arguments for each parameter defined in PARAMETERS
    for param in PARAMETERS:
        parser.add_argument(
            f'--{param["name"]}',
            type=eval(param["type"]),
            default=param["default"],
            help=f'{param.get("description", "")} (Default: {param["default"]})'
        )
    
    args = parser.parse_args()
    
    # Convert argument names to a dictionary of keyword arguments
    kwargs = {param["name"]: getattr(args, param["name"]) for param in PARAMETERS}
    
    process_files(args.file_paths, **kwargs)

if __name__ == "__main__":
    main()
