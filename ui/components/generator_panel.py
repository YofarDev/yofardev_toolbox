"""LLM script generator panel - simplified version for refactored app."""
import customtkinter as ctk
import os
import threading
from config.themes import COLORS
from config import get_config
from core.llm_generator import ScriptGenerator, GenerationError, APIError, ValidationError


class GeneratorPanel(ctk.CTkFrame):
    """Panel for generating scripts with LLM."""

    def __init__(self, master, scripts, on_complete, on_cancel, on_log=None):
        """
        Initialize the generator panel.

        Args:
            master: Parent widget
            scripts: List of available scripts
            on_complete: Callback when generation completes (script_filename)
            on_cancel: Callback when user cancels
            on_log: Callback for logging messages (message)
        """
        super().__init__(master, fg_color="transparent")
        self.scripts = scripts
        self.on_complete = on_complete
        self.on_cancel = on_cancel
        self.on_log = on_log or (lambda msg: None)
        self.generator_widgets = {}

        self.create_widgets()

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
            text="Describe the image processing script you want to create",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_sub"],
            anchor="w"
        )
        desc.pack(fill="x", pady=(0, 20))

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

        placeholder = """Describe the image processing script you want to create...

Examples:
• "Add a vintage film grain effect with adjustable intensity"
• "Create a script that generates polaroid-style frames"
• "Build a tool that adds timestamps to images"
"""
        self.prompt_text.insert("1.0", placeholder)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x")

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=100,
            command=self.on_cancel,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["border"],
            text_color=COLORS["text_main"]
        )
        cancel_btn.pack(side="left", padx=(0, 10))

        self.generate_btn = ctk.CTkButton(
            btn_frame,
            text="Generate Script",
            width=150,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.generate,
            fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"]
        )
        self.generate_btn.pack(side="left")

    def generate(self):
        """Generate a script using the LLM API."""
        prompt = self.prompt_text.get("1.0", "end").strip()
        if not prompt or prompt.startswith("Describe the image processing"):
            self.on_log("❌ Please enter a description of the script you want to create.")
            return

        # Check API config
        config = get_config()
        if not config.get("api_key"):
            self.on_log("❌ API key not configured. Please open Settings (⚙) and enter your API key.")
            return

        # Update UI state
        self.generate_btn.configure(state="disabled", text="Generating...")
        self.on_log(f"🔄 Generating script...")
        self.on_log(f"   Connecting to {config.get('model')} API...")

        # Run in background thread
        threading.Thread(
            target=self._run_generation,
            args=(prompt, config),
            daemon=True
        ).start()

    def _run_generation(self, prompt, config):
        """Run generation in background thread."""
        try:
            generator = ScriptGenerator(
                endpoint=config["endpoint"],
                model=config["model"],
                api_key=config["api_key"]
            )

            self.on_log("   Sending request to LLM...")

            result = generator.generate_script(user_prompt=prompt)

            self.on_log("   ✓ Script generated successfully!")

            # Save script
            from core.llm_generator import ScriptGenerator as SG
            script_name_slug = SG.sanitize_filename(result["name"])
            script_filename = script_name_slug
            script_path = os.path.join("scripts", f"{script_filename}.py")

            with open(script_path, "w") as f:
                f.write(result["code"])

            self.on_log(f"   ✓ Saved to: {script_path}")
            self.on_log(f"\n✅ Script '{result['name']}' created successfully!")

            # Call completion callback
            self.on_complete(script_filename)

        except APIError as e:
            self.on_log(f"\n❌ API Error: {e}")
            self._reset_button()
        except ValidationError as e:
            self.on_log(f"\n❌ Validation Error: {e}")
            self.on_log("   The generated script didn't meet requirements. Please try again.")
            self._reset_button()
        except Exception as e:
            self.on_log(f"\n❌ Error: {e}")
            self._reset_button()

    def _reset_button(self):
        """Reset generate button state."""
        if hasattr(self, 'generate_btn'):
            self.after(0, lambda: self.generate_btn.configure(
                state="normal",
                text="Generate Script",
                fg_color=COLORS["success"]
            ))
