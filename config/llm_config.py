"""
Configuration management for LLM-powered script generation.

Stores multiple API configurations persistently in user's home directory.
"""
import json
import os
from pathlib import Path
from typing import Optional, List


# Config file location
CONFIG_DIR = Path.home() / ".yofardev_toolbox"
CONFIG_FILE = CONFIG_DIR / "llm_config.json"


# Default LLM configurations
DEFAULT_LLMS = [
    {
        "id": "openai-gpt4o",
        "name": "OpenAI GPT-4o",
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o",
        "api_key": ""
    },
    {
        "id": "ollama-local",
        "name": "Ollama (Local)",
        "endpoint": "http://localhost:11434/v1/chat/completions",
        "model": "llama3",
        "api_key": ""
    }
]


def get_all_llms() -> List[dict]:
    """
    Load all LLM configurations from disk.

    Returns:
        list: List of LLM configuration dictionaries
    """
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                llms = data.get("llms", [])
                current_id = data.get("current_llm_id")
                # Mark the current one
                for llm in llms:
                    llm["is_current"] = llm.get("id") == current_id
                return llms
        except (json.JSONDecodeError, IOError):
            pass
    # Return defaults if no config file
    return [{"is_current": i == 0, **llm} for i, llm in enumerate(DEFAULT_LLMS)]


def get_current_llm() -> Optional[dict]:
    """
    Get the currently selected LLM configuration.

    Returns:
        dict or None: Current LLM config, or None if not found
    """
    llms = get_all_llms()
    for llm in llms:
        if llm.get("is_current"):
            return llm
    # Return first LLM if none marked as current
    return llms[0] if llms else None


def save_llms(llms: List[dict]) -> bool:
    """
    Save all LLM configurations to disk.

    Args:
        llms: List of LLM configuration dictionaries

    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        # Create config directory if it doesn't exist
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # Find current LLM ID
        current_id = None
        for llm in llms:
            if llm.get("is_current"):
                current_id = llm.get("id")
                break

        # If no current, set first as current
        if not current_id and llms:
            current_id = llms[0].get("id")

        # Remove is_current from saved data
        llms_to_save = [{k: v for k, v in llm.items() if k != "is_current"} for llm in llms]

        data = {
            "llms": llms_to_save,
            "current_llm_id": current_id
        }

        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except (IOError, OSError):
        return False


def add_llm(name: str, endpoint: str, model: str, api_key: str) -> bool:
    """
    Add a new LLM configuration.

    Args:
        name: Display name for the LLM
        endpoint: API endpoint URL
        model: Model name
        api_key: API key

    Returns:
        bool: True if saved successfully, False otherwise
    """
    llms = get_all_llms()

    # Create a unique ID
    base_id = name.lower().replace(" ", "-").replace("/", "-")
    llm_id = base_id
    counter = 1
    while any(llm.get("id") == llm_id for llm in llms):
        llm_id = f"{base_id}-{counter}"
        counter += 1

    new_llm = {
        "id": llm_id,
        "name": name,
        "endpoint": endpoint,
        "model": model,
        "api_key": api_key
    }

    # Add to list (not set as current)
    llms.append(new_llm)

    return save_llms(llms)


def update_llm(llm_id: str, name: str, endpoint: str, model: str, api_key: str) -> bool:
    """
    Update an existing LLM configuration.

    Args:
        llm_id: ID of the LLM to update
        name: New display name
        endpoint: New API endpoint URL
        model: New model name
        api_key: New API key

    Returns:
        bool: True if saved successfully, False otherwise
    """
    llms = get_all_llms()

    for llm in llms:
        if llm.get("id") == llm_id:
            llm["name"] = name
            llm["endpoint"] = endpoint
            llm["model"] = model
            llm["api_key"] = api_key
            return save_llms(llms)

    return False


def delete_llm(llm_id: str) -> bool:
    """
    Delete an LLM configuration.

    Args:
        llm_id: ID of the LLM to delete

    Returns:
        bool: True if saved successfully, False otherwise
    """
    llms = get_all_llms()

    # Don't allow deleting the last LLM
    if len(llms) <= 1:
        return False

    # Check if we're deleting the current one
    was_current = False
    for llm in llms:
        if llm.get("id") == llm_id:
            was_current = llm.get("is_current", False)
            break

    # Remove the LLM
    llms = [llm for llm in llms if llm.get("id") != llm_id]

    # If we deleted the current one, mark the first as current
    if was_current and llms:
        llms[0]["is_current"] = True

    return save_llms(llms)


def set_current_llm(llm_id: str) -> bool:
    """
    Set the currently active LLM configuration.

    Args:
        llm_id: ID of the LLM to set as current

    Returns:
        bool: True if saved successfully, False otherwise
    """
    llms = get_all_llms()

    # Update current status
    for llm in llms:
        llm["is_current"] = (llm.get("id") == llm_id)

    return save_llms(llms)


# Legacy functions for backward compatibility
def get_config() -> dict:
    """Legacy: Get current LLM config as a simple dict."""
    llm = get_current_llm()
    if llm:
        return {
            "endpoint": llm.get("endpoint", ""),
            "model": llm.get("model", ""),
            "api_key": llm.get("api_key", "")
        }
    return {"endpoint": "", "model": "", "api_key": ""}


def save_config(config: dict) -> bool:
    """Legacy: Update current LLM config (for backward compatibility)."""
    llms = get_all_llms()
    if llms:
        # Update the current LLM
        for llm in llms:
            if llm.get("is_current"):
                llm["endpoint"] = config.get("endpoint", llm.get("endpoint", ""))
                llm["model"] = config.get("model", llm.get("model", ""))
                llm["api_key"] = config.get("api_key", llm.get("api_key", ""))
                break
        return save_llms(llms)
    return False
