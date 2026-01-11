import os
import datetime
import argparse
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import numpy as np

# --- Core Components for UI ---

NAME = "Manga Style Converter"
DESCRIPTION = "Converts images to manga/comic book style with halftone patterns, contrast enhancement, and optional effects."
INPUT_TYPES = "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.webp)"
PARAMETERS = [
    {"name": "contrast", "type": "float", "default": 1.5, "description": "Contrast boost (1.0 = no change, higher = more contrast)."},
    {"name": "brightness", "type": "float", "default": 1.1, "description": "Brightness adjustment (1.0 = no change)."},
    {"name": "sharpness", "type": "float", "default": 2.0, "description": "Sharpness level (1.0 = no change, higher = sharper)."},
    {"name": "screentone", "type": "str", "default": "none", "description": "Halftone/screentone intensity: 'none', 'light', 'medium', 'heavy'."},
    {"name": "edge_enhance", "type": "str", "default": "yes", "description": "Enhance edges for comic book effect: 'yes' or 'no'."},
    {"name": "noise_level", "type": "int", "default": 5, "description": "Film grain/noise amount (0-50, 0 = none)."},
    {"name": "threshold", "type": "int", "default": 0, "description": "Pure black/white threshold (0 = grayscale, 128 = high contrast B&W)."},
]

# --- Script Logic ---

def add_halftone_pattern(img, intensity='light'):
    """Add manga-style halftone/screentone pattern."""
    if intensity == 'none':
        return img
    
    width, height = img.size
    pattern_size = {'light': 8, 'medium': 6, 'heavy': 4}[intensity]
    
    # Create halftone pattern
    img_array = np.array(img)
    result = img_array.copy()
    
    for y in range(0, height, pattern_size):
        for x in range(0, width, pattern_size):
            block = img_array[y:min(y+pattern_size, height), x:min(x+pattern_size, width)]
            avg_value = np.mean(block)
            
            # Add dot pattern in darker areas
            if avg_value < 180:
                dot_threshold = avg_value / 255.0
                dot_size = max(1, int(pattern_size * dot_threshold))
                
                cy, cx = pattern_size // 2, pattern_size // 2
                for dy in range(pattern_size):
                    for dx in range(pattern_size):
                        if y + dy < height and x + dx < width:
                            dist = ((dy - cy) ** 2 + (dx - cx) ** 2) ** 0.5
                            if dist < dot_size:
                                result[y + dy, x + dx] = min(result[y + dy, x + dx], int(avg_value * 0.8))
    
    return Image.fromarray(result)


def add_film_grain(img, amount=10):
    """Add film grain/noise effect."""
    if amount == 0:
        return img
    
    img_array = np.array(img).astype(float)
    noise = np.random.normal(0, amount, img_array.shape)
    noisy = img_array + noise
    noisy = np.clip(noisy, 0, 255).astype(np.uint8)
    
    return Image.fromarray(noisy)


def process_files(file_paths, contrast, brightness, sharpness, screentone, edge_enhance, noise_level, threshold):
    """Main processing logic for manga style conversion."""
    # Handle empty string defaults
    if not screentone or screentone.strip() == '':
        screentone = 'light'
    if not edge_enhance or edge_enhance.strip() == '':
        edge_enhance = 'yes'
    
    home_dir = os.path.expanduser("~")
    script_name_slug = NAME.lower().replace(" ", "_")
    
    # Create unique output directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder_name = f"{timestamp}_manga_output"
    output_folder_path = os.path.join(home_dir, "Downloads", script_name_slug, output_folder_name)
    os.makedirs(output_folder_path, exist_ok=True)
    
    print(f"Processing {len(file_paths)} image(s) to manga style...")
    print(f"Output directory: {output_folder_path}")
    print(f"Settings: contrast={contrast}, brightness={brightness}, sharpness={sharpness}")
    print(f"          screentone={screentone}, edge_enhance={edge_enhance}, noise={noise_level}, threshold={threshold}")
    print()

    successful = 0
    failed = 0

    for file_path in file_paths:
        try:
            print(f"Processing: {os.path.basename(file_path)}")
            
            # Open and convert to grayscale
            img = Image.open(file_path)
            
            # Convert to RGB first (handles RGBA, palette, etc.)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Convert to grayscale
            img = ImageOps.grayscale(img)
            
            # Enhance contrast
            if contrast != 1.0:
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(contrast)
            
            # Enhance brightness
            if brightness != 1.0:
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(brightness)
            
            # Enhance sharpness
            if sharpness != 1.0:
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(sharpness)
            
            # Edge enhancement for comic book effect
            if edge_enhance.lower() == 'yes':
                img = img.filter(ImageFilter.EDGE_ENHANCE)
            
            # Apply threshold for pure B&W if requested
            if threshold > 0:
                img = img.point(lambda x: 255 if x > threshold else 0)
            
            # Add halftone pattern
            if screentone != 'none':
                img = add_halftone_pattern(img, screentone)
            
            # Add film grain
            if noise_level > 0:
                img = add_film_grain(img, noise_level)
            
            # Save output
            filename = os.path.basename(file_path)
            name_without_ext = os.path.splitext(filename)[0]
            output_path = os.path.join(output_folder_path, f"{name_without_ext}_manga.png")
            
            img.save(output_path, 'PNG', quality=95)
            print(f"  ✓ Saved: {os.path.basename(output_path)}")
            successful += 1
            
        except Exception as e:
            print(f"  ✗ Error processing {os.path.basename(file_path)}: {str(e)}")
            failed += 1
    
    print()
    print("=" * 50)
    print(f"Processing complete!")
    print(f"Successful: {successful} | Failed: {failed}")
    print(f"Output location: {output_folder_path}")
    print("=" * 50)


# --- Command-Line Execution ---

def main():
    """Parses command-line arguments and runs the script."""
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    
    # Input files
    parser.add_argument("file_paths", nargs="+", help="Paths to the input images to process.")
    
    # Add arguments for each parameter
    for param in PARAMETERS:
        parser.add_argument(
            f'--{param["name"]}',
            type=eval(param["type"]),
            default=param["default"],
            help=param.get("description", f'Default: {param["default"]}')
        )
    
    args = parser.parse_args()
    
    # Convert to kwargs
    kwargs = {param["name"]: getattr(args, param["name"]) for param in PARAMETERS}
    
    process_files(args.file_paths, **kwargs)


if __name__ == "__main__":
    main()
