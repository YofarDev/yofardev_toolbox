#!/usr/bin/env python3
"""
webcamify.py
Dependencies:
    pip install pillow numpy
"""

from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageOps, ImageEnhance
import numpy as np
import io
import sys
import datetime
import os
import random
import argparse

NAME = "Webcamify Image"
DESCRIPTION = "Simulates the look of a cheap webcam from the early 2000s."
INPUT_TYPES = "Images (*.png *.jpg *.jpeg)"
PARAMETERS = [
    {"name": "pixel_width", "label": "Pixel Width", "type": "int", "default": 640, "min": 64, "max": 1280, "description": "The width of the simulated webcam sensor in pixels."},
    {"name": "pixel_height", "label": "Pixel Height", "type": "int", "default": 480, "min": 48, "max": 960, "description": "The height of the simulated webcam sensor in pixels."},
    {"name": "output_scale", "label": "Output Scale", "type": "int", "default": 2, "min": 1, "max": 10, "description": "The factor by which to scale the output image. For example, a scale of 2 will make the image twice the size of the simulated sensor."},
    {"name": "jpeg_quality", "label": "JPEG Quality", "type": "int", "default": 55, "min": 1, "max": 100, "description": "The quality of the JPEG compression. Lower values mean more compression and lower quality."},
    {"name": "noise_level", "label": "Noise Level", "type": "float", "default": 0.03, "min": 0.0, "max": 1.0, "description": "The amount of noise to add to the image. Higher values mean more noise."},
    {"name": "chroma_offset", "label": "Chroma Offset", "type": "int", "default": 1, "min": 0, "max": 10, "description": "The amount of chromatic aberration to apply. This simulates the color fringing effect of cheap lenses."},
    {"name": "contrast", "label": "Contrast", "type": "float", "default": 1.05, "min": 0.0, "max": 3.0, "description": "The contrast of the image. Higher values mean more contrast."},
    {"name": "saturation", "label": "Saturation", "type": "float", "default": 0.9, "min": 0.0, "max": 3.0, "description": "The saturation of the image. Lower values mean less color."},
    {"name": "sharpness", "label": "Sharpness", "type": "float", "default": 1.3, "min": 0.0, "max": 5.0, "description": "The sharpness of the image. Higher values mean a sharper image."},
    {"name": "interlace_opacity", "label": "Interlace Opacity", "type": "float", "default": 0.05, "min": 0.0, "max": 1.0, "description": "The opacity of the interlace effect. This simulates the look of old CRT monitors."},
    {"name": "ghosting_strength", "label": "Ghosting Strength", "type": "float", "default": 0.1, "min": 0.0, "max": 1.0, "description": "The strength of the ghosting effect. This simulates motion blur."},
    {"name": "timestamp", "label": "Timestamp", "type": "bool", "default": True, "description": "Whether to add a timestamp to the image."},
]


def apply_chromatic_aberration(img, offset=2):
    """Simulates cheap lens splitting colors at edges."""
    if offset == 0:
        return img
    r, g, b = img.split()
    # Shift R and B in opposite directions
    r = ImageOps.expand(r, border=(0, 0, offset, 0), fill=0).crop((offset, 0, r.width + offset, r.height))
    b = ImageOps.expand(b, border=(offset, 0, 0, 0), fill=0).crop((0, 0, b.width, b.height))
    return Image.merge("RGB", (r, g, b))

def add_sensor_noise(img, intensity=0.1):
    """Adds ugly color noise and 'hot pixel' simulation."""
    if intensity <= 0:
        return img
    arr = np.array(img).astype(np.float32)
    h, w, c = arr.shape
    
    # Random Gaussian noise (Grain)
    noise = np.random.normal(0, intensity * 50, (h, w, c))
    
    # "Fixed Pattern" noise (vertical streaks often found in old CCDs)
    col_noise = np.random.normal(0, intensity * 20, (1, w, c))
    
    arr = arr + noise + col_noise
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

def apply_interlacing(img, opacity=0.2):
    """Simulates de-interlacing artifacts (comb effect)."""
    if opacity <= 0:
        return img
    arr = np.array(img.convert("RGBA"))
    # Darken every other line
    arr[1::2, :, 0:3] = arr[1::2, :, 0:3] * (1 - opacity)
    # Slight horizontal shift for even lines (comb effect)
    shift = 1
    arr[1::2, shift:, :] = arr[1::2, :-shift, :]
    return Image.fromarray(arr).convert("RGB")

def crush_dynamic_range(img):
    """Simulates bad auto-exposure (crushed blacks, blown highlights)."""
    # Apply an S-curve using a lookup table
    lut = []
    for i in range(256):
        # Steep curve at ends
        val = int((np.sin((i / 255.0 - 0.5) * np.pi) + 1) / 2 * 255)
        lut.append(val)
    
    # If the image is not single-channel, apply LUT to each channel
    if img.mode != 'L':
        # Split the channels, apply the LUT, and merge them back
        channels = [ch.point(lut) for ch in img.split()]
        return Image.merge(img.mode, channels)
    else:
        # For single-channel images, apply the LUT directly
        return img.point(lut)

def ghosting_effect(img, strength=0.3):
    """Simulates slow shutter speed / motion blur lag."""
    if strength <= 0:
        return img
    # Create a slightly shifted, transparent copy
    ghost = img.copy()
    ghost = ghost.filter(ImageFilter.GaussianBlur(radius=2))
    # Shift it diagonally
    offset_x = int(random.uniform(-3, 3))
    offset_y = int(random.uniform(-1, 3))
    
    base = Image.new('RGB', (img.width + abs(offset_x), img.height + abs(offset_y)))
    base.paste(img, (max(0, offset_x), max(0, offset_y)))
    
    final = img.copy().convert("RGBA")
    ghost = ghost.convert("RGBA")
    
    # Blend
    final = Image.blend(final, ghost, strength).convert("RGB")
    return final

def add_timestamp(img):
    w, h = img.size
    draw = ImageDraw.Draw(img)
    
    # Classic "camcorder" date format
    text = datetime.datetime.now().strftime("%b %d %Y")
    time_text = datetime.datetime.now().strftime("%I:%M:%S %p")
    full_text = f"{time_text}\n{text}".upper()
    
    try:
        # Try to find a monospace font, fallback to default
        font = ImageFont.truetype("arial.ttf", 10) 
    except:
        font = ImageFont.load_default()

    # Draw with a slight shadow for readability against noise
    x, y = w - 80, h - 30
    draw.text((x+1, y+1), full_text, fill=(10, 10, 10), font=font) # Shadow
    draw.text((x, y), full_text, fill=(240, 240, 240), font=font) # White text
    return img

def process_image(input_path, output_path, params):
    img = Image.open(input_path).convert("RGB")

    # 1. DOWN-RES (Simulate sensor size)
    # Scale while PRESERVING aspect ratio.
    # We fit the image inside the bounding box defined by pixel_width/pixel_height
    target_w = params["pixel_width"]
    target_h = params["pixel_height"]
    
    input_aspect = img.width / img.height
    target_aspect = target_w / target_h
    
    if input_aspect > target_aspect:
        # Image is wider than target box -> Fit to width
        native_w = target_w
        native_h = int(target_w / input_aspect)
    else:
        # Image is taller than target box -> Fit to height
        native_h = target_h
        native_w = int(target_h * input_aspect)
        
    # Ensure even dimensions (cleaner for video-like effects)
    if native_w % 2 != 0: native_w -= 1
    if native_h % 2 != 0: native_h -= 1
    
    img = img.resize((native_w, native_h), Image.BILINEAR)

    # 2. LENS DISTORTION (Chromatic Aberration)
    img = apply_chromatic_aberration(img, offset=params["chroma_offset"])

    # 3. GHOSTING / LAG
    img = ghosting_effect(img, strength=params["ghosting_strength"])

    # 4. SENSOR NOISE
    img = add_sensor_noise(img, intensity=params["noise_level"])

    # 5. EXPOSURE / COLOR (Bad dynamic range)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(params["contrast"])
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(params["saturation"])
    img = crush_dynamic_range(img)

    # 6. DIGITAL SHARPENING (The "Logitech Driver" effect)
    img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=40, threshold=3))
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(params["sharpness"])

    # 7. INTERLACING
    img = apply_interlacing(img, opacity=params["interlace_opacity"])

    # 8. FINAL UPSCALE
    # Use nearest neighbor to preserve the chunky pixels.
    final_w = native_w * params["output_scale"]
    final_h = native_h * params["output_scale"]
    img = img.resize((final_w, final_h), Image.NEAREST)

    # 9. TIMESTAMP
    if params["timestamp"]:
        img = add_timestamp(img)

    # 10. SAVE (with aggressive JPEG compression)
    img.save(output_path, "JPEG", quality=params["jpeg_quality"], subsampling=0)
    print(f"Webcamified image saved to {output_path}")

def process_images(image_paths, **kwargs):
    home_dir = os.path.expanduser("~")
    script_name_slug = NAME.lower().replace(" ", "_")
    output_folder = os.path.join(home_dir, "Downloads", script_name_slug)
    os.makedirs(output_folder, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    for image_path in image_paths:
        filename, _ = os.path.splitext(os.path.basename(image_path))
        output_path = os.path.join(output_folder, f"{filename}_{timestamp}.jpg")
        process_image(image_path, output_path, kwargs)

def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("image_paths", nargs='+', help="Input image file(s)")
    
    # Add arguments from PARAMETERS
    for p in PARAMETERS:
        if p['type'] == 'bool':
            parser.add_argument(f"--{p['name']}", action="store_true")
        else:
            parser.add_argument(f"--{p['name']}", type=eval(p['type']), default=p['default'], help=f"Default: {p['default']}")

    args = parser.parse_args()
    
    # Create params dict from args
    params = {p['name']: getattr(args, p['name']) for p in PARAMETERS}
    
    process_images(args.image_paths, **params)

if __name__ == "__main__":
    main()