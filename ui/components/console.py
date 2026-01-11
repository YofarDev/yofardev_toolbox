"""Console output widget."""
import customtkinter as ctk
import subprocess
import threading
import os
from config.themes import COLORS
from core.script_executor import get_install_command


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

    def show_install_button(self, package_name: str, install_command: str, on_install):
        """
        Show auto-install button for missing package.

        Args:
            package_name: Name of the missing package
            install_command: Installation command (e.g., "uv add package")
            on_install: Callback when user clicks install
        """
        # Remove existing install frame if present
        if hasattr(self, 'install_frame') and self.install_frame:
            self.install_frame.destroy()

        # The console's master is bottom_frame
        bottom_frame = self.master
        if not bottom_frame:
            return

        # Find the action_bar (first child of bottom_frame that's a CTkFrame and not the console)
        action_bar = None
        for child in bottom_frame.winfo_children():
            if isinstance(child, ctk.CTkFrame) and child != self:
                action_bar = child
                break

        if not action_bar:
            return

        # Create install frame - pack it into the action_bar (which uses pack)
        self.install_frame = ctk.CTkFrame(action_bar, fg_color=COLORS["bg_card"], corner_radius=6)
        self.install_frame.pack(fill="x", pady=(10, 0))

        # Message
        msg_label = ctk.CTkLabel(
            self.install_frame,
            text=f"❌ Missing package: {package_name}",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["danger"],
            anchor="w"
        )
        msg_label.pack(fill="x", padx=10, pady=(8, 4))

        # Instructions
        info_label = ctk.CTkLabel(
            self.install_frame,
            text=f"Install {package_name} to use this script",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_sub"],
            anchor="w"
        )
        info_label.pack(fill="x", padx=10, pady=(0, 8))

        # Button frame
        btn_frame = ctk.CTkFrame(self.install_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0, 8))

        # Install button
        install_btn = ctk.CTkButton(
            btn_frame,
            text=f"📦 Auto-install",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            height=36,
            command=lambda: self._install_package(package_name, install_command, on_install, install_btn)
        )
        install_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        # Dismiss button
        dismiss_btn = ctk.CTkButton(
            btn_frame,
            text="Dismiss",
            width=100,
            height=36,
            font=ctk.CTkFont(size=11),
            fg_color=COLORS["bg_root"],
            hover_color=COLORS["border"],
            text_color=COLORS["text_main"],
            command=lambda: self._hide_install_frame()
        )
        dismiss_btn.pack(side="right")

    def _install_package(self, package_name: str, install_command: str, on_install, button):
        """Install the package in a background thread."""
        button.configure(state="disabled", text="⏳ Installing...")
        self.configure(state="normal")
        self.insert("end", f"\n> Installing {package_name}...\n")
        self.configure(state="disabled")
        self.see("end")

        def run_install():
            try:
                # Run uv add command
                result = subprocess.run(
                    install_command.split(),
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode == 0:
                    # Success
                    self.after(0, lambda: self._install_success(package_name))
                else:
                    # Failure
                    stderr = result.stderr if result.stderr else result.stdout
                    self.after(0, lambda: self._install_error(package_name, stderr))
            except subprocess.TimeoutExpired:
                self.after(0, lambda: self._install_error(package_name, "Installation timed out"))
            except Exception as e:
                self.after(0, lambda: self._install_error(package_name, str(e)))
            finally:
                # Always call the completion callback
                on_install()

        thread = threading.Thread(target=run_install, daemon=True)
        thread.start()

    def _install_success(self, package_name: str):
        """Handle successful installation."""
        self.configure(state="normal")
        self.insert("end", f"✓ {package_name} installed successfully!\n")
        self.insert("end", "\n" + "=" * 60 + "\n")
        self.insert("end", "🔄 Please relaunch the app to use the new package.\n")
        self.insert("end", "=" * 60 + "\n")
        self.see("end")
        self.configure(state="disabled")

        # Change the button to show success
        if hasattr(self, 'install_frame') and self.install_frame:
            for widget in self.install_frame.winfo_children():
                if isinstance(widget, ctk.CTkButton):
                    if "Dismiss" not in widget.cget("text"):
                        widget.configure(
                            state="disabled",
                            text="✓ Installed - Relaunch app",
                            fg_color=COLORS["success"],
                            hover_color=COLORS["success_hover"]
                        )

    def _install_error(self, package_name: str, error_msg: str):
        """Handle installation error."""
        self.configure(state="normal")
        self.insert("end", f"\n❌ Installation failed:\n{error_msg}\n")
        self.insert("end", f"\n📦 Please run manually: {get_install_command(package_name)}\n")
        self.see("end")
        self.configure(state="disabled")

        # Re-enable the install button
        if hasattr(self, 'install_frame') and self.install_frame:
            for widget in self.install_frame.winfo_children():
                if isinstance(widget, ctk.CTkButton):
                    if "Dismiss" not in widget.cget("text"):
                        widget.configure(state="normal", text=f"📦 Auto-install with: {get_install_command(package_name)}")

    def _hide_install_frame(self):
        """Hide the install frame."""
        if hasattr(self, 'install_frame') and self.install_frame:
            self.install_frame.destroy()
            self.install_frame = None
