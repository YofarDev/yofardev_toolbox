"""Script execution and process management."""
import subprocess
import threading
import os
import sys
import datetime
import re
import shutil
import json
from pathlib import Path
from typing import List, Dict, Callable, Optional, Tuple


def _get_project_dir() -> str:
    """Get the project directory path."""
    # Get the directory containing this file (core/script_executor.py)
    # Then go up to the project root
    return str(Path(__file__).parent.parent.resolve())


def _get_uv_executable() -> str:
    """Get the uv executable path."""
    # Try to find uv in PATH
    uv_path = shutil.which("uv")
    if uv_path:
        return uv_path
    # Fallback to common locations
    for path in ["/opt/homebrew/bin/uv", "/usr/local/bin/uv"]:
        if os.path.exists(path):
            return path
    return "uv"  # Fallback to just "uv" and hope it's in PATH


def is_package_installed(package_name: str) -> bool:
    """
    Check if a Python package is already installed in the project.

    Args:
        package_name: Name of the package to check (e.g., 'pydub', 'Pillow')

    Returns:
        True if package is installed, False otherwise
    """
    try:
        uv = _get_uv_executable()
        project_dir = _get_project_dir()
        # Use uv pip list with --directory to target the project's virtual environment
        result = subprocess.run(
            [uv, "pip", "list", "--directory", project_dir, "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            installed_packages = json.loads(result.stdout)
            installed_names = {pkg['name'].lower() for pkg in installed_packages}
            return package_name.lower() in installed_names
    except Exception:
        pass

    # Fallback: try to import the package
    try:
        import importlib
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False


def detect_missing_package(error_output: str) -> Optional[str]:
    """
    Detect if an error is due to a missing Python package and extract the package name.

    Args:
        error_output: The error output from script execution

    Returns:
        Package name if missing import detected, None otherwise
    """
    # Pattern for ModuleNotFoundError: No module named 'package_name'
    module_pattern = r"ModuleNotFoundError.*?No module named ['\"]([^'\"]+)['\"]"
    match = re.search(module_pattern, error_output)
    if match:
        return match.group(1)

    # Pattern for ImportError: No module named 'package_name'
    import_pattern = r"ImportError.*?No module named ['\"]([^'\"]+)['\"]"
    match = re.search(import_pattern, error_output)
    if match:
        return match.group(1)

    # Pattern for: cannot import name 'X' from partially initialized module 'Y' (most likely due to a circular import)
    # Pattern for missing libraries in some packages
    lib_pattern = r"library.*?([a-zA-Z0-9_-]+)\.so.*?not found"
    match = re.search(lib_pattern, error_output)
    if match:
        # Try to map library name to package name
        lib_name = match.group(1)
        # Common mappings
        mappings = {
            'PIL': 'Pillow',
            'cv2': 'opencv-python',
            'cv2.cv2': 'opencv-python-headless',
            'PIL._imaging': 'Pillow',
            'yaml': 'PyYAML',
            'bs4': 'beautifulsoup4',
            'tkinter': 'python-tk',
        }
        return mappings.get(lib_name, lib_name)

    return None


def get_install_command(package_name: str) -> str:
    """
    Get the installation command for a package.

    Args:
        package_name: Name of the missing package

    Returns:
        Installation command string (e.g., "uv add pydub")
    """
    # Map common package names to their pip/uv install names
    mappings = {
        'cv2': 'opencv-python',
        'cv2.cv2': 'opencv-python-headless',
        'PIL': 'Pillow',
        'yaml': 'PyYAML',
        'bs4': 'beautifulsoup4',
        'fitz': 'pymupdf',  # PyMuPDF is installed as pymupdf, imported as fitz
    }

    install_name = mappings.get(package_name, package_name)
    uv = _get_uv_executable()
    project_dir = _get_project_dir()
    return f"{uv} add --directory {project_dir} {install_name}"


def get_install_command_list(package_name: str) -> List[str]:
    """
    Get the installation command for a package as a list.

    Args:
        package_name: Name of the missing package

    Returns:
        Installation command as a list of arguments
    """
    # Map common package names to their pip/uv install names
    mappings = {
        'cv2': 'opencv-python',
        'cv2.cv2': 'opencv-python-headless',
        'PIL': 'Pillow',
        'yaml': 'PyYAML',
        'bs4': 'beautifulsoup4',
        'fitz': 'pymupdf',  # PyMuPDF is installed as pymupdf, imported as fitz
    }

    install_name = mappings.get(package_name, package_name)
    uv = _get_uv_executable()
    project_dir = _get_project_dir()
    return [uv, "add", "--directory", project_dir, install_name]


def get_installed_packages() -> Dict[str, str]:
    """
    Get a dictionary of all installed packages and their versions in the project.

    Returns:
        Dict mapping package names (lowercase) to version strings
    """
    try:
        uv = _get_uv_executable()
        project_dir = _get_project_dir()
        result = subprocess.run(
            [uv, "pip", "list", "--directory", project_dir, "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            packages = json.loads(result.stdout)
            return {pkg['name'].lower(): pkg['version'] for pkg in packages}
    except Exception as e:
        print(f"Error getting installed packages: {e}")
    return {}


class ScriptExecutor:
    """Manages script execution in subprocesses."""

    def __init__(self,
                 output_callback: Callable[[str], None],
                 finished_callback: Callable[[int, Optional[str]], None],
                 install_callback: Optional[Callable[[str, str], None]] = None):
        """
        Initialize the script executor.

        Args:
            output_callback: Function to call with each line of output
            finished_callback: Function to call when process finishes (returncode, output_dir)
            install_callback: Optional function to call when package needs installation (package_name, install_command)
        """
        self.output_callback = output_callback
        self.finished_callback = finished_callback
        self.install_callback = install_callback
        self.current_process: Optional[subprocess.Popen] = None

    def execute(self,
                script_path: str,
                file_paths: List[str],
                params: Dict[str, any],
                script_config: Dict) -> Tuple[int, Optional[str]]:
        """
        Execute a script with given parameters.

        Args:
            script_path: Path to the script file
            file_paths: List of input file paths
            params: Dictionary of parameter name -> value
            script_config: Script configuration dict (for output dir calculation)

        Returns:
            None (runs in background thread)
        """
        # Build output directory path
        script_name_slug = script_config["name"].lower().replace(" ", "_")
        downloads_dir = os.path.expanduser("~/Downloads")
        output_dir = os.path.join(downloads_dir, script_name_slug)
        os.makedirs(output_dir, exist_ok=True)

        # Build command
        command = self.build_command(script_path, file_paths, params, script_config, output_dir)

        # Run in background thread
        thread = threading.Thread(
            target=self._run_process,
            args=(command, output_dir),
            daemon=True
        )
        thread.start()

    def build_command(self,
                     script_path: str,
                     file_paths: List[str],
                     params: Dict[str, any],
                     script_config: Dict,
                     output_dir: str) -> List[str]:
        """
        Build the command line for script execution.

        Args:
            script_path: Path to the script file
            file_paths: List of input file paths
            params: Dictionary of parameter name -> value
            script_config: Script configuration dict
            output_dir: Output directory path

        Returns:
            List of command arguments
        """
        command = ["python", script_path]

        if not script_config.get("accepts_multiple_files", True):
            # Single file mode: script + input_file + output_path
            if file_paths:
                command.append(file_paths[0])
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(output_dir, f"{timestamp}.jpg")
            command.append(output_path)
        else:
            # Multiple file mode: script + file1 + file2 + ...
            command.extend(file_paths)

        # Add parameters
        for name, value in params.items():
            param_def = next(
                (p for p in script_config["parameters"] if p["name"] == name),
                None
            )
            if param_def and param_def["type"] in ["boolean", "bool"]:
                if value:  # Only add if True
                    command.append(f"--{name}")
            else:
                command.append(f"--{name}")
                command.append(str(value))

        return command

    def _run_process(self, command: List[str], output_dir: str):
        """Run the process and stream output."""
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            self.current_process = process

            # Accumulate stderr for error detection
            stderr_output = []

            def read_stream(stream):
                for line in iter(stream.readline, ""):
                    if line:
                        self.output_callback("  " + line)  # Indent output
                stream.close()

            def read_stderr(stream):
                for line in iter(stream.readline, ""):
                    if line:
                        self.output_callback("  " + line)  # Indent output
                        stderr_output.append(line)
                stream.close()

            # Read streams
            read_stream(process.stdout)
            read_stderr(process.stderr)

            process.wait()

            # Check for missing packages if process failed
            if process.returncode != 0 and stderr_output:
                combined_error = "".join(stderr_output)
                missing_package = detect_missing_package(combined_error)

                if missing_package:
                    # Get install command
                    install_cmd = get_install_command(missing_package)

                    # If we have an install callback, use it; otherwise show manual instructions
                    if self.install_callback:
                        # Trigger auto-install via callback
                        # Pass a no-op callback for completion notification
                        def on_install_complete():
                            pass

                        self.install_callback(missing_package, install_cmd, on_install_complete)
                    else:
                        # Manual installation fallback
                        self.output_callback("\n" + "=" * 60)
                        self.output_callback("❌ Missing Python Package")
                        self.output_callback("=" * 60)
                        self.output_callback(f"\nThe script requires the '{missing_package}' package.")
                        self.output_callback(f"\n📦 To install it, run:")
                        self.output_callback(f"\n   {install_cmd}")
                        self.output_callback(f"\n🔄 Then relaunch the app to use the newly installed package.")
                        self.output_callback("\n" + "=" * 60)

            # Call finished callback
            self.finished_callback(process.returncode, output_dir)

        except Exception as e:
            self.output_callback(f"\nERROR: {e}\n")
            self.finished_callback(-1, None)

    def stop(self) -> bool:
        """
        Stop the currently running script.

        Returns:
            True if a process was stopped, False otherwise
        """
        if self.current_process:
            try:
                self.current_process.terminate()
                # Give process a moment to terminate gracefully, then kill
                try:
                    self.current_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.current_process.kill()

                self.current_process = None
                return True
            except Exception as e:
                self.output_callback(f"\nERROR stopping script: {e}\n")
                return False
        return False

    def is_running(self) -> bool:
        """Check if a process is currently running."""
        return self.current_process is not None


def open_output_folder(path: str) -> bool:
    """
    Open a folder in the system file manager.

    Args:
        path: Path to the folder

    Returns:
        True if successful, False otherwise
    """
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        return True
    except Exception:
        return False
