"""Script version control and backup management."""
import os
import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class ScriptVersion:
    """Represents a single script version."""

    def __init__(self, version_number: int, script_path: str, metadata: Dict):
        self.version_number = version_number
        self.script_path = script_path
        self.metadata = metadata

    @property
    def timestamp(self) -> str:
        return self.metadata.get("timestamp", "")

    @property
    def change_description(self) -> str:
        return self.metadata.get("change_description", "No description")

    @property
    def editor_type(self) -> str:
        return self.metadata.get("editor_type", "unknown")

    @property
    def created_at(self) -> datetime:
        ts = self.metadata.get("timestamp", "")
        try:
            return datetime.strptime(ts, "%Y%m%d_%H%M%S")
        except:
            return datetime.now()


class ScriptVersionManager:
    """Manages script versioning and backups."""

    MAX_VERSIONS = 10
    VERSIONS_DIR = ".script_versions"

    def __init__(self):
        self._ensure_versions_dir()

    def _ensure_versions_dir(self):
        """Create versions directory if it doesn't exist."""
        versions_dir = Path(self.VERSIONS_DIR)
        if not versions_dir.exists():
            versions_dir.mkdir(parents=True, exist_ok=True)

            # Create .gitignore to exclude version backups
            gitignore = versions_dir / ".gitignore"
            if not gitignore.exists():
                gitignore.write_text("*\n")

    def _get_script_versions_dir(self, script_filename: str) -> Path:
        """Get version directory for a specific script."""
        return Path(self.VERSIONS_DIR) / script_filename

    def _get_metadata_path(self, script_filename: str) -> Path:
        """Get metadata file path for a script."""
        return self._get_script_versions_dir(script_filename) / "versions.json"

    def _load_metadata(self, script_filename: str) -> Dict:
        """Load version metadata for a script."""
        metadata_path = self._get_metadata_path(script_filename)
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"versions": {}}

    def _save_metadata(self, script_filename: str, metadata: Dict):
        """Save version metadata for a script."""
        metadata_path = self._get_metadata_path(script_filename)
        script_dir = metadata_path.parent
        if not script_dir.exists():
            script_dir.mkdir(parents=True, exist_ok=True)

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

    def create_backup(
        self,
        script_path: str,
        change_description: str = "",
        editor_type: str = "manual"
    ) -> Optional[ScriptVersion]:
        """
        Create a backup of a script before editing.

        Args:
            script_path: Path to the script file
            change_description: Description of the changes being made
            editor_type: Type of editor ('manual', 'llm', 'external')

        Returns:
            ScriptVersion object if backup created, None otherwise
        """
        script_path_obj = Path(script_path)
        if not script_path_obj.exists():
            return None

        script_filename = script_path_obj.stem
        metadata = self._load_metadata(script_filename)

        # Get next version number
        version_numbers = [int(v) for v in metadata["versions"].keys()] if metadata["versions"] else [0]
        next_version = max(version_numbers) + 1 if version_numbers else 1

        # Create timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Copy script to versions directory
        versions_dir = self._get_script_versions_dir(script_filename)
        if not versions_dir.exists():
            versions_dir.mkdir(parents=True, exist_ok=True)

        backup_filename = f"v{next_version}_{timestamp}.py"
        backup_path = versions_dir / backup_filename

        try:
            shutil.copy2(script_path, backup_path)

            # Save metadata
            version_metadata = {
                "timestamp": timestamp,
                "change_description": change_description,
                "editor_type": editor_type,
                "backup_file": backup_filename
            }
            metadata["versions"][str(next_version)] = version_metadata

            # Prune old versions if needed
            version_keys = sorted(metadata["versions"].keys(), key=int, reverse=True)
            if len(version_keys) > self.MAX_VERSIONS:
                for old_version in version_keys[self.MAX_VERSIONS:]:
                    old_metadata = metadata["versions"][old_version]
                    old_backup = versions_dir / old_metadata["backup_file"]
                    if old_backup.exists():
                        old_backup.unlink()
                    del metadata["versions"][old_version]

            self._save_metadata(script_filename, metadata)

            return ScriptVersion(next_version, str(backup_path), version_metadata)

        except Exception as e:
            print(f"Error creating backup: {e}")
            return None

    def get_versions(self, script_filename: str) -> List[ScriptVersion]:
        """
        Get all versions for a script.

        Args:
            script_filename: Script filename without .py extension

        Returns:
            List of ScriptVersion objects, sorted by version number (newest first)
        """
        metadata = self._load_metadata(script_filename)
        versions = []
        versions_dir = self._get_script_versions_dir(script_filename)

        for version_str, version_metadata in metadata["versions"].items():
            version_num = int(version_str)
            backup_file = version_metadata.get("backup_file", "")
            backup_path = versions_dir / backup_file if backup_file else None

            if backup_path and backup_path.exists():
                versions.append(ScriptVersion(
                    version_num,
                    str(backup_path),
                    version_metadata
                ))

        # Sort by version number, newest first
        versions.sort(key=lambda v: v.version_number, reverse=True)
        return versions

    def restore_version(
        self,
        script_path: str,
        version: ScriptVersion
    ) -> bool:
        """
        Restore a script from a version backup.

        Args:
            script_path: Path to the current script file
            version: ScriptVersion to restore

        Returns:
            True if restore successful, False otherwise
        """
        try:
            # First, backup the current version before restoring
            self.create_backup(
                script_path,
                change_description=f"Before reverting to v{version.version_number}",
                editor_type="auto"
            )

            # Copy version backup to script location
            shutil.copy2(version.script_path, script_path)
            return True

        except Exception as e:
            print(f"Error restoring version: {e}")
            return False

    def delete_all_versions(self, script_filename: str):
        """
        Delete all versions for a script.

        Args:
            script_filename: Script filename without .py extension
        """
        versions_dir = self._get_script_versions_dir(script_filename)
        if versions_dir.exists():
            shutil.rmtree(versions_dir)
