"""Example prompts dialog for script generator."""
import customtkinter as ctk
from config.themes import COLORS


class ExamplesDialog(ctk.CTkToplevel):
    """Dialog showing example prompts for script generation."""

    def __init__(self, master, prompt_widget, on_select=None):
        """
        Initialize the examples dialog.

        Args:
            master: Parent widget
            prompt_widget: The textbox widget to update when example is selected
            on_select: Optional callback with (title, description) when example selected
        """
        super().__init__(master)
        self.prompt_widget = prompt_widget
        self.on_select = on_select

        self.title("Example Prompts")
        self.geometry("400x300")
        self.configure(fg_color=COLORS["bg_card"])
        self.transient(master)
        self.grab_set()

        # Handle window close button (X)
        self.protocol("WM_DELETE_WINDOW", self.close_dialog)

        # Center
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 200
        y = (self.winfo_screenheight() // 2) - 150
        self.geometry(f"400x300+{x}+{y}")

        self.create_widgets()

    def create_widgets(self):
        """Create dialog widgets."""
        ctk.CTkLabel(
            self,
            text="Select an Example",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_main"]
        ).pack(pady=(20, 10))

        examples = [
            ("Vintage film grain effect",
             "Add a vintage film grain effect with adjustable intensity and grain size"),
            ("Polaroid-style frames",
             "Create a script that generates polaroid-style frames with customizable borders"),
            ("Timestamp with custom formatting",
             "Build a tool that adds timestamps to images with custom formatting options"),
            ("Duotone color effect",
             "Apply a duotone color effect with two color pickers for highlights and shadows"),
            ("Vignette with adjustable radius",
             "Add a vignette effect with adjustable radius and intensity controls"),
            ("Color lookup table (LUT) application",
             "Apply color grading using lookup tables (LUTs) for cinematic effects")
        ]

        for title, desc in examples:
            frame = ctk.CTkFrame(
                self,
                fg_color=COLORS["bg_root"],
                corner_radius=8
            )
            frame.pack(fill="x", padx=20, pady=5)

            ctk.CTkLabel(
                frame,
                text=title,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=COLORS["text_main"],
                anchor="w"
            ).pack(fill="x", padx=10, pady=(8, 2))

            ctk.CTkLabel(
                frame,
                text=desc,
                font=ctk.CTkFont(size=10),
                text_color=COLORS["text_sub"],
                anchor="w",
                wraplength=350
            ).pack(fill="x", padx=10, pady=(0, 8))

            ctk.CTkButton(
                frame,
                text="Use This",
                width=70,
                height=24,
                font=ctk.CTkFont(size=10),
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"],
                command=lambda t=title, d=desc: self.use_example(t, d)
            ).pack(anchor="e", padx=10, pady=(0, 8))

        ctk.CTkButton(
            self,
            text="Close",
            command=self.close_dialog,
            fg_color=COLORS["bg_root"],
            hover_color=COLORS["border"],
            width=100
        ).pack(pady=(10, 20))

    def close_dialog(self):
        """Properly close the dialog and release grab."""
        self.grab_release()
        self.destroy()

    def use_example(self, title, desc):
        """Use the selected example."""
        if self.prompt_widget:
            self.prompt_widget.delete("1.0", "end")
            self.prompt_widget.insert("1.0", desc)

        if self.on_select:
            self.on_select(title, desc)

        self.close_dialog()
