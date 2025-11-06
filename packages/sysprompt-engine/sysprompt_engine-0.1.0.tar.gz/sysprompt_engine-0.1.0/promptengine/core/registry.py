"""Registry for managing prompts and templates."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Union

import yaml

from promptengine.core.prompt import Prompt, PromptTemplate


class PromptRegistry:
    """Manages a collection of prompts and templates."""

    def __init__(self):
        """Initialize an empty registry."""
        self.prompts: Dict[str, Prompt] = {}
        self.templates: Dict[str, PromptTemplate] = {}

    def add(self, item: Union[Prompt, PromptTemplate], overwrite: bool = False) -> None:
        """
        Add a prompt or template to the registry.

        Args:
            item: Prompt or PromptTemplate to add
            overwrite: Whether to overwrite if item with same name exists

        Raises:
            ValueError: If item with same name exists and overwrite is False
        """
        if isinstance(item, Prompt):
            if item.name in self.prompts and not overwrite:
                raise ValueError(f"Prompt with name '{item.name}' already exists")
            self.prompts[item.name] = item
        elif isinstance(item, PromptTemplate):
            if item.name in self.templates and not overwrite:
                raise ValueError(f"Template with name '{item.name}' already exists")
            self.templates[item.name] = item
        else:
            raise TypeError("Item must be a Prompt or PromptTemplate")

    def remove_prompt(self, name: str) -> bool:
        """
        Remove a prompt by name.

        Args:
            name: Name of the prompt to remove

        Returns:
            True if removed, False if not found
        """
        if name in self.prompts:
            del self.prompts[name]
            return True
        return False

    def remove_template(self, name: str) -> bool:
        """
        Remove a template by name.

        Args:
            name: Name of the template to remove

        Returns:
            True if removed, False if not found
        """
        if name in self.templates:
            del self.templates[name]
            return True
        return False

    def get_prompt(self, name: str) -> Optional[Prompt]:
        """Get a prompt by name."""
        return self.prompts.get(name)

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Get a template by name."""
        return self.templates.get(name)

    def list_prompts(self, tag: Optional[str] = None) -> List[str]:
        """
        List all prompt names, optionally filtered by tag.

        Args:
            tag: Optional tag to filter by

        Returns:
            List of prompt names
        """
        if tag:
            return [
                name for name, prompt in self.prompts.items() if tag in prompt.tags
            ]
        return list(self.prompts.keys())

    def list_templates(self, tag: Optional[str] = None) -> List[str]:
        """
        List all template names, optionally filtered by tag.

        Args:
            tag: Optional tag to filter by

        Returns:
            List of template names
        """
        if tag:
            return [
                name
                for name, template in self.templates.items()
                if tag in template.tags
            ]
        return list(self.templates.keys())

    def search(self, query: str) -> Dict[str, List[str]]:
        """
        Search for prompts and templates by name, description, or tags.

        Args:
            query: Search query string

        Returns:
            Dictionary with 'prompts' and 'templates' keys containing matching names
        """
        query_lower = query.lower()
        results = {"prompts": [], "templates": []}

        for name, prompt in self.prompts.items():
            if (
                query_lower in name.lower()
                or query_lower in prompt.description.lower()
                or any(query_lower in tag.lower() for tag in prompt.tags)
            ):
                results["prompts"].append(name)

        for name, template in self.templates.items():
            if (
                query_lower in name.lower()
                or query_lower in template.description.lower()
                or any(query_lower in tag.lower() for tag in template.tags)
            ):
                results["templates"].append(name)

        return results

    def save(self, filepath: Union[str, Path], format: str = "json") -> None:
        """
        Save the registry to a file.

        Args:
            filepath: Path to save file
            format: 'json' or 'yaml'

        Raises:
            ValueError: If format is not supported
        """
        filepath = Path(filepath)
        data = {
            "prompts": [p.to_dict() for p in self.prompts.values()],
            "templates": [t.to_dict() for t in self.templates.values()],
        }

        if format == "json":
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        elif format == "yaml":
            with open(filepath, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'json' or 'yaml'")

    def load(self, filepath: Union[str, Path], format: str = "json") -> None:
        """
        Load the registry from a file.

        Args:
            filepath: Path to load file
            format: 'json' or 'yaml'

        Raises:
            ValueError: If format is not supported
            FileNotFoundError: If file doesn't exist
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        if format == "json":
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        elif format == "yaml":
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'json' or 'yaml'")

        # Clear existing data
        self.prompts.clear()
        self.templates.clear()

        # Load prompts
        for prompt_data in data.get("prompts", []):
            prompt = Prompt.from_dict(prompt_data)
            self.prompts[prompt.name] = prompt

        # Load templates
        for template_data in data.get("templates", []):
            template = PromptTemplate.from_dict(template_data)
            self.templates[template.name] = template

    def export_prompt(self, name: str, filepath: Union[str, Path]) -> None:
        """
        Export a single prompt to a file.

        Args:
            name: Name of the prompt to export
            filepath: Path to save file

        Raises:
            ValueError: If prompt not found
        """
        prompt = self.get_prompt(name)
        if not prompt:
            raise ValueError(f"Prompt '{name}' not found")

        filepath = Path(filepath)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(prompt.to_json())

    def export_template(self, name: str, filepath: Union[str, Path]) -> None:
        """
        Export a single template to a file.

        Args:
            name: Name of the template to export
            filepath: Path to save file

        Raises:
            ValueError: If template not found
        """
        template = self.get_template(name)
        if not template:
            raise ValueError(f"Template '{name}' not found")

        filepath = Path(filepath)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(template.to_json())

    def import_prompt(self, filepath: Union[str, Path], overwrite: bool = False) -> None:
        """
        Import a prompt from a file.

        Args:
            filepath: Path to import from
            overwrite: Whether to overwrite if prompt exists
        """
        filepath = Path(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            prompt = Prompt.from_json(f.read())
        self.add(prompt, overwrite=overwrite)

    def import_template(
        self, filepath: Union[str, Path], overwrite: bool = False
    ) -> None:
        """
        Import a template from a file.

        Args:
            filepath: Path to import from
            overwrite: Whether to overwrite if template exists
        """
        filepath = Path(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            template = PromptTemplate.from_json(f.read())
        self.add(template, overwrite=overwrite)

    def clear(self) -> None:
        """Clear all prompts and templates from the registry."""
        self.prompts.clear()
        self.templates.clear()

    def stats(self) -> Dict[str, int]:
        """Get statistics about the registry."""
        return {
            "total_prompts": len(self.prompts),
            "total_templates": len(self.templates),
            "total_items": len(self.prompts) + len(self.templates),
        }

    def __str__(self) -> str:
        stats = self.stats()
        return f"PromptRegistry(prompts={stats['total_prompts']}, templates={stats['total_templates']})"

    def __repr__(self) -> str:
        return self.__str__()
