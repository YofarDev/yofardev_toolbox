"""
LLM-powered script generator for Yofardev Toolbox.

Handles communication with OpenAI-compatible APIs to generate and edit scripts.
"""
import requests
import re
import ast
import json
from typing import Optional, Dict, Callable


# Maximum retry attempts for script generation
MAX_RETRIES = 3

# Prompt templates for script generation

CREATE_TEMPLATE = """You are an expert Python developer specializing in batch file processing scripts.

TASK: Create a new batch processing script based on the user's request.

USER REQUEST: {user_prompt}

OUTPUT FORMAT:
Respond with a JSON object containing the script and metadata:

{{
  "name": "Script Display Name",
  "description": "Brief description of what this script does",
  "packages": ["package-name-1", "package-name-2"],
  "code": "COMPLETE PYTHON CODE HERE"
}}

IMPORTANT:
- "packages" should contain the ACTUAL PyPI/pip package names needed to install
- Example: If you use "import fitz", the package is "pymupdf"
- Example: If you use "import cv2", the package is "opencv-python"
- Example: If you use "import PIL", the package is "Pillow" (likely already installed)
- Only list packages that need to be installed (NOT: os, sys, json, datetime, pathlib, argparse, subprocess, etc.)
- "code" should be the complete, valid Python script

SCRIPT TEMPLATE (paste this into the "code" field and fill in the logic):

```python
import os
import datetime
import argparse
from pathlib import Path
from PIL import Image

# Import any external packages you need
# import fitz  # PyMuPDF - requires: pip install pymupdf
# import cv2  # OpenCV - requires: pip install opencv-python
# import pandas as pd  # Pandas - requires: pip install pandas

# --- Core Components for UI ---

NAME = "Script Name Here"
DESCRIPTION = "Brief description of what this script does"
INPUT_TYPES = "Images (*.png *.jpg *.jpeg *.webp *.bmp)"

PARAMETERS = [
    # Define parameters here - each parameter is a dict with:
    # - name (str): parameter name
    # - type (str): "int", "float", "str", or "bool"
    # - default: default value
    # - description (str): help text
    {{
        "name": "example_param",
        "type": "int",
        "default": 100,
        "description": "What this parameter does"
    }}
]

# --- Script Logic ---

def process_files(file_paths, **kwargs):
    '''
    Main processing logic.

    Args:
        file_paths: List of input file paths
        **kwargs: Parameter values from UI
    '''
    # 1. Create output directory
    home_dir = os.path.expanduser("~")
    script_name_slug = NAME.lower().replace(" ", "_")
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    output_folder_path = os.path.join(home_dir, "Downloads", script_name_slug, f"{{timestamp}}_output")
    os.makedirs(output_folder_path, exist_ok=True)

    # 2. Process files
    for file_path in file_paths:
        # Your processing logic here
        # Get parameters from kwargs: kwargs.get("param_name", default_value)
        pass

    print(f"Processing complete. Output: {{output_folder_path}}")

# --- Command-Line Execution ---

def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("file_paths", nargs="+", help="Paths to input files")
    for param in PARAMETERS:
        parser.add_argument(f'--{{param["name"]}}', type=eval(param["type"]), default=param["default"])
    args = parser.parse_args()
    kwargs = {{param["name"]: getattr(args, param["name"]) for param in PARAMETERS}}
    process_files(args.file_paths, **kwargs)

if __name__ == "__main__":
    main()
```

CRITICAL - FORBIDDEN PATTERNS (YOUR CODE WILL BE REJECTED IF YOU USE THESE):
❌ NEVER hardcode directories like 'static/', 'output/', 'temp/', 'data/', 'tmp/', 'outputs/'
❌ NEVER use relative paths for file outputs
❌ NEVER use web framework patterns (Flask's static_folder, Django's static files, etc.)
✅ ALWAYS use: output_folder_path = os.path.join(home_dir, "Downloads", script_name_slug, f"{{timestamp}}_output")
✅ ALL output files MUST go to output_folder_path
✅ Use os.path.join() or Path() for all path construction

COMMON PACKAGE MAPPINGS (for the "packages" field):
- import fitz → "pymupdf"
- import cv2 → "opencv-python"
- import PIL → "Pillow"
- import yaml → "PyYAML"
- import bs4 → "beautifulsoup4"
- import pandas → "pandas"
- import numpy → "numpy"
- import matplotlib.pyplot → "matplotlib"

Respond with ONLY the JSON object, no explanations, no markdown code blocks.
"""

EDIT_TEMPLATE = """You are an expert Python developer specializing in batch file processing scripts.

TASK: Modify the existing script based on the user's request.

EXISTING SCRIPT:
```python
{existing_script}
```

USER REQUEST: {user_prompt}

CRITICAL - FORBIDDEN PATTERNS (YOUR CODE WILL BE REJECTED IF YOU USE THESE):
❌ NEVER hardcode directories like 'static/', 'output/', 'temp/', 'data/', 'tmp/', 'outputs/'
❌ NEVER use relative paths for file outputs
❌ NEVER use web framework patterns (Flask's static_folder, Django's static files, etc.)
✅ ALWAYS use: output_folder_path = os.path.join(home_dir, "Downloads", script_name_slug, f"{{timestamp}}_output")
✅ ALL output files MUST go to output_folder_path
✅ Use os.path.join() or Path() for all path construction

REQUIREMENTS:
1. Maintain the exact same structure (module-level variables, process_files, main)
2. Keep existing functionality unless told to remove it
3. OUTPUT ONLY the complete modified Python code
4. Ensure all changes integrate smoothly with existing code
5. Keep the same NAME unless the user wants to rename it
6. Update DESCRIPTION if functionality changes significantly
7. Add/remove/update PARAMETERS as needed
8. Follow the same output directory convention

Respond with ONLY the Python code, nothing else. Do not include markdown code blocks, just the raw Python code.
"""

RETRY_TEMPLATE = """The previously generated script has validation errors. Please fix them.

ORIGINAL USER REQUEST: {user_prompt}

PREVIOUS ATTEMPT:
```python
{previous_code}
```

VALIDATION ERROR:
{error_message}

CRITICAL - FORBIDDEN PATTERNS (YOUR CODE WILL BE REJECTED IF YOU USE THESE):
❌ NEVER hardcode directories like 'static/', 'output/', 'temp/', 'data/', 'tmp/', 'outputs/'
❌ NEVER use relative paths for file outputs
❌ NEVER use web framework patterns (Flask's static_folder, Django's static files, etc.)
✅ ALWAYS use: output_folder_path = os.path.join(home_dir, "Downloads", script_name_slug, f"{{timestamp}}_output")
✅ ALL output files MUST go to output_folder_path
✅ Use os.path.join() or Path() for all path construction

REQUIREMENTS:
1. Fix the validation error mentioned above
2. Ensure all required variables are present: NAME, DESCRIPTION, INPUT_TYPES, PARAMETERS
3. Ensure both required functions exist: main() and process_files()
4. main() must use argparse to accept file_paths and parameters
5. process_files() must accept file_paths and **kwargs
6. Keep the same functionality intended by the original request
7. Output ONLY valid Python code - no explanations

Respond with ONLY the complete, fixed Python code. Do not include markdown code blocks.
"""


class GenerationError(Exception):
    """Base exception for script generation errors."""
    pass


class APIError(GenerationError):
    """Exception raised when API communication fails."""
    pass


class ValidationError(GenerationError):
    """Exception raised when generated script fails validation."""
    pass


class ScriptGenerator:
    """Handles LLM-based script generation and editing."""

    def __init__(self, endpoint: str, model: str, api_key: str, timeout: int = 120):
        """
        Initialize the script generator.

        Args:
            endpoint: API endpoint URL
            model: Model name
            api_key: API key for authentication
            timeout: Request timeout in seconds
        """
        self.endpoint = endpoint
        self.model = model
        self.api_key = api_key
        self.timeout = timeout
        self.last_generated_code = ""
        self.last_validation_error = ""

    def _make_api_request(self, messages: list) -> str:
        """
        Make a request to the LLM API.

        Args:
            messages: List of message dicts with 'role' and 'content'

        Returns:
            str: The generated response content

        Raises:
            APIError: If the request fails
        """
        headers = {
            "Content-Type": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 4000,
        }

        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            return data["choices"][0]["message"]["content"]

        except requests.exceptions.Timeout:
            raise APIError("Request timed out. The API took too long to respond.")
        except requests.exceptions.ConnectionError:
            raise APIError("Could not connect to the API endpoint. Check your URL and network connection.")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise APIError("Authentication failed. Check your API key.")
            elif e.response.status_code == 429:
                raise APIError("Rate limit exceeded. Please wait and try again.")
            else:
                raise APIError(f"HTTP {e.response.status_code}: {e.response.text}")
        except (KeyError, IndexError) as e:
            raise APIError(f"Unexpected API response format: {e}")

    def _extract_code_from_response(self, response: str) -> str:
        """
        Extract Python code from the LLM response (fallback method).

        Handles responses that may or may not include markdown code blocks.
        Used as fallback when JSON parsing fails.

        Args:
            response: Raw response text from the API

        Returns:
            str: Clean Python code
        """
        # Try to extract from markdown code blocks
        pattern = r'```(?:python)?\s*\n?(.*?)\n?```'
        matches = re.findall(pattern, response, re.DOTALL)

        if matches:
            return matches[0].strip()

        # No code blocks found, return as-is
        return response.strip()

    def _parse_json_response(self, response: str) -> dict:
        """
        Parse JSON response from LLM.

        Extracts the script code, name, description, and packages from JSON.

        Args:
            response: Raw response text from the API

        Returns:
            dict with keys: name, description, packages, code

        Raises:
            APIError: If JSON parsing fails
        """
        # Try to parse as JSON directly
        try:
            data = json.loads(response.strip())
            return data
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code blocks
        pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
        matches = re.findall(pattern, response, re.DOTALL)

        if matches:
            try:
                data = json.loads(matches[0].strip())
                return data
            except json.JSONDecodeError:
                pass

        # If all else fails, try to find JSON-like structure
        try:
            # Find first { and last }
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                data = json.loads(json_str)
                return data
        except:
            pass

        # Failed to parse JSON
        raise APIError(
            "Failed to parse LLM response as JSON. "
            "The model may not have followed the JSON format instructions. "
            "Please try again."
        )

    def _check_anti_patterns(self, code: str) -> tuple[bool, str]:
        """
        Check for common anti-patterns in generated code.

        Scans the code for hardcoded paths and other problematic patterns
        that the LLM might introduce from its training data.

        Args:
            code: The generated Python code

        Returns:
            tuple: (is_valid, error_message)
        """
        # Define anti-patterns: (regex_pattern, human_readable_description)
        anti_patterns = [
            # Hardcoded directories commonly found in web apps
            (r"['\"]static/['\"]", "hardcoded 'static/' directory path"),
            (r"['\"]static\\['\"]", "hardcoded 'static\\' directory path"),
            (r"['\"]output/['\"]", "hardcoded 'output/' directory path"),
            (r"['\"]outputs/['\"]", "hardcoded 'outputs/' directory path"),
            (r"['\"]temp/['\"]", "hardcoded 'temp/' directory path"),
            (r"['\"]tmp/['\"]", "hardcoded 'tmp/' directory path"),
            (r"['\"]data/['\"]", "hardcoded 'data/' directory path"),

            # Path operations creating these directories
            (r"mkdir\(['\"]static", "creating 'static' directory"),
            (r"makedirs\(['\"]static", "creating 'static' directory"),
            (r"Path\(['\"]static", "using 'static' Path"),

            # Check for common web app patterns that shouldn't be here
            (r"app\.static_folder", "Flask static_folder reference"),
            (r"static_folder\s*=", "setting static_folder"),

            # Check for relative path usage in file outputs
            (r"open\(['\"]\w+/", "opening file with relative path (use absolute paths)"),

            # Check for improper use of HOME or user directory patterns
            (r"~/?static", "user directory with 'static'"),
        ]

        for pattern, description in anti_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return False, f"Forbidden pattern detected: {description}. Use ~/Downloads/<script_name_slug>/timestamp_output/ for all outputs."

        return True, ""

    def _validate_script(self, code: str) -> tuple[bool, str]:
        """
        Validate the generated script structure without executing imports.

        Uses AST parsing to check for required variables and functions
        without actually importing external packages.

        Args:
            code: The generated Python code

        Returns:
            tuple: (is_valid, error_message)
        """
        import ast

        # First, check for anti-patterns
        is_clean, anti_pattern_error = self._check_anti_patterns(code)
        if not is_clean:
            return False, anti_pattern_error

        # Check for required module-level variables
        required_vars = {"NAME", "DESCRIPTION", "INPUT_TYPES", "PARAMETERS"}
        required_functions = {"main", "process_files"}

        try:
            # Parse the code into an AST
            tree = ast.parse(code)

            # Check syntax is valid
            # Find all top-level assignments and function definitions
            found_vars = set()
            found_functions = set()

            for node in ast.walk(tree):
                # Look for top-level variable assignments
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            found_vars.add(target.id)
                # Look for function definitions
                elif isinstance(node, ast.FunctionDef):
                    found_functions.add(node.name)

            # Check required variables
            missing_vars = required_vars - found_vars
            if missing_vars:
                return False, f"Missing required variable(s): {', '.join(missing_vars)}"

            # Check required functions
            missing_funcs = required_functions - found_functions
            if missing_funcs:
                return False, f"Missing required function(s): {', '.join(missing_funcs)}"

            # Additional checks by trying to compile (but not execute)
            try:
                compile(code, "<string>", "exec")
            except SyntaxError as e:
                return False, f"Syntax error: {e}"

            return True, ""

        except SyntaxError as e:
            return False, f"Syntax error: {e}"
        except Exception as e:
            return False, f"Validation error: {e}"

    def _extract_metadata(self, code: str) -> tuple[str, str]:
        """
        Extract NAME and DESCRIPTION from code without executing imports.

        Uses AST parsing to safely extract string values from assignments.

        Args:
            code: The generated Python code

        Returns:
            tuple: (name, description)
        """
        import ast

        try:
            tree = ast.parse(code)

            # Try to find NAME and DESCRIPTION in top-level assignments
            name = "Generated Script"
            description = "No description"

            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id
                            # Check if this is a NAME assignment
                            if var_name == "NAME" and isinstance(node.value, ast.Constant):
                                if isinstance(node.value.value, str):
                                    name = node.value.value
                            # Check if this is a DESCRIPTION assignment
                            elif var_name == "DESCRIPTION" and isinstance(node.value, ast.Constant):
                                if isinstance(node.value.value, str):
                                    description = node.value.value

            return name, description

        except Exception:
            # Fallback to defaults if parsing fails
            return "Generated Script", "No description"

    def detect_external_packages(self, code: str) -> list[str]:
        """
        Detect external Python packages used in the generated code.

        Scans import statements to identify packages that are not
        part of Python's standard library.

        Args:
            code: The generated Python code

        Returns:
            List of external package names that need to be installed
        """
        import ast

        # Standard library modules (not exhaustive, but covers common ones)
        STANDARD_LIB = {
            'os', 'sys', 're', 'json', 'csv', 'datetime', 'time', 'pathlib',
            'argparse', 'subprocess', 'threading', 'multiprocessing',
            'collections', 'itertools', 'functools', 'operator', 'typing',
            'math', 'random', 'string', 'io', 'hashlib', 'base64',
            'urllib', 'http', 'socket', 'ssl', 'ftplib', 'smtplib',
            'textwrap', 'difflib', 'pprint', 'enum', 'dataclasses',
            'typing_extensions', 'contextlib', 'warnings', 'inspect',
            'importlib', 'pkgutil', 'sysconfig', 'platform', 'shutil',
            'tempfile', 'zipfile', 'tarfile', 'gzip', 'bz2', 'lzma',
            'logging', 'unittest', 'pdb', 'traceback', 'queue',
        }

        # Packages that are likely already installed as app dependencies
        # Don't warn users about these
        LIKELY_INSTALLED = {'PIL', 'Pillow', 'customtkinter', 'tkinter'}

        external_packages = []

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        # Get the top-level package name
                        package_name = alias.name.split('.')[0]
                        if package_name not in STANDARD_LIB and package_name not in LIKELY_INSTALLED:
                            external_packages.append(package_name)

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        # Get the top-level package name
                        package_name = node.module.split('.')[0]
                        if package_name not in STANDARD_LIB and package_name not in LIKELY_INSTALLED:
                            external_packages.append(package_name)

            # Remove duplicates and return sorted list
            return sorted(set(external_packages))

        except Exception:
            return []

    def generate_script(
        self,
        user_prompt: str,
        existing_script: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, str]:
        """
        Generate or edit a script using the LLM with automatic retry on validation failure.

        Args:
            user_prompt: User's description of what they want
            existing_script: For edit mode, the current script code
            progress_callback: Optional callback(attempt_number, max_attempts) for progress updates

        Returns:
            dict: {
                "code": full script code,
                "name": suggested script name,
                "description": what the script does
            }

        Raises:
            APIError: If API communication fails
            ValidationError: If generated script fails validation after all retry attempts
        """
        mode = "edit" if existing_script else "create"

        # Store the initial prompt for retries
        original_user_prompt = user_prompt

        for attempt in range(1, MAX_RETRIES + 1):
            # Notify progress callback
            if progress_callback:
                progress_callback(attempt, MAX_RETRIES)

            # Build the prompt
            if attempt == 1:
                # First attempt - use original prompt
                if mode == "edit":
                    prompt = EDIT_TEMPLATE.format(
                        existing_script=existing_script,
                        user_prompt=user_prompt
                    )
                else:
                    prompt = CREATE_TEMPLATE.format(user_prompt=user_prompt)
            else:
                # Retry attempt - use retry template with previous code and error
                prompt = RETRY_TEMPLATE.format(
                    user_prompt=original_user_prompt,
                    previous_code=self.last_generated_code,
                    error_message=self.last_validation_error
                )

            messages = [
                {
                    "role": "system",
                    "content": "You are an expert Python developer. Always respond with valid JSON only, no explanations. Follow the exact JSON format specified in the prompt."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            try:
                # Call the API
                response = self._make_api_request(messages)

                # Parse JSON response
                if mode == "create":
                    # For create mode, expect JSON with code, name, description, packages
                    try:
                        data = self._parse_json_response(response)
                        code = data.get("code", "")
                        name = data.get("name", "Generated Script")
                        description = data.get("description", "No description")
                        packages = data.get("packages", [])
                    except APIError:
                        # Fallback: treat as code-only response if JSON parsing fails
                        code = self._extract_code_from_response(response)
                        name, description = self._extract_metadata(code)
                        packages = self.detect_external_packages(code)
                else:
                    # For edit mode, still expect code-only (for now)
                    code = self._extract_code_from_response(response)
                    name, description = self._extract_metadata(code)
                    packages = self.detect_external_packages(code)

                # Store for potential retry
                self.last_generated_code = code

                # Validate the generated script
                is_valid, error_msg = self._validate_script(code)

                if is_valid:
                    # Success! Return all the data
                    return {
                        "code": code,
                        "name": name,
                        "description": description,
                        "packages": packages
                    }
                else:
                    # Validation failed - store error for retry
                    self.last_validation_error = error_msg

                    if attempt >= MAX_RETRIES:
                        # Last attempt failed - raise error
                        raise ValidationError(
                            f"Failed to generate valid script after {MAX_RETRIES} attempts.\n"
                            f"Last error: {error_msg}\n\n"
                            f"The AI model struggled to create a valid script. "
                            f"Please try rephrasing your request or try again."
                        )
                    # Otherwise, continue to next attempt (retry)

            except APIError:
                # API errors should not trigger retries - re-raise immediately
                raise

    @staticmethod
    def sanitize_filename(name: str) -> str:
        """
        Convert a script name to a valid filename.

        Args:
            name: Script name (e.g., "Background Remover")

        Returns:
            str: Sanitized filename (e.g., "background_remover")
        """
        # Convert to lowercase and replace spaces with underscores
        sanitized = name.lower().replace(" ", "_")
        # Remove any non-alphanumeric characters except underscore
        sanitized = re.sub(r'[^a-z0-9_]', '', sanitized)
        return sanitized
