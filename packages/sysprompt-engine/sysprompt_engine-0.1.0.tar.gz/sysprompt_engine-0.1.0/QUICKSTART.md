# PromptEngine - Quick Start Guide

Welcome to PromptEngine! This guide will get you up and running in 5 minutes.

## Installation

```bash
# Install from source
cd PrompEngine
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

## Your First Prompt

```python
from promptengine import Prompt

# Create a simple prompt
prompt = Prompt(
    name="my_first_prompt",
    content="You are a helpful AI assistant.",
    tags=["assistant"]
)

print(prompt.content)
# Output: You are a helpful AI assistant.
```

## Using Templates

Templates let you create reusable prompts with variables:

```python
from promptengine import PromptTemplate

# Create a template
template = PromptTemplate(
    name="code_helper",
    template="""You are a {{language}} expert.
Help the user with this task: {{task}}

Be {{style}} in your response.""",
    variables=["language", "language", "task", "style"]
)

# Render with different values
prompt = template.render(
    language="Python",
    task="optimize this function",
    style="concise"
)

print(prompt.content)
```

## Managing Multiple Prompts

Use the registry to organize prompts:

```python
from promptengine import PromptRegistry, Prompt

registry = PromptRegistry()

# Add prompts
registry.add(Prompt(
    name="translator",
    content="Translate the following to Spanish:",
    tags=["translation"]
))

registry.add(Prompt(
    name="summarizer",
    content="Summarize this text in 3 points:",
    tags=["summarization"]
))

# Save to file
registry.save("my_prompts.json")

# Later, load from file
registry.load("my_prompts.json")

# Get a specific prompt
prompt = registry.get_prompt("translator")
print(prompt.content)
```

## Version Control

Track changes to your prompts:

```python
from promptengine import Prompt, VersionControl

vc = VersionControl(storage_path="versions.json")

# Create and version a prompt
prompt = Prompt(name="assistant", content="Version 1")
vc.save_version(prompt, commit_message="Initial version")

# Update it
prompt.update_content("Version 2 - improved")
vc.save_version(prompt, commit_message="Made improvements")

# View history
history = vc.get_history(prompt.id)
for v in history:
    print(f"v{v['version_number']}: {v['commit_message']}")

# Rollback if needed
old_version = vc.rollback(prompt.id, version_number=1)
print(old_version.content)  # Back to "Version 1"
```

## Validation

Ensure your prompts meet quality standards:

```python
from promptengine import Prompt, PromptValidator

validator = PromptValidator()

prompt = Prompt(
    name="test",
    content="You are a professional AI assistant."
)

result = validator.validate(prompt)

if result.is_valid:
    print("✓ Prompt is valid!")
else:
    print("✗ Validation failed:")
    for error in result.errors:
        print(f"  - {error['message']}")
```

## Integration Example

Here's how to use PromptEngine in a real application:

```python
from promptengine import PromptRegistry, VersionControl, PromptValidator

class MyApp:
    def __init__(self):
        # Initialize components
        self.registry = PromptRegistry()
        self.registry.load("app_prompts.json")
        self.vc = VersionControl(storage_path="app_versions.json")
        self.validator = PromptValidator()

    def get_prompt(self, name, **variables):
        """Get and render a prompt for use."""
        # Get template
        template = self.registry.get_template(name)
        if not template:
            raise ValueError(f"Template '{name}' not found")

        # Render
        prompt = template.render(**variables)

        # Validate
        result = self.validator.validate(prompt)
        if not result.is_valid:
            raise ValueError(f"Invalid prompt: {result.errors}")

        # Version it
        self.vc.save_version(prompt, commit_message=f"Used {name}")

        return prompt.content

# Usage
app = MyApp()
prompt_content = app.get_prompt(
    "chatbot",
    personality="friendly",
    expertise="coding"
)

# Send to your LLM
# response = llm.complete(prompt_content)
```

## Next Steps

1. **Run Examples**: Check out `examples/basic_usage.py` for more examples
2. **Integration Guide**: Read `examples/integration_guide.md` for API integration
3. **Tests**: Run `pytest tests/` to see the test suite
4. **Customize**: Add your own validation rules and templates

## Key Features at a Glance

| Feature | What it does |
|---------|-------------|
| **Prompt** | Simple text prompt with metadata |
| **PromptTemplate** | Reusable template with variables |
| **PromptRegistry** | Organize and manage multiple prompts |
| **VersionControl** | Track changes, view diffs, rollback |
| **PromptValidator** | Validate prompt quality |
| **PromptTester** | Test templates with different inputs |

## Common Patterns

### Pattern 1: Multi-tenant Prompts

```python
# Different prompts for different users/tenants
registry = PromptRegistry()
registry.load(f"prompts_{tenant_id}.json")
```

### Pattern 2: A/B Testing

```python
# Version control makes A/B testing easy
vc = VersionControl()

# Save variant A
prompt_a = Prompt(name="feature", content="Variant A")
version_a = vc.save_version(prompt_a, commit_message="Variant A")

# Save variant B
prompt_b = Prompt(name="feature", content="Variant B")
version_b = vc.save_version(prompt_b, commit_message="Variant B")

# Use based on experiment
if user_in_experiment_group:
    prompt = vc.get_version(prompt_a.id, version_a)
else:
    prompt = vc.get_version(prompt_a.id, version_b)
```

### Pattern 3: Environment-specific Prompts

```python
import os

env = os.getenv("ENV", "development")
registry.load(f"prompts_{env}.json")
```

## Need Help?

- Check the `examples/` directory for more use cases
- Read the integration guide for API examples
- Look at the tests for usage patterns

Happy prompting!
