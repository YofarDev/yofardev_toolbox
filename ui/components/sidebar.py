"""Sidebar component with script list."""
import customtkinter as ctk
from config.themes import COLORS, get_font


class Sidebar(ctk.CTkFrame):
    """Left sidebar with script list and search."""

    def __init__(self, master, scripts, on_script_select=None, on_generate_click=None, on_settings_click=None):
        """
        Initialize the sidebar.

        Args:
            master: Parent widget
            scripts: List of script dictionaries
            on_script_select: Callback when script is selected (script_dict)
            on_generate_click: Callback when generate button is clicked
            on_settings_click: Callback when settings button is clicked
        """
        super().__init__(master, width=280, corner_radius=0, fg_color=COLORS["bg_sidebar"])
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.scripts = scripts
        self.on_script_select = on_script_select
        self.on_generate_click = on_generate_click
        self.on_settings_click = on_settings_click

        self.script_buttons = {}

        self.create_widgets()

    def create_widgets(self):
        """Create sidebar widgets."""
        # Logo Area
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=25, pady=(30, 20), sticky="ew")

        ctk.CTkLabel(
            logo_frame,
            text="YOFARDEV",
            font=get_font("header_large"),
            text_color=COLORS["text_main"],
            anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            logo_frame,
            text="AUTOMATION TOOLBOX",
            font=ctk.CTkFont(family="Roboto", size=10, weight="bold"),
            text_color=COLORS["accent"],
            anchor="w"
        ).pack(anchor="w")

        # Separator
        sep = ctk.CTkFrame(self, height=1, fg_color=COLORS["border"])
        sep.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 15))

        # Search Box
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 10))

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search scripts...",
            fg_color=COLORS["bg_card"],
            border_color=COLORS["border"],
            height=35,
            font=ctk.CTkFont(size=12)
        )
        self.search_entry.pack(fill="x")
        self.search_entry.bind("<KeyRelease>", self.on_search)

        # Generate Script Button
        self.generate_script_btn = ctk.CTkButton(
            self,
            text="🤖 Generate Script",
            command=self.on_generate_click,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=6
        )
        self.generate_script_btn.grid(row=3, column=0, padx=15, pady=(0, 10), sticky="ew")

        # Scrollable Script List
        self.script_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", label_text=None)
        self.script_scroll.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="nsew")

        self.populate_scripts()

        # Footer with Settings
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.grid(row=5, column=0, pady=10, sticky="ew")

        footer_lbl = ctk.CTkLabel(
            footer_frame,
            text="v1.2.0 • Ready",
            text_color=COLORS["border"],
            font=("Arial", 10)
        )
        footer_lbl.pack(side="left", padx=15)

        self.settings_btn = ctk.CTkButton(
            footer_frame,
            text="⚙",
            width=30,
            height=30,
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            text_color=COLORS["border"],
            hover_color=COLORS["bg_card"],
            command=self.on_settings_click,
            corner_radius=15
        )
        self.settings_btn.pack(side="right", padx=15)

    def populate_scripts(self):
        """Populate the script list."""
        # Clear existing buttons
        for widget in self.script_scroll.winfo_children():
            widget.destroy()
        self.script_buttons = {}

        if not self.scripts:
            ctk.CTkLabel(
                self.script_scroll,
                text="No scripts found in /scripts",
                text_color=COLORS["text_sub"]
            ).pack(pady=20)
            return

        for script in self.scripts:
            btn = ctk.CTkButton(
                self.script_scroll,
                text=f"  {script['name']}",
                command=lambda s=script: self.on_script_selected(s),
                fg_color="transparent",
                text_color=COLORS["text_sub"],
                hover_color=COLORS["bg_card"],
                anchor="w",
                height=45,
                font=ctk.CTkFont(size=13),
                corner_radius=6
            )
            btn.pack(fill="x", pady=2)
            self.script_buttons[script['name']] = btn

    def on_script_selected(self, script):
        """Handle script selection."""
        if self.on_script_select:
            self.on_script_select(script)

    def on_search(self, event=None):
        """Handle search input."""
        query = self.search_entry.get()
        self.filter_scripts(query)

    def filter_scripts(self, query):
        """
        Filter scripts based on search query.

        Args:
            query: Search query string
        """
        search_query = query.lower().strip()

        # Remove existing "no results" label if present
        for widget in self.script_scroll.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and widget.cget("text").startswith("No scripts"):
                widget.destroy()

        visible_count = 0
        for script_name, button in self.script_buttons.items():
            script_data = next((s for s in self.scripts if s['name'] == script_name), None)
            if script_data:
                name_matches = search_query in script_name.lower()
                desc_matches = search_query in script_data['description'].lower()

                if search_query == "" or name_matches or desc_matches:
                    button.pack(fill="x", pady=2)
                    visible_count += 1
                else:
                    button.pack_forget()

        # Show "no results" message if no scripts match
        if visible_count == 0 and search_query != "":
            ctk.CTkLabel(
                self.script_scroll,
                text=f"No scripts match '{search_query}'",
                text_color=COLORS["text_sub"]
            ).pack(pady=20)

    def highlight_script(self, script_name: str):
        """
        Highlight the selected script.

        Args:
            script_name: Name of the script to highlight
        """
        for name, btn in self.script_buttons.items():
            if name == script_name:
                btn.configure(fg_color=COLORS["accent"], text_color="#ffffff")
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_sub"])

    def refresh_scripts(self, scripts):
        """
        Refresh the script list.

        Args:
            scripts: New list of scripts
        """
        self.scripts = scripts
        self.populate_scripts()
