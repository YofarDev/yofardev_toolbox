from PIL import Image, ImageDraw
import os
import sys
import datetime

def process_images(image_paths, radius=100):
    home_dir = os.path.expanduser("~")
    script_name_slug = NAME.lower().replace(" ", "_")
    output_folder = os.path.join(home_dir, "Downloads", script_name_slug)
    os.makedirs(output_folder, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    for image_path in image_paths:
        img = Image.open(image_path).convert("RGBA")

        round_rectangle = Image.new('L', img.size, 0)
        draw = ImageDraw.Draw(round_rectangle)
        draw.rounded_rectangle([0, 0, *img.size], radius=radius, fill=255)

        img.putalpha(round_rectangle)

        filename, _ = os.path.splitext(os.path.basename(image_path))
        output_path = os.path.join(output_folder, f"{filename}_{timestamp}_rounded.png")
        img.save(output_path)

DESCRIPTION = "Adds rounded corners to images."
NAME = "Rounded Corners"
INPUT_TYPES = "Images (*.png *.jpg *.jpeg)"
PARAMETERS = [
    {"name": "radius", "type": "int", "default": 100, "description": "The radius of the rounded corners in pixels."},
]

def main():
    import argparse
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("image_paths", nargs="+", help="Paths to the images to process.")
    for param in PARAMETERS:
        parser.add_argument(f'--{param["name"]}', type=eval(param["type"]), default=param["default"], help=f'Default: {param["default"]}')
    
    args = parser.parse_args()
    
    process_images(args.image_paths, radius=args.radius)

if __name__ == "__main__":
    main()