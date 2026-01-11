#!/usr/bin/env python3
import argparse
import os
import sys
import datetime
from pathlib import Path
import cv2

def process_videos(video_paths, interval=0, start_time=0):
    home_dir = os.path.expanduser("~")
    script_name_slug = NAME.lower().replace(" ", "_")
    output_folder = os.path.join(home_dir, "Downloads", script_name_slug)
    os.makedirs(output_folder, exist_ok=True)

    for video_path in video_paths:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        video_name = Path(video_path).stem
        video_output_folder = os.path.join(output_folder, f"{video_name}_{timestamp}")
        os.makedirs(video_output_folder, exist_ok=True)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video file: {video_path}")
            continue
        fps = cap.get(cv2.CAP_PROP_FPS)

        # Seek to start time (in milliseconds)
        if start_time > 0:
            cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)
            print(f"Starting extraction from {start_time} seconds")
        
        if interval == 0: # extract all frames
            frame_interval = 1
        else:
            frame_interval = int(fps * interval)
        
        frame_count = 0
        saved_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                output_path = os.path.join(
                    video_output_folder, f"{video_name}_{saved_count:06d}.png"
                )
                cv2.imwrite(output_path, frame)
                saved_count += 1
            
            frame_count += 1
        
        cap.release()
        print(f"\nExtraction complete! {saved_count} frames saved to '{video_output_folder}'")

DESCRIPTION = "Extracts frames from video files. Set interval to 0 to extract all frames, otherwise specify an interval in seconds."
NAME = "Video to Images"
INPUT_TYPES = "Videos (*.mp4 *.mov *.avi *.webm *.mkv)"
PARAMETERS = [
    {"name": "interval", "type": "float", "default": 0, "description": "The interval in seconds between frame extractions. Set to 0 to extract all frames."},
    {"name": "start_time", "type": "float", "default": 0, "description": "The timestamp (in seconds) from where to start extracting frames. Default is 0 (start of video)."},
]

def main():
    import argparse
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("video_paths", nargs="+", help="Paths to the videos to process.")
    
    for param in PARAMETERS:
        parser.add_argument(f'--{param["name"]}', type=eval(param["type"]), default=param["default"], help=f'Default: {param["default"]}')
    
    args = parser.parse_args()

    process_videos(args.video_paths, interval=args.interval, start_time=args.start_time)

if __name__ == "__main__":
    main()