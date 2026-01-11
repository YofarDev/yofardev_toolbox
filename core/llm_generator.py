"""
LLM-powered script generator for Yofardev Toolbox.

Handles communication with OpenAI-compatible APIs to generate and edit scripts.
"""
import requests
import re
import ast
from typing import Optional, Dict


# Prompt templates for script generation

CREATE_TEMPLATE = """You are an expert Python developer specializing in image processing scripts using PIL/Pillow.

TASK: Create a new image processing script based on the user's request.

USER REQUEST: {user_prompt}

REQUIREMENTS:
1. The script must follow this exact template structure:

```python
import os
import datetime
import argparse
from pathlib import Path
from PIL import Image

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

2. OUTPUT ONLY valid Python code - no explanations outside the code
3. Include all required imports at the top
4. Save outputs to ~/Downloads/<script_name_slug>/<timestamp>_output/
5. Handle errors gracefully with try/except blocks for each file
6. Print progress messages to console for each file processed
7. Follow the exact pattern shown above - maintain the same structure
8. Use PIL/Pillow for image operations
9. Choose appropriate NAME and DESCRIPTION based on what the script does
10. Define sensible PARAMETERS that the user can configure

Respond with ONLY the Python code, nothing else. Do not include markdown code blocks, just the raw Python code.
"""

EDIT_TEMPLATE = """You are an expert Python developer specializing in image processing scripts.

TASK: Modify the existing script based on the user's request.

EXISTING SCRIPT:
```python
{existing_script}
```

USER REQUEST: {user_prompt}

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
        Extract Python code from the LLM response.

        Handles responses that may or may not include markdown code blocks.

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

    def _validate_script(self, code: str) -> tuple[bool, str]:
        """
        Validate the generated script.

        Args:
            code: The generated Python code

        Returns:
            tuple: (is_valid, error_message)
        """
        # Check for required module-level variables
        required_vars = ["NAME", "DESCRIPTION", "INPUT_TYPES", "PARAMETERS"]

        # Try to compile and execute in a safe namespace
        namespace = {}
        try:
            compiled = compile(code, "<string>", "exec")
            exec(compiled, namespace)

            # Check required variables
            for var in required_vars:
                if var not in namespace:
                    return False, f"Missing required variable: {var}"

            # Check that NAME is a non-empty string
            if not isinstance(namespace.get("NAME"), str) or not namespace["NAME"].strip():
                return False, "NAME must be a non-empty string"

            # Check that PARAMETERS is a list
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

    def generate_script(self, user_prompt: str, existing_script: Optional[str] = None) -> Dict[str, str]:
        """
        Generate or edit a script using the LLM.

        Args:
            user_prompt: User's description of what they want
            existing_script: For edit mode, the current script code

        Returns:
            dict: {
                "code": full script code,
                "name": suggested script name,
                "description": what the script does
            }

        Raises:
            APIError: If API communication fails
            ValidationError: If generated script fails validation
        """
        mode = "edit" if existing_script else "create"

        # Build the prompt
        if mode == "edit":
            prompt = EDIT_TEMPLATE.format(
                existing_script=existing_script,
                user_prompt=user_prompt
            )
        else:
            prompt = CREATE_TEMPLATE.format(user_prompt=user_prompt)

        messages = [
            {
                "role": "system",
                "content": "You are an expert Python developer. Always respond with valid Python code only, no explanations."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        # Call the API
        response = self._make_api_request(messages)

        # Extract code from response
        code = self._extract_code_from_response(response)

        # Validate the generated script
        is_valid, error_msg = self._validate_script(code)

        if not is_valid:
            raise ValidationError(
                f"Generated script failed validation:\n{error_msg}\n\n"
                f"You can try regenerating or edit the script manually."
            )

        # Extract metadata from the code
        namespace = {}
        exec(compile(code, "<string>", "exec"), namespace)

        name = namespace.get("NAME", "Generated Script")
        description = namespace.get("DESCRIPTION", "No description")

        return {
            "code": code,
            "name": name,
            "description": description
        }

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
