from PIL import Image
import os
import sys
import datetime

def process_images(image_paths, scale=2):
    home_dir = os.path.expanduser("~")
    script_name_slug = NAME.lower().replace(" ", "_")
    output_folder = os.path.join(home_dir, "Downloads", script_name_slug)
    os.makedirs(output_folder, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    for image_path in image_paths:
        filename, extension = os.path.splitext(os.path.basename(image_path))
        new_filename = f"{filename}_{timestamp}_d{scale}{extension}"
        new_image_path = os.path.join(output_folder, new_filename)

        with Image.open(image_path) as img:
            width, height = img.size
            img_resized = img.resize((width // scale, height // scale))
            img_resized.save(new_image_path)

DESCRIPTION = "Downscales images by a factor of 2 (half the size)."
NAME = "Downscale by Half"
INPUT_TYPES = "Images (*.png *.jpg *.jpeg)"
PARAMETERS = [
    {"name": "scale", "type": "int", "default": 2, "description": "The factor by which to downscale the image. For example, a scale of 2 will make the image half the size."},
]

def main():
    import argparse
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("image_paths", nargs="+", help="Paths to the images to process.")
    for param in PARAMETERS:
        parser.add_argument(f'--{param["name"]}', type=eval(param["type"]), default=param["default"], help=f'Default: {param["default"]}')
    
    args = parser.parse_args()
    
    process_images(args.image_paths, scale=args.scale)

if __name__ == "__main__":
    main()