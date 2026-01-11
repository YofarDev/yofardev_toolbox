from PIL import Image
import sys
import os
import datetime

# Increase the decompression bomb limit or disable it
Image.MAX_IMAGE_PIXELS = None  # Disables the limit entirely
# Or set a higher limit: Image.MAX_IMAGE_PIXELS = 300000000

def process_images(image_paths, size=512):
    home_dir = os.path.expanduser("~")
    script_name_slug = NAME.lower().replace(" ", "_")
    output_folder = os.path.join(home_dir, "Downloads", script_name_slug)
    os.makedirs(output_folder, exist_ok=True)
    
    for image_path in image_paths:
        with Image.open(image_path) as img:
            width, height = img.size
            
            if width > height:  # Landscape
                scale = height / size
                new_width = int(width // scale)
                new_height = size
            else:  # Portrait
                scale = width / size
                new_height = int(height // scale)
                new_width = size
            
            img_resized = img.resize((new_width, new_height), Image.LANCZOS)
            original_filename = os.path.basename(image_path)
            new_image_path = os.path.join(output_folder, original_filename)
            
            # Save the downscaled image
            img_resized.save(new_image_path)
            print(f"Processed: {original_filename} -> {new_width}x{new_height}")

DESCRIPTION = "Downscales images to a specific size, maintaining the aspect ratio. The size parameter will be applied to the smallest side of the image."
NAME = "Downscale to Size"
INPUT_TYPES = "Images (*.png *.jpg *.jpeg)"
PARAMETERS = [
    {"name": "size", "type": "int", "default": 512, "description": "The target size for the smallest side of the image. The aspect ratio will be maintained."},
]

def main():
    import argparse
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("image_paths", nargs="+", help="Paths to the images to process.")
    
    for param in PARAMETERS:
        parser.add_argument(f'--{param["name"]}', type=eval(param["type"]), default=param["default"], help=f'Default: {param["default"]}')
    
    args = parser.parse_args()
    
    process_images(args.image_paths, size=args.size)

if __name__ == "__main__":
    main()