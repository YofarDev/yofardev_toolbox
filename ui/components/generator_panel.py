"""LLM script generator panel - simplified version for refactored app."""
import customtkinter as ctk
import os
import threading
import subprocess
from config.themes import COLORS
from config import get_config
from core.llm_generator import ScriptGenerator, GenerationError, APIError, ValidationError
from core.script_executor import get_install_command


class GeneratorPanel(ctk.CTkFrame):
    """Panel for generating scripts with LLM."""

    def __init__(self, master, scripts, on_complete, on_cancel):
        """
        Initialize the generator panel.

        Args:
            master: Parent widget
            scripts: List of available scripts
            on_complete: Callback when generation completes (script_filename)
            on_cancel: Callback when user cancels
        """
        super().__init__(master, fg_color="transparent")
        self.scripts = scripts
        self.on_complete = on_complete
        self.on_cancel = on_cancel
        self.generator_widgets = {}

        self.create_widgets()

    def log(self, message):
        """Log a message to the internal log textbox."""
        if hasattr(self, 'log_text'):
            self.log_text.configure(state="normal")
            self.log_text.insert("end", message + "\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")

    def create_widgets(self):
        """Create generator UI widgets."""
        # Header
        header = ctk.CTkLabel(
            self,
            text="🤖 Generate New Script",
            font=ctk.CTkFont(family="Roboto", size=24, weight="bold"),
            text_color=COLORS["text_main"],
            anchor="w"
        )
        header.pack(fill="x", pady=(0, 5))

        desc = ctk.CTkLabel(
            self,
            text="Describe the batch processing script you want to create",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_sub"],
            anchor="w"
        )
        desc.pack(fill="x", pady=(0, 20))

        # Status indicator (hidden by default)
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.pack(fill="x", pady=(0, 15))

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_sub"],
            anchor="w"
        )
        self.status_label.pack(side="left", padx=(0, 10))

        self.progress_bar = ctk.CTkProgressBar(
            self.status_frame,
            width=200,
            height=8,
            progress_color=COLORS["accent"],
            fg_color=COLORS["bg_root"]
        )
        self.progress_bar.pack(side="left", padx=(0, 10))
        self.progress_bar.set(0)

        self.spinner_label = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=ctk.CTkFont(size=16),
            text_color=COLORS["accent"]
        )
        self.spinner_label.pack(side="left")

        self.spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_index = 0
        self.spinner_running = False

        # Log area for generation feedback
        log_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=8)
        log_frame.pack(fill="x", pady=(0, 15))

        log_header = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_header.pack(fill="x", padx=15, pady=(10, 5))
        ctk.CTkLabel(
            log_header,
            text="Generation Log",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text_main"]
        ).pack(side="left")

        self.log_text = ctk.CTkTextbox(
            log_frame,
            fg_color=COLORS["bg_root"],
            border_color=COLORS["border"],
            font=ctk.CTkFont(size=11, family="Consolas"),
            height=100,
            activate_scrollbars=False
        )
        self.log_text.pack(fill="x", padx=15, pady=(0, 15))
        self.log_text.configure(state="disabled")

        # Prompt input
        prompt_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=8)
        prompt_frame.pack(fill="both", expand=True, pady=(0, 15))

        prompt_header = ctk.CTkFrame(prompt_frame, fg_color="transparent")
        prompt_header.pack(fill="x", padx=15, pady=(10, 5))
        ctk.CTkLabel(
            prompt_header,
            text="Your Prompt",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_main"]
        ).pack(side="left")

        self.prompt_text = ctk.CTkTextbox(
            prompt_frame,
            fg_color=COLORS["bg_root"],
            border_color=COLORS["border"],
            font=ctk.CTkFont(size=13),
            wrap="word",
            height=150
        )
        self.prompt_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Placeholder text
        self.placeholder = """Describe the batch processing script you want to create...

Examples:
• "Resize all images to 1920x1080 and add a watermark"
• "Convert all PDFs to text and extract email addresses"
• "Rename files based on their creation date"
• "Apply sepia filter and add timestamp to photos"
"""

        # Add placeholder functionality
        self._add_placeholder(self.prompt_text, self.placeholder)

        # Buttons
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(fill="x")

        self.cancel_btn = ctk.CTkButton(
            self.btn_frame,
            text="Cancel",
            width=100,
            command=self.on_cancel,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["border"],
            text_color=COLORS["text_main"]
        )
        self.cancel_btn.pack(side="left", padx=(0, 10))

        self.generate_btn = ctk.CTkButton(
            self.btn_frame,
            text="Generate Script",
            width=150,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.generate,
            fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"]
        )
        self.generate_btn.pack(side="left")

    def _add_placeholder(self, textbox, placeholder_text):
        """
        Add placeholder functionality to a textbox.

        Args:
            textbox: The CTkTextbox widget
            placeholder_text: The placeholder text to display
        """
        self._placeholder_active = True

        # Insert placeholder with gray color
        textbox.insert("1.0", placeholder_text)
        textbox.configure(text_color=COLORS["text_sub"])

        # Bind focus events
        def on_focus_in(event):
            if self._placeholder_active:
                textbox.configure(state="normal")
                textbox.delete("1.0", "end")
                textbox.configure(text_color=COLORS["text_main"])
                self._placeholder_active = False

        def on_focus_out(event):
            content = textbox.get("1.0", "end").strip()
            if not content:
                textbox.insert("1.0", placeholder_text)
                textbox.configure(text_color=COLORS["text_sub"])
                self._placeholder_active = True

        textbox.bind("<FocusIn>", on_focus_in)
        textbox.bind("<FocusOut>", on_focus_out)

    def generate(self):
        """Generate a script using the LLM API."""
        prompt = self.prompt_text.get("1.0", "end").strip()
        if not prompt or prompt == self.placeholder.strip():
            self.log("❌ Please enter a description of the script you want to create.")
            return

        # Check API config
        config = get_config()
        if not config.get("api_key"):
            self.log("❌ API key not configured. Please open Settings (⚙) and enter your API key.")
            return

        # Clear log and update UI state
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

        self.generate_btn.configure(state="disabled", text="Generating...")
        self.start_spinner()
        self.update_status("Initializing...", 0.1)
        self.log(f"🔄 Generating script...")
        self.log(f"   Model: {config.get('model')}")

        # Run in background thread
        threading.Thread(
            target=self._run_generation,
            args=(prompt, config),
            daemon=True
        ).start()

    def start_spinner(self):
        """Start the spinner animation."""
        self.spinner_running = True
        self.status_frame.pack(fill="x", pady=(0, 15))
        self._animate_spinner()

    def stop_spinner(self):
        """Stop the spinner animation."""
        self.spinner_running = False
        self.status_frame.pack_forget()

    def _animate_spinner(self):
        """Animate the spinner."""
        if self.spinner_running:
            self.spinner_index = (self.spinner_index + 1) % len(self.spinner_frames)
            self.spinner_label.configure(text=self.spinner_frames[self.spinner_index])
            self.after(100, self._animate_spinner)

    def update_status(self, message, progress=None):
        """Update the status label and progress bar."""
        self.after(0, lambda: self.status_label.configure(text=message))
        if progress is not None:
            self.after(0, lambda: self.progress_bar.set(progress))

    def _run_generation(self, prompt, config):
        """Run generation in background thread with retry support."""
        try:
            self.update_status("Connecting to API...", 0.2)

            generator = ScriptGenerator(
                endpoint=config["endpoint"],
                model=config["model"],
                api_key=config["api_key"]
            )

            # Define progress callback for retry attempts
            def on_retry_attempt(attempt_num, max_attempts):
                if attempt_num > 1:
                    # Get the last validation error for display
                    error_msg = getattr(generator, 'last_validation_error', 'Unknown error')
                    self.log(f"\n⚠️  Validation failed (attempt {attempt_num}/{max_attempts}):")
                    self.log(f"   Issue: {error_msg}")
                    self.log(f"   Retrying with fix request...")
                    self.update_status(f"Retrying ({attempt_num}/{max_attempts})...", 0.2)

            self.log("   🔗 Sending request to LLM...")
            self.update_status("Sending request...", 0.3)

            result = generator.generate_script(
                user_prompt=prompt,
                progress_callback=on_retry_attempt
            )

            self.log("   ✓ Script generated successfully!")
            self.update_status("Validating script...", 0.7)

            # Get packages from result (already provided by LLM)
            external_packages = result.get("packages", [])

            # Save script
            from core.llm_generator import ScriptGenerator as SG
            script_name_slug = SG.sanitize_filename(result["name"])
            script_filename = script_name_slug
            script_path = os.path.join("scripts", f"{script_filename}.py")

            self.update_status("Saving script...", 0.9)

            with open(script_path, "w") as f:
                f.write(result["code"])

            self.log(f"   ✓ Saved to: {script_path}")
            self.log(f"\n✅ Script '{result['name']}' created successfully!")

            # Update progress to complete
            self.update_status("Complete!", 1.0)

            # Stop spinner immediately to prevent Tkinter errors
            self.stop_spinner()

            # Show external packages warning if needed
            if external_packages:
                self.log(f"\n📦 External packages required: {', '.join(external_packages)}")

                # Show install button in generator panel
                self._show_install_packages_button(script_filename, external_packages)
            else:
                # No packages, just show continue button
                self._show_continue_button(script_filename, external_packages)

        except APIError as e:
            self.log(f"\n❌ API Error: {e}")
            self.update_status("API Error", 0)
            self._reset_button()
        except ValidationError as e:
            self.log(f"\n❌ {e}")
            self.log("   Tip: Try rephrasing your request with more specific details.")
            self.update_status("Failed", 0)
            self._reset_button()
        except Exception as e:
            self.log(f"\n❌ Error: {e}")
            self.update_status("Error", 0)
            self._reset_button()

    def _show_install_packages_button(self, script_filename: str, external_packages: list[str]):
        """Show install packages button in the generator panel."""
        # Stop any pending after() callbacks to prevent Tkinter errors
        if hasattr(self, 'spinner_running') and self.spinner_running:
            self.spinner_running = False

        # Hide generate button
        if hasattr(self, 'generate_btn'):
            self.generate_btn.pack_forget()

        # Create install button
        self.install_btn = ctk.CTkButton(
            self.btn_frame,
            text=f"📦 Install {len(external_packages)} Package(s)",
            width=200,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self._install_all_packages(script_filename, external_packages),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"]
        )
        self.install_btn.pack(side="left")

        # Update cancel button to say "Skip"
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.configure(
                text="Skip Installation",
                command=lambda: self._continue_to_script(script_filename)
            )

        # Show install commands in log
        self.log(f"\n   Install commands:")
        for pkg in external_packages:
            install_cmd = get_install_command(pkg)
            self.log(f"   • {pkg}: {install_cmd}")

    def _install_all_packages(self, script_filename: str, external_packages: list[str]):
        """Install all required packages in sequence."""
        # Disable install button
        if hasattr(self, 'install_btn'):
            self.install_btn.configure(state="disabled", text="⏳ Installing...")

        # Disable skip button
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.configure(state="disabled")

        def run_install():
            success_count = 0
            failed_packages = []

            for i, pkg in enumerate(external_packages, 1):
                install_cmd = get_install_command(pkg)
                self.log(f"\n   [{i}/{len(external_packages)}] Installing {pkg}...")

                try:
                    result = subprocess.run(
                        install_cmd.split(),
                        capture_output=True,
                        text=True,
                        timeout=120
                    )

                    if result.returncode == 0:
                        success_count += 1
                        self.log(f"   ✓ {pkg} installed successfully")
                    else:
                        failed_packages.append(pkg)
                        stderr = result.stderr if result.stderr else result.stdout
                        self.log(f"   ❌ Failed to install {pkg}: {stderr[:100]}")
                except subprocess.TimeoutExpired:
                    failed_packages.append(pkg)
                    self.log(f"   ❌ Installation timed out for {pkg}")
                except Exception as e:
                    failed_packages.append(pkg)
                    self.log(f"   ❌ Error installing {pkg}: {e}")

            # Show final result
            self.log(f"\n{'=' * 60}")
            if success_count == len(external_packages):
                self.log(f"✅ All {success_count} packages installed successfully!")
                self.log(f"{'=' * 60}")
                self.log(f"\n🔄 Please relaunch the app to use the new packages.")
                self.log(f"   Your script '{script_filename}' will be ready to use.")

                # Change button to show success
                if hasattr(self, 'install_btn'):
                    self.after(0, lambda: self.install_btn.configure(
                        state="disabled",
                        text="✓ Installed - Relaunch App",
                        fg_color=COLORS["success"],
                        hover_color=COLORS["success_hover"]
                    ))

                # Add relaunch button
                self.relaunch_btn = ctk.CTkButton(
                    self.btn_frame,
                    text="🔄 Relaunch App",
                    width=150,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    command=self._relaunch_app,
                    fg_color=COLORS["success"],
                    hover_color=COLORS["success_hover"]
                )
                self.relaunch_btn.pack(side="left", padx=(10, 0))

            else:
                self.log(f"⚠️  Installation completed with issues:")
                self.log(f"   ✓ Success: {success_count}/{len(external_packages)}")
                if failed_packages:
                    self.log(f"   ❌ Failed: {', '.join(failed_packages)}")
                self.log(f"\n   You can still continue, but the script may not work properly.")

                # Re-enable buttons to allow retry or skip
                if hasattr(self, 'install_btn'):
                    self.after(0, lambda: self.install_btn.configure(
                        state="normal",
                        text="🔄 Retry Installation"
                    ))
                if hasattr(self, 'cancel_btn'):
                    self.after(0, lambda: self.cancel_btn.configure(
                        state="normal",
                        text="Continue Anyway",
                        command=lambda: self._continue_to_script(script_filename)
                    ))

        # Run in background thread
        thread = threading.Thread(target=run_install, daemon=True)
        thread.start()

    def _relaunch_app(self):
        """Relaunch the application."""
        import sys
        self.log("\n🔄 Restarting application...")
        self.after(1000, lambda: os.execv(sys.executable, [sys.executable] + sys.argv))

    def _show_continue_button(self, script_filename: str, external_packages: list[str]):
        """Show continue button and replace generate button."""
        # Stop any pending after() callbacks to prevent Tkinter errors
        if hasattr(self, 'spinner_running') and self.spinner_running:
            self.spinner_running = False

        # Hide generate button and show continue button
        if hasattr(self, 'generate_btn'):
            self.generate_btn.pack_forget()

        # Create continue button
        self.continue_btn = ctk.CTkButton(
            self.btn_frame,
            text=f"Continue to '{script_filename}' →",
            width=150,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self._continue_to_script(script_filename),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"]
        )
        self.continue_btn.pack(side="left")

        # Update cancel button text
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.configure(text="Cancel", command=self.on_cancel)

        # If no packages, auto-continue after a delay
        if not external_packages:
            self.after(2000, lambda: self._continue_to_script(script_filename))

    def _continue_to_script(self, script_filename: str):
        """Continue to the generated script."""
        # Proper cleanup to prevent Tkinter errors
        self.stop_spinner()
        self.spinner_running = False
        self.on_complete(script_filename)

    def _reset_button(self):
        """Reset generate button state."""
        self.stop_spinner()
        self.spinner_running = False

        # Remove continue/install/relaunch buttons if exists
        for btn_attr in ['continue_btn', 'install_btn', 'relaunch_btn']:
            if hasattr(self, btn_attr):
                try:
                    getattr(self, btn_attr).pack_forget()
                except:
                    pass

        # Reset cancel button text
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.configure(text="Cancel", command=self.on_cancel)

        # Show generate button again
        if hasattr(self, 'generate_btn'):
            self.generate_btn.pack(side="left")
            self.after(0, lambda: self.generate_btn.configure(
                state="normal",
                text="Generate Script",
                fg_color=COLORS["success"]
            ))
