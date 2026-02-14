import os
import datetime
import argparse
from pathlib import Path
from PIL import Image
import cv2

NAME = "Video to Animated WebP"
DESCRIPTION = "Converts video files to animated WebP format with best quality settings"
INPUT_TYPES = "Video Files (*.mp4 *.avi *.mov *.mkv *.webm *.flv *.wmv)"

PARAMETERS = [
    {
        "name": "quality",
        "type": "int",
        "default": 100,
        "description": "WebP quality (0-100, higher is better quality)"
    },
    {
        "name": "fps",
        "type": "int",
        "default": 0,
        "description": "Output FPS (0 = use original video FPS)"
    },
    {
        "name": "max_width",
        "type": "int",
        "default": 0,
        "description": "Maximum width in pixels (0 = no resize)"
    }
]

def process_files(file_paths, **kwargs):
    quality = kwargs.get("quality", 100)
    fps = kwargs.get("fps", 0)
    max_width = kwargs.get("max_width", 0)
    
    home_dir = os.path.expanduser("~")
    script_name_slug = NAME.lower().replace(" ", "_")
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    output_folder_path = os.path.join(home_dir, "Downloads", script_name_slug, f"{timestamp}_output")
    os.makedirs(output_folder_path, exist_ok=True)
    
    for input_path in file_paths:
        if not os.path.exists(input_path):
            print(f"Error: File not found: {input_path}")
            continue
            
        print(f"Processing: {input_path}")
        convert_video_to_webp(input_path, output_folder_path, quality, fps, max_width)
    
    print(f"\nProcessing complete. Output: {output_folder_path}")

def convert_video_to_webp(input_path, output_folder_path, quality, fps, max_width):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file {input_path}")
        return
    
    orig_fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    output_fps = orig_fps if fps == 0 else fps
    frame_interval = max(1, round(orig_fps / output_fps))
    
    frames = []
    frame_count = 0
    saved_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % frame_interval == 0:
            if max_width > 0 and width > max_width:
                ratio = max_width / width
                new_width = max_width
                new_height = int(height * ratio)
                frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            frames.append(img)
            saved_count += 1
        
        frame_count += 1
    
    cap.release()
    
    if not frames:
        print(f"Error: No frames extracted from {input_path}")
        return
    
    output_filename = os.path.splitext(os.path.basename(input_path))[0] + ".webp"
    output_path = os.path.join(output_folder_path, output_filename)
    
    print(f"Saving {len(frames)} frames to {output_path}...")
    
    duration = int(1000 / output_fps)
    
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0,
        quality=quality,
        method=6
    )
    
    print(f"Saved: {output_path}")

def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("file_paths", nargs="+", help="Paths to input video files")
    for param in PARAMETERS:
        parser.add_argument(f'--{param["name"]}', type=eval(param["type"]), default=param["default"])
    args = parser.parse_args()
    kwargs = {param["name"]: getattr(args, param["name"]) for param in PARAMETERS}
    process_files(args.file_paths, **kwargs)

if __name__ == "__main__":
    main()
