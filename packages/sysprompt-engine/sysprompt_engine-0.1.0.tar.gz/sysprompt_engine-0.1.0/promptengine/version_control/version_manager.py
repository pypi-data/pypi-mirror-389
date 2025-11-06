"""Version control system for prompts."""

import difflib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from promptengine.core.prompt import Prompt, PromptTemplate


class PromptVersion:
    """Represents a single version of a prompt."""

    def __init__(
        self,
        prompt: Union[Prompt, PromptTemplate],
        version_number: int,
        parent_version: Optional[int] = None,
        commit_message: Optional[str] = None,
        author: Optional[str] = None,
    ):
        """
        Initialize a PromptVersion.

        Args:
            prompt: The Prompt or PromptTemplate object
            version_number: Version number
            parent_version: Parent version number (if any)
            commit_message: Optional commit message
            author: Optional author name
        """
        self.version_id = str(uuid4())
        self.version_number = version_number
        self.parent_version = parent_version
        self.prompt_data = prompt.to_dict()
        self.commit_message = commit_message or "No commit message"
        self.author = author or "Unknown"
        self.timestamp = datetime.utcnow().isoformat()
        self.prompt_type = "prompt" if isinstance(prompt, Prompt) else "template"

    def to_dict(self) -> Dict[str, Any]:
        """Convert version to dictionary."""
        return {
            "version_id": self.version_id,
            "version_number": self.version_number,
            "parent_version": self.parent_version,
            "prompt_data": self.prompt_data,
            "prompt_type": self.prompt_type,
            "commit_message": self.commit_message,
            "author": self.author,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptVersion":
        """Create a PromptVersion from a dictionary."""
        # Reconstruct the prompt object
        if data["prompt_type"] == "prompt":
            prompt = Prompt.from_dict(data["prompt_data"])
        else:
            prompt = PromptTemplate.from_dict(data["prompt_data"])

        version = cls(
            prompt=prompt,
            version_number=data["version_number"],
            parent_version=data.get("parent_version"),
            commit_message=data.get("commit_message"),
            author=data.get("author"),
        )
        version.version_id = data["version_id"]
        version.timestamp = data["timestamp"]
        return version


class VersionControl:
    """Manages version control for prompts and templates."""

    def __init__(self, storage_path: Optional[Union[str, Path]] = None):
        """
        Initialize the version control system.

        Args:
            storage_path: Optional path to store version history
        """
        self.storage_path = Path(storage_path) if storage_path else None
        self.version_histories: Dict[str, List[PromptVersion]] = {}
        self.current_versions: Dict[str, int] = {}

        if self.storage_path and self.storage_path.exists():
            self.load()

    def save_version(
        self,
        prompt: Union[Prompt, PromptTemplate],
        commit_message: Optional[str] = None,
        author: Optional[str] = None,
    ) -> str:
        """
        Save a new version of a prompt or template.

        Args:
            prompt: Prompt or PromptTemplate to version
            commit_message: Optional commit message
            author: Optional author name

        Returns:
            Version ID of the saved version
        """
        prompt_id = prompt.id

        # Initialize version history if needed
        if prompt_id not in self.version_histories:
            self.version_histories[prompt_id] = []
            self.current_versions[prompt_id] = 0

        # Get version number
        version_number = len(self.version_histories[prompt_id]) + 1
        parent_version = version_number - 1 if version_number > 1 else None

        # Create new version
        version = PromptVersion(
            prompt=prompt,
            version_number=version_number,
            parent_version=parent_version,
            commit_message=commit_message,
            author=author,
        )

        # Add to history
        self.version_histories[prompt_id].append(version)
        self.current_versions[prompt_id] = version_number

        # Auto-save if storage path is set
        if self.storage_path:
            self.save()

        return version.version_id

    def get_version(
        self, prompt_id: str, version_number: Optional[int] = None
    ) -> Optional[Union[Prompt, PromptTemplate]]:
        """
        Get a specific version of a prompt.

        Args:
            prompt_id: ID of the prompt
            version_number: Version number (defaults to latest)

        Returns:
            Prompt or PromptTemplate object, or None if not found
        """
        if prompt_id not in self.version_histories:
            return None

        if version_number is None:
            version_number = self.current_versions.get(prompt_id, 1)

        # Find the version
        for version in self.version_histories[prompt_id]:
            if version.version_number == version_number:
                if version.prompt_type == "prompt":
                    return Prompt.from_dict(version.prompt_data)
                else:
                    return PromptTemplate.from_dict(version.prompt_data)

        return None

    def get_history(self, prompt_id: str) -> List[Dict[str, Any]]:
        """
        Get the version history for a prompt.

        Args:
            prompt_id: ID of the prompt

        Returns:
            List of version metadata dictionaries
        """
        if prompt_id not in self.version_histories:
            return []

        return [
            {
                "version_number": v.version_number,
                "version_id": v.version_id,
                "commit_message": v.commit_message,
                "author": v.author,
                "timestamp": v.timestamp,
                "prompt_type": v.prompt_type,
            }
            for v in self.version_histories[prompt_id]
        ]

    def rollback(
        self, prompt_id: str, version_number: int
    ) -> Optional[Union[Prompt, PromptTemplate]]:
        """
        Rollback to a specific version.

        Args:
            prompt_id: ID of the prompt
            version_number: Version number to rollback to

        Returns:
            The rolled-back Prompt or PromptTemplate, or None if not found
        """
        prompt = self.get_version(prompt_id, version_number)
        if prompt:
            self.current_versions[prompt_id] = version_number
            if self.storage_path:
                self.save()
        return prompt

    def diff(
        self, prompt_id: str, version1: int, version2: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get the diff between two versions.

        Args:
            prompt_id: ID of the prompt
            version1: First version number
            version2: Second version number

        Returns:
            Dictionary with diff information, or None if versions not found
        """
        v1 = self.get_version(prompt_id, version1)
        v2 = self.get_version(prompt_id, version2)

        if not v1 or not v2:
            return None

        # Get content based on type
        if isinstance(v1, Prompt):
            content1 = v1.content
            content2 = v2.content
        else:
            content1 = v1.template_str
            content2 = v2.template_str

        # Generate unified diff
        diff = list(
            difflib.unified_diff(
                content1.splitlines(keepends=True),
                content2.splitlines(keepends=True),
                fromfile=f"Version {version1}",
                tofile=f"Version {version2}",
            )
        )

        return {
            "prompt_id": prompt_id,
            "version1": version1,
            "version2": version2,
            "diff": "".join(diff),
            "changes": len([line for line in diff if line.startswith(("+", "-"))]),
        }

    def list_prompts(self) -> List[str]:
        """List all prompt IDs with version history."""
        return list(self.version_histories.keys())

    def delete_history(self, prompt_id: str) -> bool:
        """
        Delete the entire version history for a prompt.

        Args:
            prompt_id: ID of the prompt

        Returns:
            True if deleted, False if not found
        """
        if prompt_id in self.version_histories:
            del self.version_histories[prompt_id]
            del self.current_versions[prompt_id]
            if self.storage_path:
                self.save()
            return True
        return False

    def save(self) -> None:
        """Save version control data to storage."""
        if not self.storage_path:
            raise ValueError("No storage path configured")

        # Ensure parent directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version_histories": {
                prompt_id: [v.to_dict() for v in versions]
                for prompt_id, versions in self.version_histories.items()
            },
            "current_versions": self.current_versions,
        }

        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self) -> None:
        """Load version control data from storage."""
        if not self.storage_path or not self.storage_path.exists():
            return

        with open(self.storage_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.version_histories = {}
        for prompt_id, versions_data in data.get("version_histories", {}).items():
            self.version_histories[prompt_id] = [
                PromptVersion.from_dict(v) for v in versions_data
            ]

        self.current_versions = data.get("current_versions", {})

    def stats(self) -> Dict[str, Any]:
        """Get statistics about version control."""
        total_versions = sum(len(v) for v in self.version_histories.values())
        return {
            "total_prompts": len(self.version_histories),
            "total_versions": total_versions,
            "prompts": [
                {
                    "prompt_id": pid,
                    "version_count": len(versions),
                    "current_version": self.current_versions.get(pid, 0),
                }
                for pid, versions in self.version_histories.items()
            ],
        }

    def __str__(self) -> str:
        return f"VersionControl(prompts={len(self.version_histories)}, total_versions={sum(len(v) for v in self.version_histories.values())})"

    def __repr__(self) -> str:
        return self.__str__()
