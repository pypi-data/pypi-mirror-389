# PromptEngine

A flexible and powerful system prompt creator with built-in version control and validation capabilities. Perfect for managing AI prompts across multiple applications.

## Features

- **Template System**: Use Jinja2 templates with variable substitution
- **Version Control**: Track changes, view diffs, and rollback to previous versions
- **Validation & Testing**: Validate prompts and test outputs
- **Easy Integration**: Simple SDK that can be integrated into any Python application
- **Storage Formats**: Support for JSON and YAML
- **Metadata Management**: Track creation time, authors, tags, and more

## Installation

```bash
pip install -e .
```

For development:
```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from promptengine import PromptTemplate, PromptRegistry, VersionControl

# Create a prompt template
template = PromptTemplate(
    name="code_reviewer",
    template="""You are a {{expertise_level}} code reviewer.
Review the following {{language}} code and provide feedback on:
- Code quality
- Best practices
- Potential bugs

Code:
{{code}}
""",
    variables=["expertise_level", "language", "code"]
)

# Render with variables
prompt = template.render(
    expertise_level="senior",
    language="Python",
    code="def hello(): print('world')"
)

# Use version control
vc = VersionControl()
version_id = vc.save_version(prompt)

# Create a registry
registry = PromptRegistry()
registry.add(template)
registry.save("prompts.json")
```

## Documentation

See the `examples/` directory for more usage examples.

## License

MIT
