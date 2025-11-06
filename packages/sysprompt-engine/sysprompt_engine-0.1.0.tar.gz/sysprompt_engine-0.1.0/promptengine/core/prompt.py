"""Core prompt classes for PromptEngine."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from jinja2 import Template, TemplateSyntaxError


class Prompt:
    """Represents a system prompt with metadata."""

    def __init__(
        self,
        content: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        prompt_id: Optional[str] = None,
    ):
        """
        Initialize a Prompt.

        Args:
            content: The actual prompt text
            name: Optional name for the prompt
            description: Optional description
            metadata: Optional metadata dictionary
            tags: Optional list of tags
            prompt_id: Optional unique ID (generated if not provided)
        """
        self.id = prompt_id or str(uuid4())
        self.content = content
        self.name = name or f"prompt_{self.id[:8]}"
        self.description = description or ""
        self.metadata = metadata or {}
        self.tags = tags or []
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = self.created_at

    def update_content(self, new_content: str) -> None:
        """Update the prompt content and timestamp."""
        self.content = new_content
        self.updated_at = datetime.utcnow().isoformat()

    def add_tag(self, tag: str) -> None:
        """Add a tag to the prompt."""
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the prompt."""
        if tag in self.tags:
            self.tags.remove(tag)

    def to_dict(self) -> Dict[str, Any]:
        """Convert prompt to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "content": self.content,
            "description": self.description,
            "metadata": self.metadata,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert prompt to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Prompt":
        """Create a Prompt from a dictionary."""
        prompt = cls(
            content=data["content"],
            name=data.get("name"),
            description=data.get("description"),
            metadata=data.get("metadata"),
            tags=data.get("tags"),
            prompt_id=data.get("id"),
        )
        prompt.created_at = data.get("created_at", prompt.created_at)
        prompt.updated_at = data.get("updated_at", prompt.updated_at)
        return prompt

    @classmethod
    def from_json(cls, json_str: str) -> "Prompt":
        """Create a Prompt from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    def __str__(self) -> str:
        return f"Prompt(name='{self.name}', id='{self.id[:8]}...', tags={self.tags})"

    def __repr__(self) -> str:
        return self.__str__()


class PromptTemplate:
    """A template for creating prompts with variable substitution."""

    def __init__(
        self,
        template: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        variables: Optional[List[str]] = None,
        default_values: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        template_id: Optional[str] = None,
    ):
        """
        Initialize a PromptTemplate.

        Args:
            template: Jinja2 template string
            name: Optional name for the template
            description: Optional description
            variables: Optional list of expected variables
            default_values: Optional default values for variables
            metadata: Optional metadata dictionary
            tags: Optional list of tags
            template_id: Optional unique ID (generated if not provided)
        """
        self.id = template_id or str(uuid4())
        self.template_str = template
        self.name = name or f"template_{self.id[:8]}"
        self.description = description or ""
        self.variables = variables or []
        self.default_values = default_values or {}
        self.metadata = metadata or {}
        self.tags = tags or []
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = self.created_at

        try:
            self._template = Template(template)
        except TemplateSyntaxError as e:
            raise ValueError(f"Invalid Jinja2 template: {e}")

    def render(self, **kwargs) -> Prompt:
        """
        Render the template with provided variables.

        Args:
            **kwargs: Variable values to substitute

        Returns:
            A Prompt object with rendered content
        """
        # Merge default values with provided kwargs
        render_vars = {**self.default_values, **kwargs}

        # Check for missing required variables
        missing = set(self.variables) - set(render_vars.keys())
        if missing:
            raise ValueError(f"Missing required variables: {missing}")

        try:
            content = self._template.render(**render_vars)
        except Exception as e:
            raise ValueError(f"Template rendering failed: {e}")

        # Create a prompt with the rendered content
        prompt = Prompt(
            content=content,
            name=f"{self.name}_rendered",
            description=f"Rendered from template: {self.name}",
            metadata={
                "template_id": self.id,
                "template_name": self.name,
                "render_variables": render_vars,
            },
            tags=self.tags.copy(),
        )
        return prompt

    def validate_variables(self, **kwargs) -> tuple[bool, List[str]]:
        """
        Validate that all required variables are provided.

        Args:
            **kwargs: Variable values to check

        Returns:
            Tuple of (is_valid, missing_variables)
        """
        provided_vars = {**self.default_values, **kwargs}
        missing = [v for v in self.variables if v not in provided_vars]
        return len(missing) == 0, missing

    def update_template(self, new_template: str) -> None:
        """Update the template string."""
        try:
            self._template = Template(new_template)
            self.template_str = new_template
            self.updated_at = datetime.utcnow().isoformat()
        except TemplateSyntaxError as e:
            raise ValueError(f"Invalid Jinja2 template: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "template": self.template_str,
            "description": self.description,
            "variables": self.variables,
            "default_values": self.default_values,
            "metadata": self.metadata,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert template to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptTemplate":
        """Create a PromptTemplate from a dictionary."""
        template = cls(
            template=data["template"],
            name=data.get("name"),
            description=data.get("description"),
            variables=data.get("variables"),
            default_values=data.get("default_values"),
            metadata=data.get("metadata"),
            tags=data.get("tags"),
            template_id=data.get("id"),
        )
        template.created_at = data.get("created_at", template.created_at)
        template.updated_at = data.get("updated_at", template.updated_at)
        return template

    @classmethod
    def from_json(cls, json_str: str) -> "PromptTemplate":
        """Create a PromptTemplate from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    def __str__(self) -> str:
        return f"PromptTemplate(name='{self.name}', variables={self.variables})"

    def __repr__(self) -> str:
        return self.__str__()
