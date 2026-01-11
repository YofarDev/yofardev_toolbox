import glob
import os
import sys
import datetime
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance

def apply_vibrance_saturation_boost(image, vibrance_boost=0.10, saturation_boost=0.10):
    enhancer = ImageEnhance.Color(image)
    saturated_image = enhancer.enhance(1.0 + saturation_boost)
    img_hsv = saturated_image.convert("HSV")
    img_array = np.array(img_hsv)
    h, s, v = img_array[:, :, 0], img_array[:, :, 1], img_array[:, :, 2]
    s_norm = s / 255.0
    vibrance_adjustment = vibrance_boost * (1 - s_norm)
    s_adjusted = s_norm + vibrance_adjustment
    s_adjusted = np.clip(s_adjusted, 0, 1)
    s_final = (s_adjusted * 255).astype(np.uint8)
    img_array[:, :, 1] = s_final
    vibrance_image_hsv = Image.fromarray(img_array, "HSV")
    final_image = vibrance_image_hsv.convert("RGB")
    return final_image

def process_images(
    image_paths,
    vibrance_boost=0.10,
    saturation_boost=0.10,
):
    home_dir = os.path.expanduser("~")
    script_name_slug = NAME.lower().replace(" ", "_")
    output_folder = os.path.join(home_dir, "Downloads", script_name_slug)
    os.makedirs(output_folder, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    for input_path in image_paths:
        try:
            original = Image.open(input_path).convert("RGB")
            filename = os.path.basename(input_path)
            name, ext = os.path.splitext(filename)
            
            output_path = os.path.join(output_folder, f"{name}_{timestamp}_enhanced{ext}")
            result_image = apply_vibrance_saturation_boost(original, vibrance_boost, saturation_boost)

            result_image.save(output_path, quality=95)
            print(f"Enhanced: {input_path} -> {output_path}")

        except Exception as e:
            print(f"Error processing {input_path}: {e}")

DESCRIPTION = "Applies vibrance and saturation boost to images."
NAME = "Vibrance Saturation Enhancer"
INPUT_TYPES = "Images (*.png *.jpg *.jpeg)"
PARAMETERS = [
    {"name": "vibrance_boost", "type": "float", "default": 0.10, "description": "The amount to boost the vibrance of the image."},
    {"name": "saturation_boost", "type": "float", "default": 0.10, "description": "The amount to boost the saturation of the image."},
]

def main():
    import argparse
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("image_paths", nargs="+", help="Paths to the images to process.")
    for param in PARAMETERS:
        if param["type"] == "choice":
            parser.add_argument(f'--{param["name"]}', choices=param["choices"], default=param["default"], help=f'Default: {param["default"]}')
        else:
            parser.add_argument(f'--{param["name"]}', type=eval(param["type"]), default=param["default"], help=f'Default: {param["default"]}')
    
    args = parser.parse_args()
    
    process_images(
        args.image_paths,
        vibrance_boost=args.vibrance_boost,
        saturation_boost=args.saturation_boost,
    )

if __name__ == "__main__":
    main()