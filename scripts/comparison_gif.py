import numpy as np
import cv2
import imageio
import os
import sys
import datetime

def create_comparison_gif(original_path, enhanced_path):
    # Load images
    original = cv2.imread(original_path)
    enhanced = cv2.imread(enhanced_path)

    # Get image dimensions
    h, w, _ = enhanced.shape

    # Create a list to store the frames
    frames = []

    # Animate the comparison
    for i in range(0, w, 10):  # Move the line 10 pixels at a time
        # Create a blank image
        frame = np.zeros((h, w, 3), dtype=np.uint8)

        # Copy the left part of the image from img1
        frame[:, :i, :] = enhanced[:, :i, :]

        # Copy the right part of the image from img2
        frame[:, i:, :] = original[:, i:, :]

        # Draw a vertical line
        cv2.line(frame, (i, 0), (i, h), (255, 255, 255), 1)

        # Convert to RGB (required for imageio)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Append the frame to the list
        frames.append(frame)

    home_dir = os.path.expanduser("~")
    script_name_slug = NAME.lower().replace(" ", "_")
    output_folder = os.path.join(home_dir, "Downloads", script_name_slug)
    os.makedirs(output_folder, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    output_path = os.path.join(output_folder, f"comparison_{timestamp}.gif")
    imageio.mimsave(output_path, frames, 'GIF', duration=0.01)

DESCRIPTION = "Creates a GIF animation comparing two images with a vertical slider."
NAME = "Comparison GIF"
INPUT_TYPES = "Images (*.png *.jpg *.jpeg)"
PARAMETERS = []

def main():
    import argparse
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("image_paths", nargs=2, help="Paths to the two images to compare.")
    args = parser.parse_args()
    
    create_comparison_gif(args.image_paths[0], args.image_paths[1])

if __name__ == "__main__":
    main()