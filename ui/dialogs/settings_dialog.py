"""LLM settings dialog for managing API configurations."""
import customtkinter as ctk
from config.themes import COLORS


class SettingsDialog(ctk.CTkToplevel):
    """Settings modal for managing LLM configurations."""

    def __init__(self, master):
        """
        Initialize the settings dialog.

        Args:
            master: Parent widget (App instance)
        """
        super().__init__(master)
        self.master = master
        self.title("LLM Settings")
        self.geometry("700x550")
        self.configure(fg_color=COLORS["bg_root"])
        self.transient(master)
        self.grab_set()

        # Center the window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 350
        y = (self.winfo_screenheight() // 2) - 275
        self.geometry(f"700x550+{x}+{y}")

        # Import config functions
        from config import get_all_llms, add_llm, update_llm, delete_llm, set_current_llm
        self.get_all_llms = get_all_llms
        self.add_llm = add_llm
        self.update_llm = update_llm
        self.delete_llm = delete_llm
        self.set_current_llm = set_current_llm

        # State
        self.editing_llm_id = None

        # Handle window close button (X)
        self.protocol("WM_DELETE_WINDOW", self.close_dialog)

        # Create UI
        self.create_widgets()
        self.refresh_llm_list()
        self.clear_form()

        # Focus on close button
        self.after(100, lambda: self.focus_set())

    def create_widgets(self):
        """Create dialog widgets."""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(30, 20))

        ctk.CTkLabel(
            header_frame,
            text="🔧 LLM Configuration",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["text_main"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_frame,
            text="Add, edit, and select LLM providers for script generation",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_sub"]
        ).pack(anchor="w", pady=(5, 0))

        # Main content - two columns
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)

        # Left column - LLM list
        left_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(
            left_frame,
            text="Your LLMs",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_main"],
            anchor="w"
        ).pack(fill="x", pady=(0, 10))

        self.list_frame = ctk.CTkScrollableFrame(
            left_frame,
            fg_color=COLORS["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
            height=300
        )
        self.list_frame.pack(fill="both", expand=True)

        # Add new button at bottom of left column
        ctk.CTkButton(
            left_frame,
            text="+ Add New LLM",
            command=self.start_adding,
            fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"],
            height=35,
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(fill="x", pady=(10, 0))

        # Right column - Edit form
        right_frame = ctk.CTkFrame(
            content_frame,
            fg_color=COLORS["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"]
        )
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        # Form header
        form_header = ctk.CTkFrame(right_frame, fg_color="transparent")
        form_header.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            form_header,
            text="LLM Details",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_main"]
        ).pack(side="left")

        # Form fields
        form_content = ctk.CTkScrollableFrame(right_frame, fg_color="transparent")
        form_content.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Name
        ctk.CTkLabel(
            form_content,
            text="Name",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["text_sub"],
            anchor="w"
        ).pack(fill="x", pady=(0, 3))

        self.name_entry = ctk.CTkEntry(
            form_content,
            fg_color=COLORS["bg_root"],
            border_color=COLORS["border"],
            height=35
        )
        self.name_entry.pack(fill="x", pady=(0, 12))

        # Endpoint
        ctk.CTkLabel(
            form_content,
            text="API Endpoint",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["text_sub"],
            anchor="w"
        ).pack(fill="x", pady=(0, 3))

        self.endpoint_entry = ctk.CTkEntry(
            form_content,
            fg_color=COLORS["bg_root"],
            border_color=COLORS["border"],
            height=35
        )
        self.endpoint_entry.pack(fill="x", pady=(0, 12))

        # Model
        ctk.CTkLabel(
            form_content,
            text="Model Name",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["text_sub"],
            anchor="w"
        ).pack(fill="x", pady=(0, 3))

        self.model_entry = ctk.CTkEntry(
            form_content,
            fg_color=COLORS["bg_root"],
            border_color=COLORS["border"],
            height=35
        )
        self.model_entry.pack(fill="x", pady=(0, 12))

        # API Key
        ctk.CTkLabel(
            form_content,
            text="API Key",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["text_sub"],
            anchor="w"
        ).pack(fill="x", pady=(0, 3))

        self.api_key_entry = ctk.CTkEntry(
            form_content,
            fg_color=COLORS["bg_root"],
            border_color=COLORS["border"],
            height=35,
            show="•"
        )
        self.api_key_entry.pack(fill="x", pady=(0, 5))

        # Show/hide key
        self.show_key_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            form_content,
            text="Show API Key",
            variable=self.show_key_var,
            command=self.toggle_api_key_visibility,
            checkbox_width=16,
            checkbox_height=16,
            checkmark_color=COLORS["accent"]
        ).pack(anchor="w", pady=(0, 12))

        # Action buttons (outside scrollable area, always visible)
        action_container = ctk.CTkFrame(right_frame, fg_color="transparent")
        action_container.pack(fill="x", padx=15, pady=(0, 15))

        # Mode label
        self.mode_label = ctk.CTkLabel(
            action_container,
            text="Adding new LLM",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_sub"]
        )
        self.mode_label.pack(anchor="w", pady=(0, 8))

        # Button row
        button_row = ctk.CTkFrame(action_container, fg_color="transparent")
        button_row.pack(fill="x")

        ctk.CTkButton(
            button_row,
            text="Cancel",
            width=90,
            command=self.clear_form,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["border"],
            text_color=COLORS["text_main"],
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=(0, 8))

        self.save_btn = ctk.CTkButton(
            button_row,
            text="Add LLM",
            width=120,
            command=self.save_form,
            fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"],
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.save_btn.pack(side="left")

        # Close button at bottom
        ctk.CTkButton(
            self,
            text="Close",
            command=self.close_dialog,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["border"],
            text_color=COLORS["text_main"],
            width=100
        ).pack(pady=(0, 20))

    def toggle_api_key_visibility(self):
        """Toggle API key visibility."""
        self.api_key_entry.configure(
            show="" if self.show_key_var.get() else "•"
        )

    def refresh_llm_list(self):
        """Refresh the LLM list display."""
        # Clear list
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        llms = self.get_all_llms()

        for llm in llms:
            item_frame = ctk.CTkFrame(
                self.list_frame,
                fg_color=COLORS["bg_root"],
                corner_radius=6
            )
            item_frame.pack(fill="x", pady=5, padx=5)

            # Left content
            content_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
            content_frame.pack(side="left", fill="both", expand=True, padx=10, pady=8)

            # Name row
            name_row = ctk.CTkFrame(content_frame, fg_color="transparent")
            name_row.pack(fill="x")

            ctk.CTkLabel(
                name_row,
                text=llm.get("name", "Unnamed"),
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=COLORS["text_main"],
                anchor="w"
            ).pack(side="left")

            if llm.get("is_current"):
                ctk.CTkLabel(
                    name_row,
                    text="● Active",
                    font=ctk.CTkFont(size=10),
                    text_color=COLORS["success"]
                ).pack(side="left", padx=(8, 0))

            # Model row
            ctk.CTkLabel(
                content_frame,
                text=f"Model: {llm.get('model', 'N/A')}",
                font=ctk.CTkFont(size=10),
                text_color=COLORS["text_sub"],
                anchor="w"
            ).pack(fill="x", pady=(2, 0))

            # Right actions
            actions_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
            actions_frame.pack(side="right", padx=5)

            # Select button
            if not llm.get("is_current"):
                ctk.CTkButton(
                    actions_frame,
                    text="▸",
                    width=30,
                    height=30,
                    font=ctk.CTkFont(size=12),
                    fg_color="transparent",
                    hover_color=COLORS["bg_card"],
                    text_color=COLORS["success"],
                    command=lambda lid=llm.get("id"): self.select_llm(lid)
                ).pack(side="left", padx=2)

            # Edit button
            ctk.CTkButton(
                actions_frame,
                text="✎",
                width=30,
                height=30,
                font=ctk.CTkFont(size=12),
                fg_color="transparent",
                hover_color=COLORS["bg_card"],
                text_color=COLORS["accent"],
                command=lambda lid=llm.get("id"): self.edit_llm(lid)
            ).pack(side="left", padx=2)

            # Delete button (only if more than 1 LLM)
            if len(llms) > 1:
                ctk.CTkButton(
                    actions_frame,
                    text="×",
                    width=30,
                    height=30,
                    font=ctk.CTkFont(size=14, weight="bold"),
                    fg_color="transparent",
                    hover_color=COLORS["danger"],
                    text_color=COLORS["danger"],
                    command=lambda lid=llm.get("id"): self.delete_llm_item(lid)
                ).pack(side="left", padx=2)

    def select_llm(self, llm_id):
        """Set an LLM as current."""
        if self.set_current_llm(llm_id):
            self.refresh_llm_list()
            self.clear_form()

    def edit_llm(self, llm_id):
        """Load an LLM into the form for editing."""
        llms = self.get_all_llms()
        llm = next((l for l in llms if l.get("id") == llm_id), None)
        if llm:
            self.editing_llm_id = llm_id
            self.name_entry.delete(0, "end")
            self.name_entry.insert(0, llm.get("name", ""))
            self.endpoint_entry.delete(0, "end")
            self.endpoint_entry.insert(0, llm.get("endpoint", ""))
            self.model_entry.delete(0, "end")
            self.model_entry.insert(0, llm.get("model", ""))
            self.api_key_entry.delete(0, "end")
            self.api_key_entry.insert(0, llm.get("api_key", ""))

            # Update UI for edit mode
            self.mode_label.configure(text=f"Editing '{llm.get('name', 'Unnamed')}'")
            self.save_btn.configure(
                text="Update LLM",
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"]
            )

    def delete_llm_item(self, llm_id):
        """Delete an LLM."""
        llms = self.get_all_llms()
        if len(llms) <= 1:
            return  # Don't allow deleting last LLM

        # Find name for confirmation
        llm = next((l for l in llms if l.get("id") == llm_id), None)
        if llm:
            name = llm.get("name", "this LLM")

            # Simple confirmation via toplevel
            confirm = ctk.CTkToplevel(self)
            confirm.title("Confirm Delete")
            confirm.geometry("300x120")
            confirm.configure(fg_color=COLORS["bg_root"])
            confirm.transient(self)
            confirm.grab_set()

            def close_confirm():
                confirm.grab_release()
                confirm.destroy()

            ctk.CTkLabel(
                confirm,
                text=f"Delete '{name}'?",
                font=ctk.CTkFont(size=13),
                text_color=COLORS["text_main"]
            ).pack(pady=(20, 10))

            btn_frame = ctk.CTkFrame(confirm, fg_color="transparent")
            btn_frame.pack()

            def do_delete():
                if self.delete_llm(llm_id):
                    self.refresh_llm_list()
                    if self.editing_llm_id == llm_id:
                        self.clear_form()
                close_confirm()

            ctk.CTkButton(
                btn_frame,
                text="Delete",
                command=do_delete,
                fg_color=COLORS["danger"],
                hover_color=COLORS["danger_hover"],
                width=80
            ).pack(side="left", padx=5)

            ctk.CTkButton(
                btn_frame,
                text="Cancel",
                command=close_confirm,
                fg_color=COLORS["bg_card"],
                hover_color=COLORS["border"],
                width=80
            ).pack(side="left", padx=5)

    def start_adding(self):
        """Clear form to add a new LLM."""
        self.editing_llm_id = None
        self.clear_form()
        self.name_entry.focus()

    def clear_form(self):
        """Clear the form."""
        self.editing_llm_id = None
        self.name_entry.delete(0, "end")
        self.endpoint_entry.delete(0, "end")
        self.model_entry.delete(0, "end")
        self.api_key_entry.delete(0, "end")

        # Reset UI for add mode
        self.mode_label.configure(text="Adding new LLM")
        self.save_btn.configure(
            text="Add LLM",
            fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"]
        )

    def close_dialog(self):
        """Properly close the dialog and release grab."""
        self.grab_release()
        self.destroy()

    def save_form(self):
        """Save the form data."""
        name = self.name_entry.get().strip()
        endpoint = self.endpoint_entry.get().strip()
        model = self.model_entry.get().strip()
        api_key = self.api_key_entry.get().strip()

        if not name or not endpoint or not model:
            self.show_error("Name, endpoint, and model are required!")
            return

        if self.editing_llm_id:
            # Update existing
            if self.update_llm(self.editing_llm_id, name, endpoint, model, api_key):
                self.refresh_llm_list()
                self.clear_form()
            else:
                self.show_error("Failed to update!")
        else:
            # Add new
            if self.add_llm(name, endpoint, model, api_key):
                self.refresh_llm_list()
                self.clear_form()
            else:
                self.show_error("Failed to save!")

    def show_error(self, message):
        """Show an error message."""
        # Find the form_content frame
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkFrame):
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, ctk.CTkScrollableFrame):
                                ctk.CTkLabel(
                                    grandchild,
                                    text=message,
                                    text_color=COLORS["danger"]
                                ).pack(pady=5)
                                return
