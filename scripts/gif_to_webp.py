import os
import sys
import datetime
from PIL import Image

def process_gifs(gif_paths, duration=None, loop=0):
    home_dir = os.path.expanduser("~")
    script_name_slug = NAME.lower().replace(" ", "_")
    output_folder = os.path.join(home_dir, "Downloads", script_name_slug)
    os.makedirs(output_folder, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    for gif_path in gif_paths:
        if not os.path.exists(gif_path):
            print(f"Error: GIF file '{gif_path}' not found.")
            continue

        try:
            img = Image.open(gif_path)
        except Exception as e:
            print(f"Error: Could not open GIF file {gif_path}. Error: {e}")
            continue

        frames = []
        try:
            while True:
                frames.append(img.copy())
                img.seek(img.tell() + 1)
        except EOFError:
            pass

        if not frames:
            print("Error: No frames found in the GIF to convert.")
            continue

        if duration is None:
            try:
                duration = img.info['duration']
            except KeyError:
                duration = 100

        filename, _ = os.path.splitext(os.path.basename(gif_path))
        output_webp_path = os.path.join(output_folder, f"{filename}_{timestamp}.webp")

        frames[0].save(
            output_webp_path,
            format='WEBP',
            append_images=frames[1:],
            save_all=True,
            duration=duration,
            loop=loop
        )
        print(f"Animated WebP successfully created at {output_webp_path}.")

DESCRIPTION = "Converts GIF files to animated WebP files."
NAME = "GIF to WebP"
INPUT_TYPES = "GIFs (*.gif)"
PARAMETERS = [
    {"name": "duration", "type": "int", "default": 100, "description": "The display duration for each frame in milliseconds."},
    {"name": "loop", "type": "int", "default": 0, "description": "The number of times the animation should loop. 0 means infinite."},
]

def main():
    import argparse
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("gif_paths", nargs="+", help="Paths to the GIF files to process.")
    for param in PARAMETERS:
        parser.add_argument(f'--{param["name"]}', type=eval(param["type"]), default=param["default"], help=f'Default: {param["default"]}')
    
    args = parser.parse_args()
    
    process_gifs(args.gif_paths, duration=args.duration, loop=args.loop)

if __name__ == "__main__":
    main()