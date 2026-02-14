import os
import datetime
import argparse
import subprocess

# --- Core Components for UI ---

NAME = "MP4 to MP3 Converter"
DESCRIPTION = "Converts MP4 video files to MP3 audio files using ffmpeg."
INPUT_TYPES = "Video files (*.mp4)"
PARAMETERS = [
    {"name": "bitrate", "type": "str", "default": "192k", "description": "Audio bitrate (e.g., 128k, 192k, 320k)."},
    {"name": "samplerate", "type": "int", "default": 44100, "description": "Audio sample rate in Hz (e.g., 44100, 48000)."},
    {"name": "channels", "type": "int", "default": 2, "description": "Number of audio channels (1 for mono, 2 for stereo)."},
]

# --- Script Logic ---

def process_files(file_paths, bitrate, samplerate, channels):
    """
    Converts MP4 files to MP3 format using ffmpeg.
    """
    home_dir = os.path.expanduser("~")
    script_name_slug = NAME.lower().replace(" ", "_")
    
    # Ensure bitrate has a default value if empty
    if not bitrate or bitrate.strip() == "":
        bitrate = "192k"
    
    # 1. Create a unique output directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    output_folder_name = f"{timestamp}_output"
    output_folder_path = os.path.join(home_dir, "Downloads", script_name_slug, output_folder_name)
    os.makedirs(output_folder_path, exist_ok=True)
    
    print(f"Processing {len(file_paths)} file(s)...")
    print(f"Bitrate: {bitrate}")
    print(f"Sample Rate: {samplerate} Hz")
    print(f"Channels: {channels}")
    print(f"Output will be saved to: {output_folder_path}")

    for file_path in file_paths:
        # 2. Process each file
        print(f"-> Converting {file_path}")
        
        # Get the base filename without extension
        filename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(filename)[0]
        output_path = os.path.join(output_folder_path, f"{name_without_ext}.mp3")
        
        # 3. Run ffmpeg command
        try:
            ffmpeg_command = [
                "/opt/homebrew/bin/ffmpeg",
                "-i", file_path,           # Input file
                "-vn",                     # No video
                "-acodec", "libmp3lame",   # Use MP3 codec
                "-b:a", bitrate,           # Audio bitrate
                "-ar", str(samplerate),    # Audio sample rate
                "-ac", str(channels),      # Audio channels
                "-y",                      # Overwrite output files without asking
                output_path                # Output file
            ]
            
            subprocess.run(ffmpeg_command, check=True, capture_output=True)
            print(f"   ✓ Saved to: {output_path}")
            
        except subprocess.CalledProcessError as e:
            print(f"   ✗ Error converting {filename}: {e.stderr.decode()}")
        except FileNotFoundError:
            print("   ✗ Error: ffmpeg not found at /opt/homebrew/bin/ffmpeg")
            print("      Please install ffmpeg: brew install ffmpeg")
            break

    print("Processing complete.")


# --- Command-Line Execution ---

def main():
    """
    Parses command-line arguments and runs the script.
    """
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    
    # Default argument for input files
    parser.add_argument("file_paths", nargs="+", help="Paths to the input MP4 files to process.")
    
    # Add arguments for each parameter defined in PARAMETERS
    for param in PARAMETERS:
        parser.add_argument(
            f'--{param["name"]}',
            type=eval(param["type"]),
            default=param["default"],
            help=f'{param.get("description", "")} Default: {param["default"]}'
        )
    
    args = parser.parse_args()
    
    # Convert argument names to a dictionary of keyword arguments
    kwargs = {param["name"]: getattr(args, param["name"]) for param in PARAMETERS}
    
    process_files(args.file_paths, **kwargs)

if __name__ == "__main__":
    main()