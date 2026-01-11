import os
import datetime
import argparse
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance

# --- Core Components for UI ---

NAME = "JPEG Artifact Reducer"
DESCRIPTION = "Reduces compression artifacts and blockiness in JPEG images using smoothing and selective sharpening."
INPUT_TYPES = "Images (*.jpg *.jpeg *.png *.webp *.bmp)"

PARAMETERS = [
    {
        "name": "smoothing_radius",
        "type": "float",
        "default": 1.0,
        "min": 0.0,
        "max": 5.0,
        "description": "Gaussian blur radius to smooth block edges. Higher values reduce more artifacts but may soften details."
    },
    {
        "name": "sharpening_amount",
        "type": "float",
        "default": 1.2,
        "min": 0.0,
        "max": 3.0,
        "description": "Sharpening strength to restore edge details after smoothing. Use higher values for soft images."
    },
    {
        "name": "edge_preservation",
        "type": "float",
        "default": 0.3,
        "min": 0.0,
        "max": 1.0,
        "description": "Edge preservation strength. Higher values maintain more original detail at edges while smoothing flat areas."
    },
    {
        "name": "output_quality",
        "type": "int",
        "default": 95,
        "min": 1,
        "max": 100,
        "description": "JPEG quality for the output image (1-100). Higher values reduce further compression but increase file size."
    }
]

# --- Script Logic ---

def get_image_files(paths):
    """
    Recursively finds image files if a folder is passed,
    or returns the path if it's a file.
    """
    valid_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff'}
    images = []

    for path_str in paths:
        path = Path(path_str)
        if path.is_file():
            if path.suffix.lower() in valid_extensions:
                images.append(path)
        elif path.is_dir():
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.suffix.lower() in valid_extensions:
                        images.append(file_path)
    return images


def reduce_artifacts(image, smoothing_radius, sharpening_amount, edge_preservation):
    """
    Apply artifact reduction using a combination of techniques:
    1. Gaussian blur to smooth block boundaries
    2. Edge-preserving blend to maintain detail
    3. Selective sharpening to restore clarity
    """
    # Step 1: Apply mild Gaussian blur to reduce blockiness
    if smoothing_radius > 0:
        blurred = image.filter(ImageFilter.GaussianBlur(radius=smoothing_radius))
    else:
        blurred = image

    # Step 2: Blend original and blurred based on edge preservation
    # Create an edge mask to preserve important edges
    if edge_preservation > 0:
        # Detect edges using OpenCV
        import numpy as np
        import cv2

        original_arr = np.array(image)
        blurred_arr = np.array(blurred)

        # Convert to grayscale and detect edges using Sobel operator
        gray = cv2.cvtColor(original_arr, cv2.COLOR_RGB2GRAY)

        # Calculate gradient magnitude for edge detection
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        edge_magnitude = np.sqrt(sobel_x**2 + sobel_y**2)

        # Normalize edge mask to 0-1 range
        edge_mask = np.clip(edge_magnitude / (edge_magnitude.max() + 1e-6), 0, 1)

        # Expand mask to 3 channels
        edge_mask = np.stack([edge_mask] * 3, axis=2)

        # Blend: keep more original at edges, more blurred in flat areas
        blend_factor = edge_preservation
        result_arr = original_arr.astype(np.float32) * edge_mask * blend_factor + \
                     blurred_arr.astype(np.float32) * (1 - edge_mask * blend_factor)
        result = Image.fromarray(np.clip(result_arr, 0, 255).astype(np.uint8))
    else:
        result = blurred

    # Step 3: Apply selective sharpening to restore detail
    if sharpening_amount > 1.0:
        enhancer = ImageEnhance.Sharpness(result)
        result = enhancer.enhance(sharpening_amount)

    return result


def process_files(file_paths, smoothing_radius, sharpening_amount, edge_preservation, output_quality):
    """
    Main processing logic.
    """
    home_dir = os.path.expanduser("~")
    script_name_slug = NAME.lower().replace(" ", "_")

    # 1. Create a unique output directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    output_folder_name = f"{timestamp}_output"
    output_folder_path = os.path.join(home_dir, "Downloads", script_name_slug, output_folder_name)
    os.makedirs(output_folder_path, exist_ok=True)

    # Collect actual image files from inputs (handles folders)
    target_images = get_image_files(file_paths)

    print(f"Found {len(target_images)} image(s) to process.")
    print(f"Smoothing Radius: {smoothing_radius}")
    print(f"Sharpening Amount: {sharpening_amount}")
    print(f"Edge Preservation: {edge_preservation}")
    print(f"Output Quality: {output_quality}")
    print(f"Output location: {output_folder_path}")

    success_count = 0

    for img_path in target_images:
        try:
            filename = img_path.name
            print(f"-> Processing: {filename}")

            # Open the image
            with Image.open(img_path) as img:
                # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Apply artifact reduction
                processed = reduce_artifacts(
                    img,
                    smoothing_radius,
                    sharpening_amount,
                    edge_preservation
                )

                # Determine output filename
                name_without_ext = img_path.stem
                output_filename = f"{name_without_ext}.jpg"
                output_path = os.path.join(output_folder_path, output_filename)

                # Save with specified quality
                processed.save(output_path, "JPEG", quality=output_quality, optimize=True)
                success_count += 1

        except Exception as e:
            print(f"!! Error processing {img_path.name}: {e}")

    print("-" * 30)
    print(f"Processing complete. {success_count}/{len(target_images)} images saved.")
    print(f"Folder: {output_folder_path}")


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
            type=eval(param["type"]),  # Use eval to dynamically set the type
            default=param["default"],
            help=f'Default: {param["default"]}'
        )

    args = parser.parse_args()

    # Convert argument names to a dictionary of keyword arguments
    kwargs = {param["name"]: getattr(args, param["name"]) for param in PARAMETERS}

    process_files(args.file_paths, **kwargs)


if __name__ == "__main__":
    main()
