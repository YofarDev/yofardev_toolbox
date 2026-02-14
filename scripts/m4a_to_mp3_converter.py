import os
import sys
import datetime
import argparse
import subprocess
import shutil
from pathlib import Path

# --- Core Components for UI ---

NAME = "M4A to MP3 Converter"
DESCRIPTION = "Converts M4A audio files to MP3 format using ffmpeg."
INPUT_TYPES = "Audio Files (*.m4a *.M4A)"
PARAMETERS = [
    {"name": "bitrate", "type": "str", "default": "192k", "description": "Output MP3 bitrate (e.g., 128k, 192k, 256k, 320k)."},
]

# --- Script Logic ---

def check_ffmpeg():
    """
    Check if ffmpeg is installed and accessible.
    
    Returns:
        bool: True if ffmpeg is available, False otherwise
    """
    ffmpeg_path = "/opt/homebrew/bin/ffmpeg"
    return os.path.exists(ffmpeg_path)


def convert_m4a_to_mp3(input_path, output_path, bitrate):
    """
    Convert a single M4A file to MP3 using ffmpeg.
    
    Args:
        input_path (str): Path to input M4A file
        output_path (str): Path to output MP3 file
        bitrate (str): Bitrate for output MP3
    
    Returns:
        bool: True if conversion successful, False otherwise
    """
    try:
        # Build ffmpeg command
        command = [
            "/opt/homebrew/bin/ffmpeg",
            "-i", str(input_path),      # Input file
            "-vn",                       # No video
            "-acodec", "libmp3lame",     # Use MP3 codec
            "-b:a", bitrate,             # Set bitrate
            "-y",                        # Overwrite output file if exists
            str(output_path)             # Output file
        ]
        
        # Run ffmpeg with captured output
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            print(f"ffmpeg error output:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error running ffmpeg: {e}")
        return False


def process_files(file_paths, bitrate):
    """
    Convert M4A files to MP3 format.
    
    Args:
        file_paths (list): List of paths to M4A files
        bitrate (str): Bitrate for the output MP3 files
    """
    # Check if ffmpeg is installed
    if not check_ffmpeg():
        print("Error: ffmpeg is not found at /opt/homebrew/bin/ffmpeg")
        print("\nTo install ffmpeg:")
        print("  macOS (Homebrew): brew install ffmpeg")
        sys.exit(1)
    
    # Validate bitrate - set default if empty
    if not bitrate or bitrate.strip() == "":
        bitrate = "192k"
        print(f"Warning: No bitrate specified, using default: {bitrate}")
    
    home_dir = os.path.expanduser("~")
    script_name_slug = NAME.lower().replace(" ", "_")
    
    # Create a unique output directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    output_folder_name = f"{timestamp}_output"
    output_folder_path = os.path.join(home_dir, "Downloads", script_name_slug, output_folder_name)
    os.makedirs(output_folder_path, exist_ok=True)
    
    print(f"Processing {len(file_paths)} file(s)...")
    print(f"Bitrate: {bitrate}")
    print(f"Output will be saved to: {output_folder_path}")
    print()
    
    successful = 0
    failed = 0
    
    for file_path in file_paths:
        input_path = Path(file_path)
        
        # Validate input file
        if not input_path.exists():
            print(f"✗ Error: File not found: {file_path}")
            failed += 1
            continue
        
        # Create output file path
        output_filename = input_path.stem + ".mp3"
        output_path = os.path.join(output_folder_path, output_filename)
        
        print(f"Converting: {input_path.name}")
        
        # Convert the file
        if convert_m4a_to_mp3(input_path, output_path, bitrate):
            print(f"✓ Successfully converted to: {output_filename}")
            successful += 1
        else:
            print(f"✗ Conversion failed for: {input_path.name}")
            failed += 1
        
        print()
    
    print(f"Conversion complete: {successful} successful, {failed} failed")
    print(f"Output saved to: {output_folder_path}")


# --- Command-Line Execution ---

def main():
    """
    Parses command-line arguments and runs the script.
    """
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    
    # Default argument for input files
    parser.add_argument("file_paths", nargs="+", help="Paths to the M4A files to convert.")
    
    # Add arguments for each parameter defined in PARAMETERS
    for param in PARAMETERS:
        parser.add_argument(
            f'--{param["name"]}',
            type=eval(param["type"]),
            default=param["default"],
            help=param.get("description", f'Default: {param["default"]}')
        )
    
    args = parser.parse_args()
    
    # Convert argument names to a dictionary of keyword arguments
    kwargs = {param["name"]: getattr(args, param["name"]) for param in PARAMETERS}
    
    process_files(args.file_paths, **kwargs)


if __name__ == "__main__":
    main()