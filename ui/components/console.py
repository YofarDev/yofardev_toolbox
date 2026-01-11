"""Console output widget."""
import customtkinter as ctk
from config.themes import COLORS


class Console(ctk.CTkTextbox):
    """Console output display with streaming support."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            font=("Consolas", 13),
            fg_color="#0f0f0f",
            text_color="#dcdcdc",
            border_width=1,
            border_color=COLORS["border"],
            activate_scrollbars=True,
            **kwargs
        )
        self.insert("1.0", "Waiting for input...\n")
        self.configure(state="disabled")

    def log(self, message: str, level: str = "info"):
        """
        Log a message to the console.

        Args:
            message: Message to log
            level: Log level (info, error, warning, etc.)
        """
        self.configure(state="normal")
        if level == "error":
            self.insert("end", f"ERROR: {message}\n")
        else:
            self.insert("end", f"{message}\n")
        self.see("end")
        self.configure(state="disabled")

    def clear(self):
        """Clear the console."""
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.insert("1.0", "")
        self.configure(state="disabled")

    def append_stream(self, text: str):
        """
        Append streamed output.

        Args:
            text: Text to append
        """
        self.configure(state="normal")
        self.insert("end", text)
        self.see("end")
        self.configure(state="disabled")

    def initialize_script(self, script_name: str, output_path: str):
        """
        Initialize console for a new script run.

        Args:
            script_name: Name of the script being run
            output_path: Output directory path
        """
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.insert("end", f"> Initializing {script_name}...\n")
        self.insert("end", f"> Output Path: {output_path}\n\n")
        self.see("end")
        self.configure(state="disabled")

    def show_success(self, output_dir: str = None):
        """
        Show success message.

        Args:
            output_dir: Output directory to show (optional)
        """
        self.configure(state="normal")
        self.insert("end", "\n> SUCCESS: Task completed.\n")
        if output_dir:
            self.insert("end", "> Opening output folder...\n")
        self.see("end")
        self.configure(state="disabled")

    def show_failure(self, return_code: int):
        """
        Show failure message.

        Args:
            return_code: Process exit code
        """
        self.configure(state="normal")
        self.insert("end", f"\n> FAILED: Exit code {return_code}.\n")
        self.see("end")
        self.configure(state="disabled")
