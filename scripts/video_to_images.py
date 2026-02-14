#!/usr/bin/env python3
import argparse
import os
import sys
import datetime
import time
import subprocess
import shutil
from pathlib import Path

def find_ffmpeg():
    """Find ffmpeg executable, checking common Homebrew paths."""
    # First, try common Homebrew paths directly (more reliable)
    common_paths = [
        '/opt/homebrew/bin/ffmpeg',  # Apple Silicon
        '/usr/local/bin/ffmpeg',      # Intel Mac
        '/opt/local/bin/ffmpeg',      # MacPorts
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    # Fallback: Check if ffmpeg is in PATH
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        return ffmpeg_path
    
    return None

def process_videos(video_paths, interval=0, start_time=0, lossless=False):
    """Extract frames from videos using ffmpeg for maximum performance.

    Args:
        video_paths: List of video file paths
        interval: Seconds between frame extractions (0 = all frames)
        start_time: Start extraction from this timestamp (seconds)
        lossless: If True, use PNG format (slower, lossless). If False, use JPEG (faster, high quality).
    """
    # Find ffmpeg executable
    ffmpeg_path = find_ffmpeg()
    if not ffmpeg_path:
        print("Error: ffmpeg is not installed or not in PATH")
        print("Please install ffmpeg:")
        print("  macOS: brew install ffmpeg")
        print("  Ubuntu/Debian: sudo apt install ffmpeg")
        print("  Windows: Download from https://ffmpeg.org/download.html")
        print("\nIf you installed via Homebrew, add this to ~/.zshrc:")
        print("  export PATH=\"/opt/homebrew/bin:$PATH\"")
        print("Then run: source ~/.zshrc")
        sys.exit(1)
    
    print(f"Using ffmpeg: {ffmpeg_path}")

    home_dir = os.path.expanduser("~")
    script_name_slug = NAME.lower().replace(" ", "_")
    output_folder = os.path.join(home_dir, "Downloads", script_name_slug)
    os.makedirs(output_folder, exist_ok=True)

    # Determine output format and extension
    if lossless:
        file_extension = "png"
        codec_args = []  # PNG is lossless by default
        print("Using lossless PNG format (slower)")
    else:
        file_extension = "jpg"
        codec_args = ["-q:v", "1"]  # Highest quality JPEG (1-31 scale, 1 is best)
        print("Using JPEG format (fastest, highest quality)")

    for video_path in video_paths:
        if not os.path.exists(video_path):
            print(f"Error: Video file not found: {video_path}")
            continue

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        video_name = Path(video_path).stem
        video_output_folder = os.path.join(output_folder, f"{video_name}_{timestamp}")
        os.makedirs(video_output_folder, exist_ok=True)

        # Get video info first (FPS)
        ffprobe_path = ffmpeg_path.replace('ffmpeg', 'ffprobe')
        probe_cmd = [
            ffprobe_path,
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=r_frame_rate',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]
        
        try:
            result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
            fps_str = result.stdout.strip()
            # Parse fraction (e.g., "30000/1001" or "30/1")
            if '/' in fps_str:
                num, den = fps_str.split('/')
                fps = float(num) / float(den)
            else:
                fps = float(fps_str)
            print(f"Video FPS: {fps:.2f}")
        except subprocess.CalledProcessError:
            print(f"Warning: Could not determine FPS, assuming 30")
            fps = 30.0

        # Build ffmpeg command
        output_pattern = os.path.join(video_output_folder, f"{video_name}_%06d.{file_extension}")
        
        # Start timing
        start_time_total = time.time()
        
        # Build filter for frame selection
        if interval == 0:
            # Extract all frames
            filter_select = "select='1'"
        else:
            # Extract every N frames based on interval
            # Calculate how many frames to skip
            frame_interval = int(fps * interval)
            if frame_interval <= 1:
                filter_select = "select='1'"
            else:
                # Select every Nth frame: not(mod(n, N))
                filter_select = f"select='not(mod(n\\,{frame_interval}))'"
        
        # Build complete ffmpeg command
        ffmpeg_cmd = [ffmpeg_path]
        
        # Start time (seeking)
        if start_time > 0:
            ffmpeg_cmd.extend(['-ss', str(start_time)])
        
        # Input file
        ffmpeg_cmd.extend(['-i', video_path])
        
        # Video filters
        ffmpeg_cmd.extend(['-vf', filter_select])
        
        # Output format and quality
        ffmpeg_cmd.extend(codec_args)
        
        # Force frame output (don't skip duplicates)
        ffmpeg_cmd.extend(['-vsync', '0'])
        
        # Overwrite output files
        ffmpeg_cmd.extend(['-y'])
        
        # Output pattern
        ffmpeg_cmd.append(output_pattern)
        
        print(f"\nProcessing: {video_name}")
        print(f"Command: {' '.join(ffmpeg_cmd)}")
        print(f"Extracting frames...")
        
        try:
            # Run ffmpeg
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Count extracted frames
            saved_count = len(list(Path(video_output_folder).glob(f"*.{file_extension}")))
            
            # Calculate timing stats
            elapsed = time.time() - start_time_total
            extraction_fps = saved_count / elapsed if elapsed > 0 else 0
            time_per_frame = elapsed / saved_count if saved_count > 0 else 0
            
            # Output stats
            print("\n" + "=" * 60)
            print("EXTRACTION COMPLETE")
            print("=" * 60)
            print(f"Total frames extracted:  {saved_count}")
            print(f"Total time taken:        {elapsed:.4f} seconds")
            print(f"Time per frame:          {time_per_frame:.4f} seconds")
            print(f"Processing speed:        {extraction_fps:.2f} FPS")
            print(f"Output format:           {'PNG (lossless)' if lossless else 'JPEG (quality 1/highest)'}")
            print(f"Frame interval:          {interval}s (0 = all frames)")
            if start_time > 0:
                print(f"Start time:              {start_time}s")
            print("=" * 60)
            print(f"\nFrames saved to: '{video_output_folder}'")
            
        except subprocess.CalledProcessError as e:
            print(f"\nError running ffmpeg:")
            print(f"Command: {' '.join(ffmpeg_cmd)}")
            print(f"Return code: {e.returncode}")
            print(f"stderr: {e.stderr}")
            continue

DESCRIPTION = "Extracts frames from video files using ffmpeg. Set interval to 0 to extract all frames, otherwise specify an interval in seconds."
NAME = "Video to Images"
INPUT_TYPES = "Videos (*.mp4 *.mov *.avi *.webm *.mkv)"
PARAMETERS = [
    {"name": "interval", "type": "float", "default": 0, "description": "The interval in seconds between frame extractions. Set to 0 to extract all frames."},
    {"name": "start_time", "type": "float", "default": 0, "description": "The timestamp (in seconds) from where to start extracting frames. Default is 0 (start of video)."},
    {"name": "lossless", "type": "bool", "default": False, "label": "Enable lossless (Slow)", "description": "Use PNG format for lossless quality. Slower than JPEG. Default: False (JPEG, highest quality & fast)."},
]

def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("video_paths", nargs="+", help="Paths to the videos to process.")

    for param in PARAMETERS:
        parser.add_argument(
            f'--{param["name"]}',
            type=eval(param["type"]),
            default=param["default"],
            help=f'{param.get("description", "")} Default: {param["default"]}'
        )

    args = parser.parse_args()

    process_videos(
        args.video_paths,
        interval=args.interval,
        start_time=args.start_time,
        lossless=args.lossless
    )

if __name__ == "__main__":
    main()