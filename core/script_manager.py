"""Script discovery, loading, and management."""
import importlib.util
import os
import ast
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from config.app_config import SCRIPTS_DIR, SKIP_FILES


class ScriptManager:
    """Manages script discovery, loading, and filtering."""

    def __init__(self):
        self._scripts_cache: List[Dict] = []

    def _extract_metadata_ast(self, script_path: str, filename: str) -> Optional[Dict]:
        """
        Extract script metadata using AST parsing (without importing).

        This avoids ImportError when scripts have missing dependencies.

        Args:
            script_path: Path to the script file
            filename: Name of the script file

        Returns:
            Script dict with metadata, or None if extraction fails
        """
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                code = f.read()

            # Parse the code into AST
            tree = ast.parse(code)

            # Initialize with defaults
            metadata = {
                "name": filename[:-3],  # Use filename as default
                "filename": filename[:-3],
                "description": "No description available.",
                "input_types": "",
                "parameters": [],
                "accepts_multiple_files": True,
            }

            # Walk the AST to find module-level variables
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id
                            var_value = node.value

                            # Extract string values
                            if isinstance(var_value, ast.Constant):
                                if var_name == "NAME" and isinstance(var_value.value, str):
                                    metadata["name"] = var_value.value
                                elif var_name == "DESCRIPTION" and isinstance(var_value.value, str):
                                    metadata["description"] = var_value.value
                                elif var_name == "INPUT_TYPES" and isinstance(var_value.value, str):
                                    metadata["input_types"] = var_value.value

                            # Extract PARAMETERS list
                            elif var_name == "PARAMETERS" and isinstance(var_value, ast.List):
                                # Try to evaluate the list safely
                                try:
                                    # Compile and evaluate just the list node
                                    param_code = compile(ast.Expression(var_value), '<string>', 'eval')
                                    metadata["parameters"] = eval(param_code, {"__builtins__": {}}, {})
                                except:
                                    metadata["parameters"] = []

                            # Extract ACCEPTS_MULTIPLE_FILES boolean
                            elif var_name == "ACCEPTS_MULTIPLE_FILES" and isinstance(var_value, ast.Constant):
                                metadata["accepts_multiple_files"] = bool(var_value.value)

            return metadata

        except SyntaxError as e:
            print(f"Error loading {filename}: Syntax error: {e}")
            return None
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return None

    def load_scripts(self) -> List[Dict]:
        """
        Discover and load all scripts from the scripts directory.

        Uses AST parsing to extract metadata without importing modules,
        which avoids ImportError when dependencies are missing.

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
                    script_path = os.path.join(SCRIPTS_DIR, filename)

                    # Use AST parsing to extract metadata (no import required)
                    metadata = self._extract_metadata_ast(script_path, filename)
                    if metadata:
                        scripts.append(metadata)

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
