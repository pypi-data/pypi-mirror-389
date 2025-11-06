# PromptEngine Integration Guide

This guide shows how to integrate PromptEngine into your applications.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Flask API Integration](#flask-api-integration)
3. [FastAPI Integration](#fastapi-integration)
4. [CLI Tool Integration](#cli-tool-integration)
5. [Database Integration](#database-integration)

## Quick Start

Install PromptEngine in your project:

```bash
pip install -e /path/to/promptengine
```

Basic usage:

```python
from promptengine import PromptTemplate, PromptRegistry

# Load your prompts
registry = PromptRegistry()
registry.load("prompts.json")

# Get and render a template
template = registry.get_template("chatbot")
prompt = template.render(personality="friendly", role="helper")

# Use with your LLM
response = your_llm_client.complete(prompt.content)
```

## Flask API Integration

Create a Flask API that serves prompts:

```python
from flask import Flask, request, jsonify
from promptengine import PromptRegistry, PromptTemplate, VersionControl

app = Flask(__name__)
registry = PromptRegistry()
version_control = VersionControl(storage_path="data/versions.json")

# Load prompts on startup
registry.load("data/prompts.json")

@app.route("/api/prompts", methods=["GET"])
def list_prompts():
    """List all available prompts."""
    return jsonify({
        "prompts": registry.list_prompts(),
        "templates": registry.list_templates()
    })

@app.route("/api/prompts/<name>", methods=["GET"])
def get_prompt(name):
    """Get a specific prompt."""
    prompt = registry.get_prompt(name)
    if not prompt:
        return jsonify({"error": "Prompt not found"}), 404
    return jsonify(prompt.to_dict())

@app.route("/api/templates/<name>/render", methods=["POST"])
def render_template(name):
    """Render a template with variables."""
    template = registry.get_template(name)
    if not template:
        return jsonify({"error": "Template not found"}), 404

    variables = request.json
    try:
        prompt = template.render(**variables)

        # Version the rendered prompt
        version_id = version_control.save_version(
            prompt,
            commit_message=f"Rendered {name}",
            author=request.headers.get("X-User", "anonymous")
        )

        return jsonify({
            "content": prompt.content,
            "version_id": version_id
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/prompts", methods=["POST"])
def create_prompt():
    """Create a new prompt."""
    data = request.json

    if "template" in data:
        item = PromptTemplate(
            name=data["name"],
            template=data["template"],
            variables=data.get("variables", []),
            description=data.get("description"),
            tags=data.get("tags", [])
        )
    else:
        from promptengine import Prompt
        item = Prompt(
            name=data["name"],
            content=data["content"],
            description=data.get("description"),
            tags=data.get("tags", [])
        )

    registry.add(item)
    registry.save("data/prompts.json")

    return jsonify(item.to_dict()), 201

if __name__ == "__main__":
    app.run(debug=True, port=5000)
```

Test the API:

```bash
# List prompts
curl http://localhost:5000/api/prompts

# Render a template
curl -X POST http://localhost:5000/api/templates/chatbot/render \
  -H "Content-Type: application/json" \
  -d '{"personality": "friendly", "role": "helper"}'
```

## FastAPI Integration

Modern async API with FastAPI:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from promptengine import PromptRegistry, PromptTemplate, PromptValidator

app = FastAPI(title="PromptEngine API")
registry = PromptRegistry()
validator = PromptValidator()

class RenderRequest(BaseModel):
    variables: Dict[str, str]

class PromptCreate(BaseModel):
    name: str
    content: Optional[str] = None
    template: Optional[str] = None
    variables: Optional[List[str]] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None

@app.on_event("startup")
async def startup_event():
    """Load prompts on startup."""
    try:
        registry.load("prompts.json")
    except FileNotFoundError:
        pass

@app.get("/templates/{name}")
async def get_template(name: str):
    """Get a template by name."""
    template = registry.get_template(name)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template.to_dict()

@app.post("/templates/{name}/render")
async def render_template(name: str, request: RenderRequest):
    """Render a template with variables."""
    template = registry.get_template(name)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    try:
        prompt = template.render(**request.variables)

        # Validate before returning
        validation = validator.validate(prompt)

        return {
            "content": prompt.content,
            "validation": validation.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/prompts")
async def create_prompt(prompt_data: PromptCreate):
    """Create a new prompt or template."""
    if prompt_data.template:
        item = PromptTemplate(
            name=prompt_data.name,
            template=prompt_data.template,
            variables=prompt_data.variables or [],
            description=prompt_data.description,
            tags=prompt_data.tags or []
        )
    else:
        from promptengine import Prompt
        item = Prompt(
            name=prompt_data.name,
            content=prompt_data.content,
            description=prompt_data.description,
            tags=prompt_data.tags or []
        )

    registry.add(item, overwrite=False)
    registry.save("prompts.json")

    return item.to_dict()
```

## CLI Tool Integration

Create a command-line tool:

```python
#!/usr/bin/env python3
"""CLI tool for managing prompts."""

import click
from promptengine import PromptRegistry, PromptTemplate, VersionControl

registry = PromptRegistry()
vc = VersionControl(storage_path="versions.json")

@click.group()
def cli():
    """PromptEngine CLI - Manage your prompts from the command line."""
    pass

@cli.command()
@click.option("--file", default="prompts.json", help="Prompts file")
def list(file):
    """List all prompts and templates."""
    registry.load(file)
    click.echo(f"\\nPrompts: {', '.join(registry.list_prompts())}")
    click.echo(f"Templates: {', '.join(registry.list_templates())}")

@cli.command()
@click.argument("name")
@click.option("--file", default="prompts.json", help="Prompts file")
def show(name, file):
    """Show a prompt or template."""
    registry.load(file)

    prompt = registry.get_prompt(name)
    if prompt:
        click.echo(f"\\nPrompt: {name}")
        click.echo(f"Content:\\n{prompt.content}")
        return

    template = registry.get_template(name)
    if template:
        click.echo(f"\\nTemplate: {name}")
        click.echo(f"Variables: {template.variables}")
        click.echo(f"Template:\\n{template.template_str}")
        return

    click.echo(f"Not found: {name}", err=True)

@cli.command()
@click.argument("name")
@click.option("--var", "-v", multiple=True, help="Variable in format key=value")
@click.option("--file", default="prompts.json", help="Prompts file")
def render(name, var, file):
    """Render a template with variables."""
    registry.load(file)
    template = registry.get_template(name)

    if not template:
        click.echo(f"Template not found: {name}", err=True)
        return

    # Parse variables
    variables = {}
    for v in var:
        key, value = v.split("=", 1)
        variables[key] = value

    try:
        prompt = template.render(**variables)
        click.echo(prompt.content)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)

if __name__ == "__main__":
    cli()
```

Save as `prompt-cli.py` and use:

```bash
python prompt-cli.py list
python prompt-cli.py show chatbot
python prompt-cli.py render chatbot -v personality=friendly -v role=helper
```

## Database Integration

Store prompts in a database:

```python
from sqlalchemy import create_engine, Column, String, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from promptengine import Prompt, PromptTemplate

Base = declarative_base()

class PromptModel(Base):
    __tablename__ = "prompts"

    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    prompt_type = Column(String, nullable=False)  # 'prompt' or 'template'
    data = Column(JSON, nullable=False)

class PromptDatabase:
    def __init__(self, database_url="sqlite:///prompts.db"):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def save_prompt(self, prompt):
        """Save a prompt to the database."""
        model = PromptModel(
            id=prompt.id,
            name=prompt.name,
            prompt_type="prompt" if isinstance(prompt, Prompt) else "template",
            data=prompt.to_dict()
        )
        self.session.merge(model)
        self.session.commit()

    def load_prompt(self, name):
        """Load a prompt from the database."""
        model = self.session.query(PromptModel).filter_by(name=name).first()
        if not model:
            return None

        if model.prompt_type == "prompt":
            return Prompt.from_dict(model.data)
        else:
            return PromptTemplate.from_dict(model.data)

    def list_prompts(self):
        """List all prompt names."""
        return [p.name for p in self.session.query(PromptModel).all()]

# Usage
db = PromptDatabase()
prompt = Prompt(name="test", content="Test content")
db.save_prompt(prompt)
loaded = db.load_prompt("test")
```

## Best Practices

1. **Version Control**: Always use version control for production prompts
2. **Validation**: Validate prompts before deployment
3. **Testing**: Create test cases for critical templates
4. **Tagging**: Use tags to organize prompts by feature/use-case
5. **Caching**: Cache rendered prompts for better performance
6. **Monitoring**: Track which prompts are used most frequently
7. **Security**: Sanitize user inputs before rendering templates
