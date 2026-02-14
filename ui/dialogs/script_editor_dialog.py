"""Script editor dialog with version history and LLM editing."""
import customtkinter as ctk
import os
import threading
from pathlib import Path
from typing import Optional, Dict, Callable

from config.themes import COLORS, get_font
from core.script_version_manager import ScriptVersionManager, ScriptVersion
from core.llm_script_editor import LLMScriptEditor


class ScriptEditorDialog(ctk.CTkToplevel):
    """Dialog for editing scripts with version control and LLM assistance."""

    def __init__(
        self,
        parent,
        script_config: Dict,
        script_path: str,
        on_save: Callable,
        version_manager: ScriptVersionManager
    ):
        super().__init__(parent)

        self.script_config = script_config
        self.script_path = script_path
        self.on_save = on_save
        self.version_manager = version_manager
        self.llm_editor = LLMScriptEditor()
        self.versions = []
        self.original_code = ""

        # Setup window
        self.title(f"Edit Script: {script_config['name']}")
        self.geometry("1000x700")
        self.configure(fg_color=COLORS["bg_root"])

        # Make modal
        self.grab_set()
        self.focus_set()

        # Load script content
        self._load_script_content()

        # Build UI
        self._create_ui()

        # Load versions
        self._load_versions()

    def _load_script_content(self):
        """Load script content from file."""
        try:
            with open(self.script_path, 'r', encoding='utf-8') as f:
                self.original_code = f.read()
        except Exception as e:
            self.original_code = f"# Error loading script: {e}"

    def _create_ui(self):
        """Create dialog UI."""
        # Main layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Content frame
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        # Left sidebar - Version History
        self._create_version_sidebar(content_frame)

        # Right - Code Editor
        self._create_code_editor(content_frame)

        # Bottom - Action Bar
        self._create_action_bar(content_frame)

    def _create_version_sidebar(self, parent):
        """Create version history sidebar."""
        sidebar = ctk.CTkFrame(
            parent,
            fg_color=COLORS["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
            width=250
        )
        sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 10))

        # Header
        header = ctk.CTkFrame(sidebar, fg_color="transparent", height=40)
        header.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkLabel(
            header,
            text="Version History",
            font=get_font("header_small"),
            text_color=COLORS["text_main"]
        ).pack(side="left")

        # Version list
        self.version_scroll = ctk.CTkScrollableFrame(
            sidebar,
            fg_color="transparent",
            height=400
        )
        self.version_scroll.pack(fill="both", expand=True, padx=10, pady=10)

        self.empty_versions_label = ctk.CTkLabel(
            self.version_scroll,
            text="No previous versions",
            text_color=COLORS["text_sub"],
            font=ctk.CTkFont(size=12)
        )
        self.empty_versions_label.pack(pady=20)

    def _create_code_editor(self, parent):
        """Create code editor area."""
        editor_frame = ctk.CTkFrame(
            parent,
            fg_color=COLORS["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"]
        )
        editor_frame.grid(row=0, column=1, sticky="nsew")
        editor_frame.grid_columnconfigure(0, weight=1)
        editor_frame.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(editor_frame, fg_color="transparent", height=40)
        header.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
        ctk.CTkLabel(
            header,
            text="Script Code",
            font=get_font("header_small"),
            text_color=COLORS["text_main"]
        ).pack(side="left")

        # Code textbox
        self.code_textbox = ctk.CTkTextbox(
            editor_frame,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=COLORS["bg_root"],
            text_color=COLORS["text_main"],
            border_color=COLORS["border"],
            border_width=1
        )
        self.code_textbox.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))

        # Load code
        self.code_textbox.insert("1.0", self.original_code)

    def _create_action_bar(self, parent):
        """Create action buttons bar."""
        action_frame = ctk.CTkFrame(parent, fg_color="transparent")
        action_frame.grid(row=1, column=1, sticky="ew", pady=(10, 0))

        # Left buttons
        left_buttons = ctk.CTkFrame(action_frame, fg_color="transparent")
        left_buttons.pack(side="left")

        self.open_external_btn = ctk.CTkButton(
            left_buttons,
            text="📝 Open in Editor",
            width=150,
            height=35,
            fg_color=COLORS["bg_root"],
            hover_color="#000000",
            command=self._open_in_external_editor
        )
        self.open_external_btn.pack(side="left", padx=(0, 5))

        self.llm_edit_btn = ctk.CTkButton(
            left_buttons,
            text="✨ Ask AI to Edit",
            width=150,
            height=35,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self._show_llm_edit_dialog
        )
        self.llm_edit_btn.pack(side="left", padx=5)

        # Right buttons
        right_buttons = ctk.CTkFrame(action_frame, fg_color="transparent")
        right_buttons.pack(side="right")

        cancel_btn = ctk.CTkButton(
            right_buttons,
            text="Cancel",
            width=100,
            height=35,
            fg_color="transparent",
            text_color=COLORS["text_sub"],
            hover_color=COLORS["bg_root"],
            command=self.destroy
        )
        cancel_btn.pack(side="left", padx=5)

        self.save_btn = ctk.CTkButton(
            right_buttons,
            text="💾 Save Changes",
            width=150,
            height=35,
            fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"],
            command=self._save_changes
        )
        self.save_btn.pack(side="left", padx=(5, 0))

    def _load_versions(self):
        """Load and display version history."""
        script_filename = Path(self.script_path).stem
        self.versions = self.version_manager.get_versions(script_filename)

        # Clear existing version widgets
        for widget in self.version_scroll.winfo_children():
            widget.destroy()

        if not self.versions:
            self.empty_versions_label = ctk.CTkLabel(
                self.version_scroll,
                text="No previous versions",
                text_color=COLORS["text_sub"],
                font=ctk.CTkFont(size=12)
            )
            self.empty_versions_label.pack(pady=20)
            return

        # Display versions
        for version in self.versions:
            self._create_version_widget(version)

    def _create_version_widget(self, version: ScriptVersion):
        """Create a widget for displaying version info."""
        frame = ctk.CTkFrame(
            self.version_scroll,
            fg_color=COLORS["bg_root"],
            corner_radius=6
        )
        frame.pack(fill="x", pady=5, padx=2)

        # Version number
        v_label = ctk.CTkLabel(
            frame,
            text=f"v{version.version_number}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["accent"]
        )
        v_label.pack(anchor="w", padx=10, pady=(8, 2))

        # Timestamp
        ts_label = ctk.CTkLabel(
            frame,
            text=version.timestamp,
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_sub"]
        )
        ts_label.pack(anchor="w", padx=10, pady=2)

        # Description
        desc = version.change_description
        if len(desc) > 30:
            desc = desc[:27] + "..."
        desc_label = ctk.CTkLabel(
            frame,
            text=desc,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_main"],
            anchor="w"
        )
        desc_label.pack(anchor="w", padx=10, pady=(2, 5))

        # Revert button
        revert_btn = ctk.CTkButton(
            frame,
            text="↺ Revert",
            width=80,
            height=24,
            font=ctk.CTkFont(size=10),
            fg_color="transparent",
            text_color=COLORS["accent"],
            hover_color=COLORS["bg_root"],
            command=lambda v=version: self._revert_to_version(v)
        )
        revert_btn.pack(pady=(0, 8))

    def _revert_to_version(self, version: ScriptVersion):
        """Revert script to a previous version."""
        # Confirm
        if not self._confirm_revert(version):
            return

        # Restore
        success = self.version_manager.restore_version(self.script_path, version)
        if success:
            # Reload content
            self._load_script_content()
            self.code_textbox.delete("1.0", "end")
            self.code_textbox.insert("1.0", self.original_code)

            # Reload versions list
            self._load_versions()

            self.show_info(f"Restored to version {version.version_number}")
        else:
            self.show_error("Failed to restore version")

    def _confirm_revert(self, version: ScriptVersion) -> bool:
        """Show confirmation dialog for revert."""
        # For simplicity, using CTkmessagebox equivalent
        confirm_dialog = ctk.CTkToplevel(self)
        confirm_dialog.title("Confirm Revert")
        confirm_dialog.geometry("400x200")
        confirm_dialog.configure(fg_color=COLORS["bg_root"])
        confirm_dialog.grab_set()

        frame = ctk.CTkFrame(confirm_dialog, fg_color="transparent")
        frame.pack(expand=True, fill="both", padx=30, pady=30)

        ctk.CTkLabel(
            frame,
            text=f"Revert to version {version.version_number}?",
            font=get_font("header_small"),
            text_color=COLORS["text_main"]
        ).pack(pady=(0, 10))

        ctk.CTkLabel(
            frame,
            text=f"{version.change_description}\n\nThis will create a backup of the current version first.",
            text_color=COLORS["text_sub"],
            wraplength=340
        ).pack(pady=(0, 20))

        result = {"confirmed": False}

        def confirm():
            result["confirmed"] = True
            confirm_dialog.destroy()

        def cancel():
            confirm_dialog.destroy()

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack()

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=100,
            fg_color="transparent",
            text_color=COLORS["text_sub"],
            command=cancel
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Revert",
            width=100,
            fg_color=COLORS["danger"],
            command=confirm
        ).pack(side="left", padx=5)

        self.wait_window(confirm_dialog)
        return result["confirmed"]

    def _open_in_external_editor(self):
        """Open script in system default text editor."""
        try:
            import subprocess
            import sys

            if sys.platform == "darwin":  # macOS
                subprocess.Popen(["open", "-a", "TextEdit", self.script_path])
            elif sys.platform == "win32":  # Windows
                os.startfile(self.script_path)
            else:  # Linux
                subprocess.Popen(["xdg-open", self.script_path])

            self.show_info("Opened in external editor. Reload after saving to see changes.")

        except Exception as e:
            self.show_error(f"Failed to open editor: {e}")

    def _show_llm_edit_dialog(self):
        """Show dialog for LLM-assisted editing."""
        if not self.llm_editor.is_configured():
            self.show_error(
                "LLM not configured.\n"
                "Please configure your API key in Settings first."
            )
            return

        # Create dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("AI Script Editor")
        dialog.geometry("600x400")
        dialog.configure(fg_color=COLORS["bg_root"])
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(expand=True, fill="both", padx=30, pady=30)

        ctk.CTkLabel(
            frame,
            text="What changes would you like to make?",
            font=get_font("header_small"),
            text_color=COLORS["text_main"]
        ).pack(pady=(0, 15))

        request_textbox = ctk.CTkTextbox(
            frame,
            height=150,
            fg_color=COLORS["bg_root"],
            border_color=COLORS["border"]
        )
        request_textbox.pack(fill="x", pady=(0, 20))
        request_textbox.focus_set()

        def generate():
            request = request_textbox.get("1.0", "end").strip()
            if not request:
                self.show_error("Please describe the changes you want")
                return

            dialog.destroy()
            self._generate_with_llm(request)

        ctk.CTkButton(
            frame,
            text="✨ Generate with AI",
            height=40,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=generate
        ).pack()

    def _generate_with_llm(self, request: str):
        """Generate script modification using LLM."""
        # Show loading
        self.llm_edit_btn.configure(state="disabled", text="⏳ Generating...")

        # Run in thread
        def thread_func():
            success, code, error = self.llm_editor.edit_script(
                self.original_code,
                request,
                self.script_config
            )

            # Update UI in main thread
            self.after(0, lambda: self._on_llm_complete(success, code, error))

        thread = threading.Thread(target=thread_func, daemon=True)
        thread.start()

    def _on_llm_complete(self, success: bool, code: str, error: str):
        """Handle LLM generation completion."""
        self.llm_edit_btn.configure(state="normal", text="✨ Ask AI to Edit")

        if success:
            # Update editor with generated code
            self.code_textbox.delete("1.0", "end")
            self.code_textbox.insert("1.0", code)
            self.show_info("AI generated updated code. Review and save when ready.")
        else:
            self.show_error(f"Generation failed: {error}")

    def _save_changes(self):
        """Save the edited script."""
        new_code = self.code_textbox.get("1.0", "end")

        # Create backup before saving
        self.version_manager.create_backup(
            self.script_path,
            change_description="Manual edit",
            editor_type="manual"
        )

        # Write to file
        try:
            with open(self.script_path, 'w', encoding='utf-8') as f:
                f.write(new_code)

            self.show_info("Script saved successfully!")

            # Trigger callback
            if self.on_save:
                self.on_save()

            # Close dialog
            self.destroy()

        except Exception as e:
            self.show_error(f"Failed to save: {e}")

    def show_info(self, message: str):
        """Show info message."""
        self._show_message("Info", message, COLORS["accent"])

    def show_error(self, message: str):
        """Show error message."""
        self._show_message("Error", message, COLORS["danger"])

    def _show_message(self, title: str, message: str, color: str):
        """Show a message dialog."""
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.configure(fg_color=COLORS["bg_root"])
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(expand=True, fill="both", padx=30, pady=30)

        ctk.CTkLabel(
            frame,
            text=message,
            text_color=COLORS["text_main"],
            wraplength=340
        ).pack(expand=True)

        ctk.CTkButton(
            frame,
            text="OK",
            width=100,
            fg_color=color,
            command=dialog.destroy
        ).pack(pady=20)
