import os
import datetime
import argparse
from pathlib import Path
from PIL import Image

# --- Core Components for UI ---

NAME = "Images to Boomerang WebP"
DESCRIPTION = "Converts a sequence of images into a looping animated WebP by reversing the frames at the end."
INPUT_TYPES = "Images (*.png *.jpg *.jpeg *.webp *.bmp)"

PARAMETERS = [
    {
        "name": "duration",
        "type": "int",
        "default": 100,
        "description": "Duration for each frame in milliseconds"
    },
    {
        "name": "loop",
        "type": "int",
        "default": 0,
        "description": "Number of times to loop (0 for infinite)"
    },
    {
        "name": "output_filename",
        "type": "str",
        "default": "boomerang_animation.webp",
        "description": "Name of the resulting webp file"
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
    if not file_paths:
        print("No files provided.")
        return

    # 1. Create output directory
    home_dir = os.path.expanduser("~")
    script_name_slug = NAME.lower().replace(" ", "_")
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    output_folder_path = os.path.join(home_dir, "Downloads", script_name_slug, f"{timestamp}_output")
    os.makedirs(output_folder_path, exist_ok=True)

    # 2. Get parameters
    duration = kwargs.get("duration", 100)
    loop = kwargs.get("loop", 0)
    output_filename = kwargs.get("output_filename", "boomerang_animation.webp")
    if not output_filename.endswith(".webp"):
        output_filename += ".webp"

    # 3. Sort and Load Images
    # Ensure files are sorted alphabetically
    sorted_paths = sorted(file_paths)
    frames = []
    
    print(f"Loading {len(sorted_paths)} images...")
    for path in sorted_paths:
        try:
            img = Image.open(path).convert("RGBA")
            frames.append(img)
        except Exception as e:
            print(f"Skipping {path}: {e}")

    if not frames:
        print("No valid images could be loaded.")
        return

    # 4. Create Boomerang Sequence
    # If frames are 1, 2, 3, 4, 5
    # Boomerang is 1, 2, 3, 4, 5, 4, 3, 2
    # We exclude the last and first frame of the reversed list to prevent double-pauses
    if len(frames) > 2:
        reversed_frames = frames[-2:0:-1]
        boomerang_frames = frames + reversed_frames
    elif len(frames) == 2:
        boomerang_frames = frames
    else:
        boomerang_frames = frames

    # 5. Save Animated WebP
    output_path = os.path.join(output_folder_path, output_filename)
    
    boomerang_frames[0].save(
        output_path,
        save_all=True,
        append_images=boomerang_frames[1:],
        duration=duration,
        loop=loop,
        format="WEBP",
        method=6, # Highest quality compression
        lossless=False
    )

    print(f"Processing complete. Output: {output_path}")

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