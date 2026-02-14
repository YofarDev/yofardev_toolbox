"""LLM-based script editing functionality."""
import os
from typing import Optional, Tuple
from config import get_current_llm


# Script template for new/editing scripts
SCRIPT_TEMPLATE = '''import os
import datetime
import argparse
from pathlib import Path

# --- Core Components for UI ---

NAME = ""
DESCRIPTION = ""
INPUT_TYPES = ""

PARAMETERS = []

# --- Script Logic ---

def process_files(file_paths, **kwargs):
    """
    Main processing logic.
    """
    # Your processing code here
    print(f"Processing {len(file_paths)} files...")

# --- Command-Line Execution ---

def main():
    """
    Parses command-line arguments and runs the script.
    """
    parser = argparse.ArgumentParser(description=DESCRIPTION)

    # Default argument for input files
    parser.add_argument("file_paths", nargs="+", help="Paths to input files to process.")

    # Add arguments for each parameter defined in PARAMETERS
    for param in PARAMETERS:
        parser.add_argument(
            f'--{param["name"]}',
            type=eval(param["type"]),
            default=param["default"],
            help=f'Default: {param["default"]}'
        )

    args = parser.parse_args()

    # Convert argument names to a dictionary of keyword arguments
    kwargs = {param["name"]: getattr(args, param["name"]) for param in PARAMETERS}

    process_files(args.file_paths, **kwargs)

if __name__ == "__main__":
    main()
'''


class LLMScriptEditor:
    """Handles LLM-based script editing."""

    def __init__(self):
        self.api_key = None
        self.model = None
        self._load_config()

    def _load_config(self):
        """Load LLM configuration from settings."""
        llm_config = get_current_llm()

        if llm_config:
            self.api_key = llm_config.get("api_key", "")
            self.model = llm_config.get("model", "")
        else:
            self.api_key = ""
            self.model = ""

    def is_configured(self) -> bool:
        """Check if LLM is properly configured."""
        return bool(self.api_key and self.model)

    def edit_script(
        self,
        original_code: str,
        user_request: str,
        current_metadata: dict
    ) -> Tuple[bool, str, str]:
        """
        Request LLM to edit a script based on user request.

        Args:
            original_code: Current script code
            user_request: User's change request
            current_metadata: Script metadata (NAME, DESCRIPTION, etc.)

        Returns:
            Tuple of (success, modified_code, error_message)
        """
        if not self.is_configured():
            return False, "", "LLM not configured. Please check settings."

        # Build the prompt
        prompt = self._build_edit_prompt(
            original_code,
            user_request,
            current_metadata
        )

        # Import API client based on model
        try:
            if "gemini" in self.model.lower():
                from core.gemini_client import GeminiClient
                client = GeminiClient(self.api_key, self.model)
                response = client.generate_script(prompt)
                return True, response, ""
            elif "openai" in self.model.lower() or "gpt" in self.model.lower():
                from core.openai_client import OpenAIClient
                client = OpenAIClient(self.api_key, self.model)
                response = client.generate_script(prompt)
                return True, response, ""
            else:
                # Try generic OpenAI-compatible endpoint
                from core.openai_client import OpenAIClient
                client = OpenAIClient(self.api_key, self.model)
                response = client.generate_script(prompt)
                return True, response, ""

        except Exception as e:
            return False, "", f"Error generating script: {str(e)}"

    def _build_edit_prompt(
        self,
        original_code: str,
        user_request: str,
        current_metadata: dict
    ) -> str:
        """Build the prompt for LLM script editing."""
        prompt = f"""You are an expert Python developer specializing in image processing scripts.

# Current Task
The user wants to modify an existing script with this request:
"{user_request}"

# Original Script Metadata
- Name: {current_metadata.get('name', 'Unknown')}
- Description: {current_metadata.get('description', 'Unknown')}

# Original Script Code
```python
{original_code}
```

# Script Template Reference
This is the expected structure for scripts in this application:

```python
{SCRIPT_TEMPLATE}
```

# Instructions
1. Modify the original script to fulfill the user's request
2. Maintain the existing structure with NAME, DESCRIPTION, INPUT_TYPES, and PARAMETERS
3. Keep the process_files() function signature intact
4. Keep the main() function for command-line execution
5. Ensure all imports are included
6. Output the COMPLETE modified script code only - no explanations, no markdown code blocks
7. The script should be ready to save and run directly

Return only the complete Python code, nothing else.
"""
        return prompt
