"""UI themes and color schemes."""
import customtkinter as ctk

# Configure CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Modern Color Palette
COLORS = {
    "bg_root": "#1a1a1a",       # Very dark grey for main background
    "bg_sidebar": "#111111",    # Black/Darker for sidebar
    "bg_card": "#242424",       # Card background
    "accent": "#1f6aa5",        # Primary Blue
    "accent_hover": "#144870",
    "text_main": "#ffffff",
    "text_sub": "#a0a0a0",
    "success": "#2b825b",       # Green
    "success_hover": "#1e5c40",
    "danger": "#c42b1c",        # Red
    "danger_hover": "#8a1f15",
    "border": "#333333"
}

# Font definitions
FONTS = {
    "header_large": ("Roboto", 28, "bold"),
    "header_medium": ("Roboto", 15, "bold"),
    "body": ("Roboto", 13),
    "body_small": ("Roboto", 11),
    "code": ("Consolas", 13)
}

def get_font(name: str) -> tuple:
    """Get a font by name."""
    return FONTS.get(name, ("Roboto", 12))
