import glob
import os
import sys
import datetime
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance

def color_dodge_blend(base, blend, opacity=1.0):
    base_array = np.array(base, dtype=np.float32) / 255.0
    blend_array = np.array(blend, dtype=np.float32) / 255.0
    blend_array = np.clip(blend_array, 0, 0.999)
    result = base_array / (1.0 - blend_array)
    result = np.clip(result, 0, 1)
    if opacity < 1.0:
        result = base_array * (1 - opacity) + result * opacity
    return (result * 255).astype(np.uint8)

def lighten_blend(base, blend, opacity=1.0):
    base_array = np.array(base, dtype=np.float32)
    blend_array = np.array(blend, dtype=np.float32)
    result = np.maximum(base_array, blend_array)
    if opacity < 1.0:
        result = base_array * (1 - opacity) + result * opacity
    return Image.fromarray(result.astype(np.uint8))

def add_uniform_noise(image, amount=30):
    img_array = np.array(image)
    noise = np.random.uniform(-1, 1, img_array.shape) * (amount / 100.0) * 255
    noisy = img_array.astype(np.float32) + noise
    noisy = np.clip(noisy, 0, 255)
    return Image.fromarray(noisy.astype(np.uint8))

def apply_glow_effect(image, blur_radius=8, opacity=0.35):
    duplicate = image.copy()
    blurred_duplicate = duplicate.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    result_image = lighten_blend(image, blurred_duplicate, opacity)
    return result_image

def apply_noise_effect(image, noise_amount=30, opacity=0.45):
    width, height = image.size
    black_layer = Image.new("RGB", (width, height), (0, 0, 0))
    noisy_black = add_uniform_noise(black_layer, noise_amount)
    result_array = color_dodge_blend(image, noisy_black, opacity)
    result_image = Image.fromarray(result_array)
    return result_image

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
    effect_type="combined",
    blur_radius=8,
    lighten_opacity=0.35,
    noise_amount=30,
    dodge_opacity=0.45,
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
            
            if effect_type == "glow":
                output_path = os.path.join(output_folder, f"{name}_{timestamp}_glow{ext}")
                result_image = apply_glow_effect(original, blur_radius, lighten_opacity)
            elif effect_type == "noise":
                output_path = os.path.join(output_folder, f"{name}_{timestamp}_noise{ext}")
                result_image = apply_noise_effect(original, noise_amount, dodge_opacity)
            else: # combined
                output_path = os.path.join(output_folder, f"{name}_{timestamp}_combined{ext}")
                first_result = apply_glow_effect(original, blur_radius, lighten_opacity)
                second_result = apply_noise_effect(first_result, noise_amount, dodge_opacity)
                result_image = apply_vibrance_saturation_boost(second_result, vibrance_boost, saturation_boost)

            result_image.save(output_path, quality=95)
            print(f"Effect '{effect_type}' applied: {input_path} -> {output_path}")

        except Exception as e:
            print(f"Error processing {input_path}: {e}")

DESCRIPTION = "Applies a combination of effects to images to give them an 'anime' look. It can apply a glow, noise, and vibrance/saturation boost."
NAME = "Anime Enhancer"
INPUT_TYPES = "Images (*.png *.jpg *.jpeg)"
PARAMETERS = [
    {"name": "effect_type", "type": "choice", "choices": ["combined", "glow", "noise"], "default": "combined", "description": "The type of effect to apply. 'combined' applies all effects, 'glow' applies only the glow effect, and 'noise' applies only the noise effect."},
    {"name": "blur_radius", "type": "int", "default": 8, "description": "The radius of the blur for the glow effect."},
    {"name": "lighten_opacity", "type": "float", "default": 0.35, "description": "The opacity of the lighten blend for the glow effect."},
    {"name": "noise_amount", "type": "int", "default": 30, "description": "The amount of noise to add for the noise effect."},
    {"name": "dodge_opacity", "type": "float", "default": 0.45, "description": "The opacity of the color dodge blend for the noise effect."},
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
        effect_type=args.effect_type,
        blur_radius=args.blur_radius,
        lighten_opacity=args.lighten_opacity,
        noise_amount=args.noise_amount,
        dodge_opacity=args.dodge_opacity,
        vibrance_boost=args.vibrance_boost,
        saturation_boost=args.saturation_boost,
    )

if __name__ == "__main__":
    main()