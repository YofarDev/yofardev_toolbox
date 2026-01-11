"""File handling utilities."""
import os
from tkinter import filedialog
from pathlib import Path
from typing import List, Tuple, Optional


class FileHandler:
    """Handles file selection and validation."""

    def select_files(self, filetypes: List[Tuple], multiple: bool = True) -> List[str]:
        """
        Open file dialog and return selected files.

        Args:
            filetypes: List of (description, extensions) tuples
            multiple: Whether to allow multiple file selection

        Returns:
            List of selected file paths
        """
        if multiple:
            files = filedialog.askopenfilenames(filetypes=filetypes)
            return list(files) if files else []
        else:
            file = filedialog.askopenfilename(filetypes=filetypes)
            return [file] if file else []

    def select_folder(self) -> Optional[str]:
        """
        Open folder dialog and return path.

        Returns:
            Selected folder path or None
        """
        folder = filedialog.askdirectory()
        return folder if folder else None

    def get_images_from_folder(self, folder: str, extensions: List[str]) -> List[str]:
        """
        Recursively find images in a folder.

        Args:
            folder: Path to the folder
            extensions: List of valid file extensions (e.g., [".jpg", ".png"])

        Returns:
            List of image file paths
        """
        images = []
        for root, _, files in os.walk(folder):
            for file in files:
                if not extensions or any(file.lower().endswith(ext.lower()) for ext in extensions):
                    full_path = os.path.join(root, file)
                    images.append(full_path)
        return images

    def parse_input_types(self, input_str: str) -> List[Tuple[str, str]]:
        """
        Parse INPUT_TYPES string into filetypes format.

        Args:
            input_str: Input types string like "Images (*.png *.jpg)"

        Returns:
            List of (description, extensions) tuples
        """
        filetypes = []
        if not input_str:
            return filetypes

        try:
            parts = input_str.split("(")
            if len(parts) > 1:
                desc = parts[0].strip()
                exts = parts[1].replace(")", "")
                filetypes.append((desc, exts))
        except Exception:
            pass

        # Always add "All Files" option
        filetypes.append(("All Files", "*.*"))
        return filetypes

    def get_file_extensions(self, input_str: str) -> List[str]:
        """
        Extract file extensions from INPUT_TYPES string.

        Args:
            input_str: Input types string like "Images (*.png *.jpg)"

        Returns:
            List of extensions like [".png", ".jpg"]
        """
        try:
            parts = input_str.split("(")
            if len(parts) > 1:
                exts_str = parts[1].replace(")", "").replace("*", "").replace(",", "")
                return exts_str.split()
        except Exception:
            pass
        return []
