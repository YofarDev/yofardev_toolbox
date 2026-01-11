import os
import sys
import datetime
from PIL import Image

def create_gif(image_paths, duration=100):
    if not image_paths:
        print("Error: No image files provided.")
        return

    frames = []
    for image_file in image_paths:
        try:
            frames.append(Image.open(image_file))
        except Exception as e:
            print(f"Warning: Could not open image {image_file}. Skipping. Error: {e}")

    if not frames:
        print("Error: No valid frames were loaded to create the GIF.")
        return

    home_dir = os.path.expanduser("~")
    script_name_slug = NAME.lower().replace(" ", "_")
    output_folder = os.path.join(home_dir, "Downloads", script_name_slug)
    os.makedirs(output_folder, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    output_gif_path = os.path.join(output_folder, f"output_{timestamp}.gif")
    
    frames[0].save(
        output_gif_path,
        format='GIF',
        append_images=frames[1:],
        save_all=True,
        duration=duration,
        loop=0  # 0 means loop forever
    )
    print(f"GIF successfully created at {output_gif_path} with {len(frames)} frames.")

DESCRIPTION = "Creates a GIF from a sequence of images."
NAME = "Images to GIF"
INPUT_TYPES = "Images (*.png *.jpg *.jpeg)"
PARAMETERS = [
    {"name": "duration", "type": "int", "default": 100, "description": "The display duration for each frame in milliseconds."},
]

def main():
    import argparse
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("image_paths", nargs="+", help="Paths to the images to process.")
    for param in PARAMETERS:
        parser.add_argument(f'--{param["name"]}', type=eval(param["type"]), default=param["default"], help=f'Default: {param["default"]}')
    
    args = parser.parse_args()
    
    create_gif(args.image_paths, duration=args.duration)

if __name__ == "__main__":
    main()