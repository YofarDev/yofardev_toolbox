"""Script discovery, loading, and management."""
import importlib.util
import os
from pathlib import Path
from typing import List, Dict, Optional
from config.app_config import SCRIPTS_DIR, SKIP_FILES


class ScriptManager:
    """Manages script discovery, loading, and filtering."""

    def __init__(self):
        self._scripts_cache: List[Dict] = []

    def load_scripts(self) -> List[Dict]:
        """
        Discover and load all scripts from the scripts directory.

        Returns:
            List of script dictionaries with metadata
        """
        scripts = []

        # Create scripts directory if it doesn't exist
        if not os.path.exists(SCRIPTS_DIR):
            os.makedirs(SCRIPTS_DIR)

        if os.path.exists(SCRIPTS_DIR) and os.path.isdir(SCRIPTS_DIR):
            for filename in sorted(os.listdir(SCRIPTS_DIR)):
                if (filename.endswith(".py")
                    and not filename.startswith("__")
                    and filename not in SKIP_FILES):
                    try:
                        script_path = os.path.join(SCRIPTS_DIR, filename)
                        spec = importlib.util.spec_from_file_location(filename[:-3], script_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        scripts.append({
                            "name": getattr(module, "NAME", filename[:-3]),
                            "filename": filename[:-3],
                            "description": getattr(module, "DESCRIPTION", "No description available."),
                            "input_types": getattr(module, "INPUT_TYPES", ""),
                            "parameters": getattr(module, "PARAMETERS", []),
                            "accepts_multiple_files": getattr(module, "ACCEPTS_MULTIPLE_FILES", True),
                        })
                    except Exception as e:
                        print(f"Error loading {filename}: {e}")

        self._scripts_cache = scripts
        return scripts

    def get_script_by_name(self, name: str) -> Optional[Dict]:
        """
        Get a script by its display name.

        Args:
            name: The script's display name

        Returns:
            Script dict or None if not found
        """
        if not self._scripts_cache:
            self.load_scripts()

        for script in self._scripts_cache:
            if script["name"] == name:
                return script
        return None

    def get_script_by_filename(self, filename: str) -> Optional[Dict]:
        """
        Get a script by its filename.

        Args:
            filename: The script's filename (without .py extension)

        Returns:
            Script dict or None if not found
        """
        if not self._scripts_cache:
            self.load_scripts()

        for script in self._scripts_cache:
            if script["filename"] == filename:
                return script
        return None

    def filter_scripts(self, scripts: List[Dict], query: str) -> List[Dict]:
        """
        Filter scripts by search query.

        Args:
            scripts: List of scripts to filter
            query: Search query string

        Returns:
            Filtered list of scripts
        """
        if not query:
            return scripts

        query = query.lower().strip()
        filtered = []

        for script in scripts:
            name_matches = query in script["name"].lower()
            desc_matches = query in script["description"].lower()

            if name_matches or desc_matches:
                filtered.append(script)

        return filtered

    def validate_script(self, code: str) -> tuple[bool, str]:
        """
        Validate script has required variables and functions.

        Args:
            code: The Python code to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        required_vars = ["NAME", "DESCRIPTION", "INPUT_TYPES", "PARAMETERS"]

        try:
            namespace = {}
            compiled = compile(code, "<string>", "exec")
            exec(compiled, namespace)

            # Check required variables
            for var in required_vars:
                if var not in namespace:
                    return False, f"Missing required variable: {var}"

            # Check NAME is non-empty string
            if not isinstance(namespace.get("NAME"), str) or not namespace["NAME"].strip():
                return False, "NAME must be a non-empty string"

            # Check PARAMETERS is a list
            if not isinstance(namespace.get("PARAMETERS"), list):
                return False, "PARAMETERS must be a list"

            # Check for required functions
            if "main" not in namespace or not callable(namespace["main"]):
                return False, "Missing required function: main()"

            if "process_files" not in namespace or not callable(namespace["process_files"]):
                return False, "Missing required function: process_files()"

            return True, ""

        except SyntaxError as e:
            return False, f"Syntax error: {e}"
        except Exception as e:
            return False, f"Validation error: {e}"

    def get_all(self) -> List[Dict]:
        """Get all cached scripts."""
        if not self._scripts_cache:
            self.load_scripts()
        return self._scripts_cache.copy()

    def refresh(self) -> List[Dict]:
        """Reload and return scripts."""
        return self.load_scripts()
