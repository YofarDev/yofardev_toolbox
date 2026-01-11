# How to Write a Script for the Toolbox UI

This document explains how to create a Python script that is compatible with the Toolbox UI.

## File Location

All scripts must be placed in the `scripts/` directory.

## Core Components

For the UI to correctly display and execute your script, you must define the following variables in the global scope of your script file:

### `NAME`

A user-friendly name for your script. This will be displayed in the list of available scripts.

- **Type:** `str`
- **Example:** `NAME = "Image Downscaler"`

### `DESCRIPTION`

A short, clear description of what your script does. This will be shown when the user selects your script.

- **Type:** `str`
- **Example:** `DESCRIPTION = "Downscales an image to a specific size."`

### `INPUT_TYPES`

A string that describes the file types your script accepts. This is used for the file dialog filter.

- **Type:** `str`
- **Example:** `INPUT_TYPES = "Images (*.png *.jpg *.jpeg)"`

### `PARAMETERS`

A list of dictionaries, where each dictionary defines a configurable parameter for your script. These parameters will be displayed as input fields in the UI.

- **Type:** `list[dict]`
- **Structure of each dictionary:**
    - `name` (str): The name of the parameter. This will be used as the command-line argument name (e.g., `--radius`).
    - `type` (str): The expected Python type of the parameter (e.g., `"int"`, `"str"`, `"float"`).
    - `default`: The default value for the parameter.
    - `description` (str, optional): A short explanation of what the parameter controls, displayed in the UI.

- **Example:**
  ```python
  PARAMETERS = [
      {"name": "width", "type": "int", "default": 1280, "description": "The target width of the image."},
      {"name": "height", "type": "int", "default": 720, "description": "The target height of the image."},
      {"name": "quality", "type": "int", "default": 95, "description": "The output quality for the image (0-100)."},
  ]
  ```

## Script Logic

### Input

Your script will receive one or more file paths as command-line arguments. The UI will pass the paths of the files or folders selected by the user.

It is highly recommended to use Python's `argparse` module to handle these arguments.

### Output

- All output files should be saved to a unique, timestamped directory to avoid overwriting previous results.
- The output directory should be created inside the user's `Downloads` folder, in a subfolder named after your script.

- **Example Output Directory Structure:**
  `~/Downloads/<script_name_slug>/<timestamped_output_files>`

### Example Script (`scripts/template_script.py`)

Here is a basic template you can use as a starting point for your own scripts. It includes argument parsing, parameter handling, and the recommended output directory structure.

```python
import os
-import sys
import datetime
import argparse

# --- Core Components for UI ---

NAME = "My Awesome Script"
DESCRIPTION = "A brief description of what this script does."
INPUT_TYPES = "All files (*.*)" # e.g., "Images (*.png *.jpg)"
PARAMETERS = [
    {"name": "my_parameter", "type": "str", "default": "default_value", "description": "An example string parameter."},
    {"name": "another_param", "type": "int", "default": 42, "description": "An example integer parameter."},
]

# --- Script Logic ---

def process_files(file_paths, my_parameter, another_param):
    """
    Your main processing logic goes here.
    """
    home_dir = os.path.expanduser("~")
    script_name_slug = NAME.lower().replace(" ", "_")
    
    # 1. Create a unique output directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    output_folder_name = f"{timestamp}_output"
    output_folder_path = os.path.join(home_dir, "Downloads", script_name_slug, output_folder_name)
    os.makedirs(output_folder_path, exist_ok=True)
    
    print(f"Processing {len(file_paths)} file(s)...")
    print(f"My Parameter: {my_parameter}")
    print(f"Another Param: {another_param}")
    print(f"Output will be saved to: {output_folder_path}")

    for file_path in file_paths:
        # 2. Process each file
        print(f"-> Processing {file_path}")
        
        # Example: Create a dummy output file
        filename = os.path.basename(file_path)
        output_path = os.path.join(output_folder_path, f"processed_{filename}")
        with open(output_path, "w") as f:
            f.write(f"Processed {filename} with parameter '{my_parameter}'.")

    print("Processing complete.")


# --- Command-Line Execution ---

def main():
    """
    Parses command-line arguments and runs the script.
    """
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    
    # Default argument for input files
    parser.add_argument("file_paths", nargs="+", help="Paths to the input files to process.")
    
    # Add arguments for each parameter defined in PARAMETERS
    for param in PARAMETERS:
        parser.add_argument(
            f'--{param["name"]}',
            type=eval(param["type"]), # Use eval to dynamically set the type
            default=param["default"],
            help=f'Default: {param["default"]}'
        )
    
    args = parser.parse_args()
    
    # Convert argument names to a dictionary of keyword arguments
    kwargs = {param["name"]: getattr(args, param["name"]) for param in PARAMETERS}
    
    process_files(args.file_paths, **kwargs)

if __name__ == "__main__":
    # This allows the script to be run from the command line
    main()
```
