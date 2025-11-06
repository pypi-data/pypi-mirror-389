"""Unit tests for prompt module."""

import pytest
from promptengine.core.prompt import Prompt, PromptTemplate


def test_prompt_creation():
    """Test creating a basic prompt."""
    prompt = Prompt(
        name="test_prompt",
        content="Test content",
        description="Test description",
        tags=["test"],
    )

    assert prompt.name == "test_prompt"
    assert prompt.content == "Test content"
    assert prompt.description == "Test description"
    assert "test" in prompt.tags


def test_prompt_serialization():
    """Test prompt to/from dict and JSON."""
    prompt = Prompt(name="test", content="Test content", tags=["tag1"])

    # To dict
    data = prompt.to_dict()
    assert data["name"] == "test"
    assert data["content"] == "Test content"

    # From dict
    loaded = Prompt.from_dict(data)
    assert loaded.name == prompt.name
    assert loaded.content == prompt.content
    assert loaded.id == prompt.id


def test_prompt_update():
    """Test updating prompt content."""
    prompt = Prompt(name="test", content="Original")
    original_time = prompt.updated_at

    prompt.update_content("Updated")

    assert prompt.content == "Updated"
    assert prompt.updated_at != original_time


def test_template_creation():
    """Test creating a prompt template."""
    template = PromptTemplate(
        name="test_template",
        template="Hello {{name}}, you are {{age}} years old.",
        variables=["name", "age"],
    )

    assert template.name == "test_template"
    assert template.variables == ["name", "age"]


def test_template_rendering():
    """Test rendering a template."""
    template = PromptTemplate(
        name="greeting",
        template="Hello {{name}}!",
        variables=["name"],
    )

    prompt = template.render(name="Alice")
    assert "Hello Alice!" in prompt.content


def test_template_missing_variables():
    """Test template with missing required variables."""
    template = PromptTemplate(
        name="test",
        template="{{var1}} and {{var2}}",
        variables=["var1", "var2"],
    )

    with pytest.raises(ValueError, match="Missing required variables"):
        template.render(var1="value1")


def test_template_default_values():
    """Test template with default values."""
    template = PromptTemplate(
        name="test",
        template="{{greeting}} {{name}}",
        variables=["greeting", "name"],
        default_values={"greeting": "Hello"},
    )

    prompt = template.render(name="Bob")
    assert "Hello Bob" in prompt.content


def test_template_validation():
    """Test template variable validation."""
    template = PromptTemplate(
        name="test",
        template="{{var1}} {{var2}}",
        variables=["var1", "var2"],
        default_values={"var1": "default"},
    )

    is_valid, missing = template.validate_variables(var2="value")
    assert is_valid
    assert len(missing) == 0

    is_valid, missing = template.validate_variables()
    assert not is_valid
    assert "var2" in missing


def test_invalid_template():
    """Test invalid Jinja2 template."""
    with pytest.raises(ValueError, match="Invalid Jinja2 template"):
        PromptTemplate(
            name="bad",
            template="{{unclosed",
            variables=[],
        )
