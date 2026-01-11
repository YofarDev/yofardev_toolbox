"""Script execution and process management."""
import subprocess
import threading
import os
import sys
import datetime
from typing import List, Dict, Callable, Optional, Tuple


class ScriptExecutor:
    """Manages script execution in subprocesses."""

    def __init__(self,
                 output_callback: Callable[[str], None],
                 finished_callback: Callable[[int, Optional[str]], None]):
        """
        Initialize the script executor.

        Args:
            output_callback: Function to call with each line of output
            finished_callback: Function to call when process finishes (returncode, output_dir)
        """
        self.output_callback = output_callback
        self.finished_callback = finished_callback
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

            def read_stream(stream):
                for line in iter(stream.readline, ""):
                    if line:
                        self.output_callback("  " + line)  # Indent output
                stream.close()

            # Read streams
            read_stream(process.stdout)
            read_stream(process.stderr)

            process.wait()

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
