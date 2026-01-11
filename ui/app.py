"""Main application window - orchestrates all components."""
import customtkinter as ctk
import os
import sys
import threading
from tkinter import filedialog
import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.themes import COLORS, get_font
from config.app_config import WINDOW_SIZE
from core.script_manager import ScriptManager
from core.script_executor import ScriptExecutor, open_output_folder
from core.file_handler import FileHandler
from config import get_config, get_current_llm
from core.llm_generator import ScriptGenerator, GenerationError, APIError, ValidationError

from ui.components.sidebar import Sidebar
from ui.components.console import Console
from ui.components.generator_panel import GeneratorPanel
from ui.dialogs.settings_dialog import SettingsDialog


class App(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.title("Yofardev Toolbox")
        self.geometry(WINDOW_SIZE)
        self.configure(fg_color=COLORS["bg_root"])

        # Grid Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- State Variables ---
        self.script_manager = ScriptManager()
        self.scripts = self.script_manager.load_scripts()
        self.current_script = None
        self.parameter_widgets = {}
        self.selected_files = []
        self.script_buttons = {}
        self.current_process = None
        self.showing_generator = False
        self.generator_widgets = {}

        # --- UI Components ---
        self.create_sidebar()
        self.create_main_area()

    def create_sidebar(self):
        """Left Sidebar for Script Selection"""
        self.sidebar = Sidebar(
            self,
            self.scripts,
            on_script_select=self.load_script_details,
            on_generate_click=self.show_generator,
            on_settings_click=self.show_settings_modal
        )
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")

    def create_main_area(self):
        """Right Main Area"""
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)

        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # 1. Header
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        self.script_title_label = ctk.CTkLabel(
            self.header_frame,
            text="Select a Script",
            font=get_font("header_large"),
            text_color=COLORS["text_main"],
            anchor="w"
        )
        self.script_title_label.pack(fill="x")

        self.script_desc_label = ctk.CTkLabel(
            self.header_frame,
            text="Choose an automation tool from the sidebar to configure parameters and run tasks.",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_sub"],
            anchor="w",
            justify="left",
            wraplength=800
        )
        self.script_desc_label.pack(fill="x", pady=(5, 0))

        # 2. Configuration Container (Grid)
        self.config_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.config_container.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        self.config_container.grid_columnconfigure(0, weight=1, uniform="group1")
        self.config_container.grid_columnconfigure(1, weight=1, uniform="group1")
        self.config_container.grid_rowconfigure(0, weight=1)

        # --- Card 1: Parameters ---
        self.params_card = ctk.CTkFrame(
            self.config_container,
            fg_color=COLORS["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"]
        )
        self.params_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        p_header = ctk.CTkFrame(self.params_card, fg_color="transparent", height=40)
        p_header.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkLabel(
            p_header,
            text="Configuration",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS["text_main"]
        ).pack(side="left")

        self.params_scroll = ctk.CTkScrollableFrame(self.params_card, fg_color="transparent")
        self.params_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        self.empty_params_lbl = ctk.CTkLabel(
            self.params_scroll,
            text="No parameters available.",
            text_color=COLORS["border"]
        )
        self.empty_params_lbl.pack(pady=40)

        # --- Card 2: Files ---
        self.files_card = ctk.CTkFrame(
            self.config_container,
            fg_color=COLORS["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"]
        )
        self.files_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        f_header = ctk.CTkFrame(self.files_card, fg_color="transparent", height=40)
        f_header.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkLabel(
            f_header,
            text="Input Files",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS["text_main"]
        ).pack(side="left")

        self.clear_files_btn = ctk.CTkButton(
            f_header,
            text="Clear All",
            width=60,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            text_color=COLORS["danger"],
            hover_color=COLORS["bg_root"],
            command=self.clear_files,
            state="disabled"
        )
        self.clear_files_btn.pack(side="right")

        # File Action Buttons
        self.file_btn_frame = ctk.CTkFrame(self.files_card, fg_color="transparent")
        self.file_btn_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.add_file_btn = ctk.CTkButton(
            self.file_btn_frame,
            text="+ Add Files",
            height=32,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self.add_files,
            state="disabled"
        )
        self.add_file_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.add_folder_btn = ctk.CTkButton(
            self.file_btn_frame,
            text="+ Add Folder",
            height=32,
            fg_color=COLORS["bg_root"],
            hover_color="#000000",
            command=self.add_folder,
            state="disabled"
        )
        self.add_folder_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # File List
        self.file_list_scroll = ctk.CTkScrollableFrame(
            self.files_card,
            fg_color=COLORS["bg_root"],
            height=150,
            corner_radius=6
        )
        self.file_list_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.file_list_placeholder = ctk.CTkLabel(
            self.file_list_scroll,
            text="Drag and drop not supported.\nPlease use buttons above.",
            text_color=COLORS["border"]
        )
        self.file_list_placeholder.pack(pady=40)

        # 3. Console & Execution
        self.bottom_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.bottom_frame.grid(row=2, column=0, sticky="nsew")
        self.bottom_frame.grid_rowconfigure(1, weight=1)
        self.bottom_frame.grid_columnconfigure(0, weight=1)

        # Run Button Bar
        self.action_bar = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        self.action_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self.run_button = ctk.CTkButton(
            self.action_bar,
            text="RUN SCRIPT",
            height=50,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"],
            corner_radius=8,
            state="disabled",
            command=self.run_script
        )
        self.run_button.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.stop_button = ctk.CTkButton(
            self.action_bar,
            text="STOP",
            height=50,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=COLORS["danger"],
            hover_color=COLORS["danger_hover"],
            corner_radius=8,
            width=150,
            state="disabled",
            command=self.stop_script
        )
        self.stop_button.pack(side="right")

        # Console Window
        self.output_console = Console(self.bottom_frame)
        self.output_console.grid(row=1, column=0, sticky="nsew")

        # Initialize executor
        self.executor = ScriptExecutor(
            output_callback=self.output_console.append_stream,
            finished_callback=self._process_finished,
            install_callback=self.output_console.show_install_button
        )

    # --- Script Loading and Selection ---

    def load_script_details(self, script):
        """Load and display script details."""
        # Exit generator mode if active
        if self.showing_generator:
            self._exit_generator()

        # Update sidebar highlighting
        self.sidebar.highlight_script(script["name"])

        self.current_script = script

        # Update Header
        self.script_title_label.configure(text=script["name"])
        self.script_desc_label.configure(text=script["description"])

        # Button Config
        if not script.get("accepts_multiple_files", True):
            self.add_file_btn.configure(text="Select File", command=self.add_file)
            self.add_folder_btn.configure(state="disabled")
        else:
            self.add_file_btn.configure(text="+ Add Files", command=self.add_files)
            self.add_folder_btn.configure(state="normal")

        self.add_file_btn.configure(state="normal")
        self.clear_files_btn.configure(state="normal")
        self.run_button.configure(state="normal", text="RUN SCRIPT", fg_color=COLORS["success"])

        # Clear Params
        for widget in self.params_scroll.winfo_children():
            widget.destroy()
        self.parameter_widgets = {}

        # Build Params
        if not script["parameters"]:
            self.empty_params_lbl = ctk.CTkLabel(
                self.params_scroll,
                text="No parameters required.",
                text_color=COLORS["border"]
            )
            self.empty_params_lbl.pack(pady=20)

        for param in script["parameters"]:
            # Parameter Row Container
            param_frame = ctk.CTkFrame(self.params_scroll, fg_color="transparent")
            param_frame.pack(fill="x", pady=8, padx=5)

            # Label
            label_text = param.get("label", param["name"])
            lbl = ctk.CTkLabel(
                param_frame,
                text=label_text,
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w"
            )
            lbl.pack(fill="x", pady=(0, 2))

            # Input Widget
            if param["type"] == "choice":
                widget = ctk.CTkOptionMenu(
                    param_frame,
                    values=param["choices"],
                    fg_color=COLORS["bg_root"],
                    button_color=COLORS["accent"]
                )
                widget.set(param["default"])
            elif param["type"] in ["integer", "int", "float", "string"]:
                widget = ctk.CTkEntry(
                    param_frame,
                    fg_color=COLORS["bg_root"],
                    border_color=COLORS["border"]
                )
                widget.insert(0, str(param.get("default", "")))
            elif param["type"] in ["boolean", "bool"]:
                widget = ctk.CTkSwitch(
                    param_frame,
                    text="Enable",
                    progress_color=COLORS["success"]
                )
                if param.get("default"):
                    widget.select()
            else:
                widget = ctk.CTkEntry(param_frame, fg_color=COLORS["bg_root"])

            widget.pack(fill="x")
            self.parameter_widgets[param["name"]] = widget

            # Description
            if param.get("description"):
                desc_lbl = ctk.CTkLabel(
                    param_frame,
                    text=param.get("description"),
                    text_color=COLORS["text_sub"],
                    font=ctk.CTkFont(size=11),
                    anchor="w",
                    justify="left",
                    wraplength=380
                )
                desc_lbl.pack(fill="x", pady=(4, 2))

        self.selected_files = []
        self.update_file_list_ui()

    # --- File Handling ---

    def update_file_list_ui(self):
        """Update the file list display."""
        for widget in self.file_list_scroll.winfo_children():
            widget.destroy()

        if not self.selected_files:
            self.file_list_placeholder = ctk.CTkLabel(
                self.file_list_scroll,
                text="No files selected",
                text_color=COLORS["border"]
            )
            self.file_list_placeholder.pack(pady=40)
            self.run_button.configure(state="disabled", fg_color=COLORS["border"])
            return

        # Re-enable run button if we have files
        self.run_button.configure(state="normal", fg_color=COLORS["success"])

        for i, file_path in enumerate(self.selected_files):
            row = ctk.CTkFrame(self.file_list_scroll, fg_color=COLORS["bg_card"], height=35)
            row.pack(fill="x", pady=2)

            icon = ctk.CTkLabel(row, text="📄", width=30, anchor="center")
            icon.pack(side="left")

            name = os.path.basename(file_path)
            lbl = ctk.CTkLabel(row, text=name, anchor="w", font=ctk.CTkFont(size=12))
            lbl.pack(side="left", padx=5, fill="x", expand=True)

            del_btn = ctk.CTkButton(
                row,
                text="×",
                width=30,
                height=25,
                fg_color="transparent",
                hover_color=COLORS["danger"],
                text_color=COLORS["danger"],
                font=("Arial", 16, "bold"),
                command=lambda idx=i: self.remove_file(idx)
            )
            del_btn.pack(side="right", padx=5, pady=5)

    def remove_file(self, index):
        """Remove a file from the list."""
        if 0 <= index < len(self.selected_files):
            del self.selected_files[index]
            self.update_file_list_ui()

    def clear_files(self):
        """Clear all selected files."""
        self.selected_files = []
        self.update_file_list_ui()

    def add_file(self):
        """Add a single file."""
        if not self.current_script:
            return
        filetypes = self._get_filetypes()
        file = filedialog.askopenfilename(filetypes=filetypes)
        if file:
            self.selected_files = [file]
            self.update_file_list_ui()

    def add_files(self):
        """Add multiple files."""
        if not self.current_script:
            return
        filetypes = self._get_filetypes()
        files = filedialog.askopenfilenames(filetypes=filetypes)
        if files:
            for file in files:
                if file not in self.selected_files:
                    self.selected_files.append(file)
            self.update_file_list_ui()

    def _get_filetypes(self):
        """Get filetypes for file dialog."""
        filetypes = []
        input_str = self.current_script.get("input_types", "")
        if input_str:
            parts = input_str.split("(")
            if len(parts) > 1:
                desc = parts[0].strip()
                exts = parts[1].replace(")", "")
                filetypes.append((desc, exts))
        filetypes.append(("All Files", "*.*"))
        return filetypes

    def add_folder(self):
        """Add all files from a folder."""
        if not self.current_script:
            return
        folder = filedialog.askdirectory()
        if not folder:
            return

        file_handler = FileHandler()
        target_exts = file_handler.get_file_extensions(
            self.current_script.get("input_types", "")
        )

        images = file_handler.get_images_from_folder(folder, target_exts)
        for img in images:
            if img not in self.selected_files:
                self.selected_files.append(img)

        if images:
            self.update_file_list_ui()

    # --- Script Execution ---

    def run_script(self):
        """Run the current script."""
        if not self.current_script:
            return

        script_filename = self.current_script["filename"]
        script_path = os.path.join("scripts", f"{script_filename}.py")

        # Get parameter values
        params = {}
        for name, widget in self.parameter_widgets.items():
            param_def = next(
                (p for p in self.current_script["parameters"] if p["name"] == name),
                None
            )
            if param_def and param_def["type"] in ["boolean", "bool"]:
                params[name] = widget.get() == 1
            else:
                params[name] = widget.get()

        # Build output directory
        script_name_slug = self.current_script["name"].lower().replace(" ", "_")
        downloads_dir = os.path.expanduser("~/Downloads")
        output_dir = os.path.join(downloads_dir, script_name_slug)

        # Initialize console
        self.output_console.initialize_script(self.current_script["name"], output_dir)

        # Update UI
        self.run_button.configure(state="disabled", text="PROCESSING...", fg_color=COLORS["accent"])
        self.stop_button.configure(state="normal")

        # Execute
        self.executor.execute(script_path, self.selected_files, params, self.current_script)

    def stop_script(self):
        """Stop the currently running script."""
        if self.executor.is_running():
            self.output_console.append_stream("\n> Interrupting script...\n")
            self.executor.stop()
            self.output_console.append_stream("\n> Script interrupted by user.\n")
            self.stop_button.configure(state="disabled")
            self.run_button.configure(state="normal", text="RUN SCRIPT", fg_color=COLORS["success"])

    def _process_finished(self, return_code, output_dir):
        """Handle process completion."""
        self.stop_button.configure(state="disabled")

        if return_code == 0:
            self.output_console.show_success(output_dir)
            if output_dir:
                if not open_output_folder(output_dir):
                    self.output_console.append_stream("Could not open output folder.\n")
            self.run_button.configure(state="normal", text="RUN SCRIPT", fg_color=COLORS["success"])
        else:
            self.output_console.show_failure(return_code)
            self.run_button.configure(state="normal", text="RETRY", fg_color=COLORS["danger"])

    # --- Generator Methods ---

    def show_generator(self):
        """Show the script generator panel."""
        self.showing_generator = True
        self.current_script = None

        # Unhighlight sidebar
        for name, btn in self.sidebar.script_buttons.items():
            btn.configure(fg_color="transparent", text_color=COLORS["text_sub"])

        # Clear main area
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Create generator panel
        self.generator_panel = GeneratorPanel(
            self.main_frame,
            self.scripts,
            on_complete=self._on_generator_complete,
            on_cancel=self._exit_generator
        )
        self.generator_panel.pack(fill="both", expand=True)

    def _on_generator_complete(self, script_filename):
        """Called when script generation completes."""
        # Reload scripts
        self.scripts = self.script_manager.refresh()
        self.sidebar.refresh_scripts(self.scripts)

        # Find and select the new script
        new_script = self.script_manager.get_script_by_filename(script_filename)
        if new_script:
            self.showing_generator = False
            self._exit_generator()
            self.load_script_details(new_script)

    def _exit_generator(self):
        """Exit generator mode and restore normal view."""
        self.showing_generator = False
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.create_main_area()

    def show_settings_modal(self):
        """Show settings modal for LLM configuration."""
        SettingsDialog(self)

    def _log_to_console(self, message):
        """Log a message to the console."""
        self.output_console.append_stream(message + "\n")


if __name__ == "__main__":
    app = App()
    app.mainloop()
