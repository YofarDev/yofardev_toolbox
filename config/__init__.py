"""Configuration module for Yofardev Toolbox."""
from .app_config import APP_NAME, APP_VERSION, WINDOW_SIZE, SCRIPTS_DIR, SKIP_FILES
from .themes import COLORS, FONTS
from .llm_config import (
    get_all_llms,
    get_current_llm,
    set_current_llm,
    add_llm,
    update_llm,
    delete_llm,
    get_config,
    save_config
)

__all__ = [
    "APP_NAME", "APP_VERSION", "WINDOW_SIZE", "SCRIPTS_DIR", "SKIP_FILES",
    "COLORS", "FONTS",
    "get_all_llms", "get_current_llm", "set_current_llm",
    "add_llm", "update_llm", "delete_llm",
    "get_config", "save_config"
]
