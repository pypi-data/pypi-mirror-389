# PromptEngine Architecture & Code Explanation

**Complete guide to understanding how PromptEngine works internally**

---

## 🎯 Overview

**PromptEngine** is a content management system for AI prompts. It helps you create, organize, version, validate, and integrate prompts into your applications.

### High-Level Data Flow

```
Developer creates prompt → Store in Registry → Version Control tracks changes →
Validate quality → Export to app → App uses with LLM
```

### Core Concepts

1. **Prompt**: A simple text prompt with metadata
2. **PromptTemplate**: A reusable prompt with variables (uses Jinja2)
3. **PromptRegistry**: Central storage/organization for all prompts
4. **VersionControl**: Git-like versioning system for prompts
5. **PromptValidator**: Quality control and testing framework

---

## 📂 Project Structure

```
PrompEngine/
├── promptengine/              # Main package
│   ├── __init__.py           # Package entry point
│   ├── core/                 # Core functionality
│   │   ├── __init__.py
│   │   ├── prompt.py        # Prompt & PromptTemplate classes
│   │   └── registry.py      # PromptRegistry for management
│   ├── version_control/      # Version control system
│   │   ├── __init__.py
│   │   └── version_manager.py
│   └── validation/           # Validation & testing
│       ├── __init__.py
│       └── validator.py
├── examples/                 # Usage examples
│   ├── basic_usage.py
│   ├── validation_examples.py
│   └── integration_guide.md
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_prompt.py
├── setup.py                  # Package installer
├── requirements.txt          # Dependencies
├── README.md
├── QUICKSTART.md
└── .gitignore
```

---

## 📄 File-by-File Code Explanation

### **Setup & Configuration**

#### `setup.py` - Package Installer

**Purpose**: Defines how to install PromptEngine via pip

```python
# Key configurations:
name="promptengine"
version="0.1.0"

# Dependencies:
install_requires=[
    "jinja2>=3.0.0",    # Template rendering
    "pyyaml>=6.0",      # YAML file support
    "pydantic>=2.0.0",  # Data validation
]

# Install with: pip install -e .
```

**What it does**: Tells Python how to package and install PromptEngine, including all dependencies.

---

#### `requirements.txt` - Dependency List

```
jinja2>=3.0.0    # Templating engine for {{variables}}
pyyaml>=6.0      # YAML format support (alternative to JSON)
pydantic>=2.0.0  # Data validation framework
```

---

#### `.gitignore` - Git Exclusions

Tells git to ignore:
- `__pycache__/` - Python bytecode
- `*.egg-info/` - Build artifacts
- `venv/` - Virtual environments
- `.pytest_cache/` - Test cache

---

### **Core Module** (`promptengine/core/`)

#### `promptengine/__init__.py` - Package Entry Point

**Purpose**: Defines what gets imported when you use `from promptengine import ...`

```python
"""PromptEngine - Main package"""

from promptengine.core.prompt import Prompt, PromptTemplate
from promptengine.core.registry import PromptRegistry
from promptengine.version_control.version_manager import VersionControl
from promptengine.validation.validator import PromptValidator

__version__ = "0.1.0"
__all__ = [
    "Prompt",
    "PromptTemplate",
    "PromptRegistry",
    "VersionControl",
    "PromptValidator",
]
```

**How it works**: When you do `from promptengine import Prompt`, Python looks here and imports from `core.prompt`.

---

#### `promptengine/core/prompt.py` - Foundation Classes

**Purpose**: Defines the two fundamental classes that represent prompts.

##### **Class 1: `Prompt` - Simple Prompt**

```python
class Prompt:
    """Represents a system prompt with metadata."""

    def __init__(self, content, name=None, description=None,
                 metadata=None, tags=None, prompt_id=None):
        self.id = prompt_id or str(uuid4())  # Unique identifier
        self.content = content                # The actual prompt text
        self.name = name or f"prompt_{self.id[:8]}"
        self.description = description or ""
        self.metadata = metadata or {}        # Extra data
        self.tags = tags or []                # Categories
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = self.created_at
```

**What it stores**:
- `id`: UUID for unique identification
- `content`: The actual prompt text you send to LLMs
- `name`: Human-readable name
- `description`: What this prompt does
- `tags`: List of categories like `["chatbot", "coding"]`
- `metadata`: Any extra data you want to store
- `created_at`/`updated_at`: Timestamps

**Key Methods**:

```python
# Update the prompt
prompt.update_content("New content")  # Updates content and timestamp

# Manage tags
prompt.add_tag("production")
prompt.remove_tag("testing")

# Serialization (save to file/database)
data = prompt.to_dict()        # Convert to dictionary
json_str = prompt.to_json()    # Convert to JSON string

# Deserialization (load from file/database)
prompt = Prompt.from_dict(data)
prompt = Prompt.from_json(json_str)
```

**Example Usage**:

```python
prompt = Prompt(
    name="translator",
    content="Translate the following text to French:",
    description="French translation prompt",
    tags=["translation", "french"]
)

print(prompt.content)  # "Translate the following text to French:"
print(prompt.id)       # "a1b2c3d4-e5f6-..."
```

---

##### **Class 2: `PromptTemplate` - Reusable Template**

```python
class PromptTemplate:
    """A template for creating prompts with variable substitution."""

    def __init__(self, template, name=None, description=None,
                 variables=None, default_values=None, metadata=None,
                 tags=None, template_id=None):
        self.id = template_id or str(uuid4())
        self.template_str = template              # Jinja2 template string
        self.name = name or f"template_{self.id[:8]}"
        self.description = description or ""
        self.variables = variables or []          # Required variables
        self.default_values = default_values or {} # Defaults
        self.metadata = metadata or {}
        self.tags = tags or []
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = self.created_at

        # Compile Jinja2 template
        try:
            self._template = Template(template)
        except TemplateSyntaxError as e:
            raise ValueError(f"Invalid Jinja2 template: {e}")
```

**What it stores** (extends Prompt):
- `template_str`: Jinja2 template with `{{variable}}` placeholders
- `variables`: List of required variables `["name", "age"]`
- `default_values`: Default values for variables
- `_template`: Compiled Jinja2 template object (for performance)

**Key Methods**:

```python
# Render template with variables
prompt = template.render(name="Alice", age=25)
# Returns a Prompt object with rendered content

# Validate variables before rendering
is_valid, missing = template.validate_variables(name="Alice")
# Returns: (False, ["age"])  if age is missing

# Update template
template.update_template("New {{template}} string")
```

**How Jinja2 Works**:

```python
template = PromptTemplate(
    name="greeter",
    template="""Hello {{name}}, you are {{age}} years old.

{% if age >= 18 %}
You are an adult.
{% else %}
You are a minor.
{% endif %}

Your hobbies:
{% for hobby in hobbies %}
- {{hobby}}
{% endfor %}
""",
    variables=["name", "age", "hobbies"],
    default_values={"age": 0}
)

# Render it
prompt = template.render(
    name="Bob",
    age=25,
    hobbies=["coding", "reading"]
)

# prompt.content =
# "Hello Bob, you are 25 years old.
# You are an adult.
# Your hobbies:
# - coding
# - reading"
```

**Jinja2 Syntax**:
- `{{variable}}` - Variable substitution
- `{% if condition %}...{% endif %}` - Conditionals
- `{% for item in list %}...{% endfor %}` - Loops
- `{{variable|upper}}` - Filters (upper, lower, etc.)

**Example Usage**:

```python
template = PromptTemplate(
    name="code_reviewer",
    template="""You are a {{expertise}} {{language}} developer.
Review this code:

```{{language}}
{{code}}
```

Focus on {{focus_area}}.""",
    variables=["expertise", "language", "code", "focus_area"],
    default_values={"expertise": "senior", "focus_area": "best practices"}
)

# Render for Python
prompt = template.render(
    language="Python",
    code="def hello(): print('world')"
)

# prompt.content = "You are a senior Python developer..."
```

**Metadata in Rendered Prompts**:

When you render a template, the resulting Prompt includes metadata about where it came from:

```python
prompt = template.render(name="Alice")

prompt.metadata == {
    "template_id": "uuid-of-template",
    "template_name": "greeter",
    "render_variables": {"name": "Alice", "age": 0}  # includes defaults
}
```

---

#### `promptengine/core/registry.py` - Prompt Organizer

**Purpose**: Central storage and management for all prompts and templates.

```python
class PromptRegistry:
    """Manages a collection of prompts and templates."""

    def __init__(self):
        self.prompts: Dict[str, Prompt] = {}           # {name: Prompt}
        self.templates: Dict[str, PromptTemplate] = {} # {name: Template}
```

**Data Structure**:

```python
# Internal storage:
registry.prompts = {
    "translator": Prompt(...),
    "summarizer": Prompt(...),
}

registry.templates = {
    "chatbot": PromptTemplate(...),
    "code_reviewer": PromptTemplate(...),
}
```

**Key Methods**:

##### **Adding & Removing**

```python
# Add items
registry.add(prompt, overwrite=False)
# Raises ValueError if name exists and overwrite=False

# Remove items
registry.remove_prompt("translator")  # Returns True if found
registry.remove_template("chatbot")
```

##### **Retrieving**

```python
# Get by name
prompt = registry.get_prompt("translator")
template = registry.get_template("chatbot")

# List all names
all_prompts = registry.list_prompts()
# Returns: ["translator", "summarizer"]

# Filter by tag
coding_prompts = registry.list_prompts(tag="coding")
```

##### **Searching**

```python
results = registry.search("translation")
# Searches in: name, description, tags
# Returns: {
#     "prompts": ["translator"],
#     "templates": ["translation_template"]
# }
```

##### **Persistence (Save/Load)**

```python
# Save to JSON
registry.save("prompts.json", format="json")

# Save to YAML
registry.save("prompts.yaml", format="yaml")

# Load from file
registry.load("prompts.json", format="json")
```

**File Format (JSON)**:

```json
{
  "prompts": [
    {
      "id": "uuid-123",
      "name": "translator",
      "content": "Translate to French",
      "description": "Translation prompt",
      "tags": ["translation"],
      "metadata": {},
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ],
  "templates": [
    {
      "id": "uuid-456",
      "name": "chatbot",
      "template": "You are {{personality}}",
      "variables": ["personality"],
      "default_values": {},
      "description": "",
      "tags": ["chatbot"],
      "metadata": {},
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ]
}
```

##### **Import/Export Individual Items**

```python
# Export single prompt to file
registry.export_prompt("translator", "translator.json")

# Import single prompt from file
registry.import_prompt("translator.json", overwrite=False)

# Same for templates
registry.export_template("chatbot", "chatbot.json")
registry.import_template("chatbot.json")
```

##### **Utility Methods**

```python
# Clear everything
registry.clear()

# Get statistics
stats = registry.stats()
# Returns: {
#     "total_prompts": 5,
#     "total_templates": 3,
#     "total_items": 8
# }
```

**Example Usage**:

```python
# Create registry
registry = PromptRegistry()

# Add some prompts
registry.add(Prompt(
    name="translator",
    content="Translate to Spanish",
    tags=["translation"]
))

registry.add(PromptTemplate(
    name="chatbot",
    template="You are a {{personality}} assistant",
    variables=["personality"],
    tags=["chatbot", "assistant"]
))

# Search
results = registry.search("chatbot")
# {"prompts": [], "templates": ["chatbot"]}

# Save everything
registry.save("my_prompts.json")

# Later, in another app/session
new_registry = PromptRegistry()
new_registry.load("my_prompts.json")
chatbot = new_registry.get_template("chatbot")
```

**Why use PromptRegistry?**
- Organize hundreds of prompts in one place
- Easy search and retrieval
- Share prompts across team (export/import)
- Backup and restore
- Tag-based categorization

---

### **Version Control Module** (`promptengine/version_control/`)

#### `version_manager.py` - Git for Prompts

**Purpose**: Track changes to prompts over time, like Git does for code.

##### **Class 1: `PromptVersion` - A Snapshot**

```python
class PromptVersion:
    """Represents a single version of a prompt."""

    def __init__(self, prompt, version_number, parent_version=None,
                 commit_message=None, author=None):
        self.version_id = str(uuid4())        # Unique ID for this version
        self.version_number = version_number   # 1, 2, 3, etc.
        self.parent_version = parent_version   # Previous version number
        self.prompt_data = prompt.to_dict()    # Full snapshot
        self.commit_message = commit_message or "No commit message"
        self.author = author or "Unknown"
        self.timestamp = datetime.utcnow().isoformat()
        self.prompt_type = "prompt" if isinstance(prompt, Prompt) else "template"
```

**What it stores**:
- Complete snapshot of the prompt at this point in time
- Version lineage (parent version)
- Commit metadata (message, author, timestamp)

---

##### **Class 2: `VersionControl` - Version Manager**

```python
class VersionControl:
    """Manages version control for prompts and templates."""

    def __init__(self, storage_path=None):
        self.storage_path = Path(storage_path) if storage_path else None

        # All version histories
        self.version_histories: Dict[str, List[PromptVersion]] = {}
        # {prompt_id: [version1, version2, version3]}

        # Current version for each prompt
        self.current_versions: Dict[str, int] = {}
        # {prompt_id: 3}  <- currently on version 3
```

**Data Structure**:

```python
# Example internal state:
vc.version_histories = {
    "prompt-uuid-123": [
        PromptVersion(version_number=1, commit_message="Initial"),
        PromptVersion(version_number=2, commit_message="Fixed typo"),
        PromptVersion(version_number=3, commit_message="Added context"),
    ],
    "prompt-uuid-456": [
        PromptVersion(version_number=1, commit_message="First draft"),
        PromptVersion(version_number=2, commit_message="Finalized"),
    ]
}

vc.current_versions = {
    "prompt-uuid-123": 3,  # Currently on version 3
    "prompt-uuid-456": 2   # Currently on version 2
}
```

**Key Methods**:

##### **1. Save Version (like `git commit`)**

```python
vc = VersionControl(storage_path="versions.json")

prompt = Prompt(name="assistant", content="Version 1")
version_id = vc.save_version(
    prompt,
    commit_message="Initial version",
    author="Alice"
)
# Returns: version ID string

# Later, update and save again
prompt.update_content("Version 2 - improved")
vc.save_version(
    prompt,
    commit_message="Improved tone",
    author="Bob"
)
```

**What happens**:
1. Creates a `PromptVersion` object with snapshot of prompt
2. Adds to version history for that prompt ID
3. Updates current version number
4. Auto-saves to file if storage_path is set

---

##### **2. Get Version (like `git checkout`)**

```python
# Get latest version
prompt = vc.get_version("prompt-uuid-123")

# Get specific version
prompt = vc.get_version("prompt-uuid-123", version_number=1)

# Returns a Prompt or PromptTemplate object (reconstructed from snapshot)
```

---

##### **3. View History (like `git log`)**

```python
history = vc.get_history("prompt-uuid-123")

# Returns list of metadata:
# [
#   {
#     "version_number": 1,
#     "version_id": "version-uuid-1",
#     "commit_message": "Initial version",
#     "author": "Alice",
#     "timestamp": "2024-01-01T10:00:00",
#     "prompt_type": "prompt"
#   },
#   {
#     "version_number": 2,
#     "version_id": "version-uuid-2",
#     "commit_message": "Improved tone",
#     "author": "Bob",
#     "timestamp": "2024-01-02T15:30:00",
#     "prompt_type": "prompt"
#   }
# ]
```

---

##### **4. View Diff (like `git diff`)**

```python
diff_result = vc.diff(
    prompt_id="prompt-uuid-123",
    version1=1,
    version2=2
)

# Returns:
# {
#     "prompt_id": "prompt-uuid-123",
#     "version1": 1,
#     "version2": 2,
#     "diff": "--- Version 1\n+++ Version 2\n...",  # Unified diff
#     "changes": 5  # Number of changed lines
# }
```

**Diff format** (uses Python's `difflib.unified_diff`):

```diff
--- Version 1
+++ Version 2
@@ -1,1 +1,1 @@
-You are a helpful assistant.
+You are a helpful and friendly assistant.
```

---

##### **5. Rollback (like `git reset`)**

```python
# Rollback to version 1
old_prompt = vc.rollback("prompt-uuid-123", version_number=1)

# Returns the Prompt/Template at that version
# Updates current_versions to point to version 1
```

**Use case**: Deployed a bad prompt to production? Rollback instantly.

---

##### **6. Manage Histories**

```python
# List all prompts with version history
prompt_ids = vc.list_prompts()

# Delete entire version history for a prompt
vc.delete_history("prompt-uuid-123")

# Get statistics
stats = vc.stats()
# Returns:
# {
#     "total_prompts": 2,
#     "total_versions": 5,
#     "prompts": [
#         {
#             "prompt_id": "uuid-123",
#             "version_count": 3,
#             "current_version": 3
#         },
#         {
#             "prompt_id": "uuid-456",
#             "version_count": 2,
#             "current_version": 2
#         }
#     ]
# }
```

---

##### **7. Persistence**

```python
# Save to file (auto-called if storage_path is set)
vc.save()

# Load from file (auto-called on init if file exists)
vc.load()
```

**Storage Format (`versions.json`)**:

```json
{
  "version_histories": {
    "prompt-uuid-123": [
      {
        "version_id": "version-uuid-1",
        "version_number": 1,
        "parent_version": null,
        "prompt_data": {
          "id": "prompt-uuid-123",
          "name": "assistant",
          "content": "You are helpful.",
          "tags": []
        },
        "prompt_type": "prompt",
        "commit_message": "Initial version",
        "author": "Alice",
        "timestamp": "2024-01-01T10:00:00"
      },
      {
        "version_id": "version-uuid-2",
        "version_number": 2,
        "parent_version": 1,
        "prompt_data": {
          "id": "prompt-uuid-123",
          "name": "assistant",
          "content": "You are helpful and friendly.",
          "tags": []
        },
        "prompt_type": "prompt",
        "commit_message": "Made more friendly",
        "author": "Bob",
        "timestamp": "2024-01-02T15:30:00"
      }
    ]
  },
  "current_versions": {
    "prompt-uuid-123": 2
  }
}
```

---

**Real-World Use Cases**:

```python
# Use Case 1: A/B Testing
vc = VersionControl()

prompt_a = Prompt(name="cta", content="Buy now!")
v1 = vc.save_version(prompt_a, commit_message="Variant A")

prompt_a.update_content("Get started today!")
v2 = vc.save_version(prompt_a, commit_message="Variant B")

# Serve different versions to users
if user_in_group_a:
    prompt = vc.get_version(prompt_a.id, version_number=1)
else:
    prompt = vc.get_version(prompt_a.id, version_number=2)


# Use Case 2: Rollback Bad Deploy
# Deployed version 5, but it's causing issues
vc.rollback(prompt_id, version_number=4)  # Back to last good version


# Use Case 3: Audit Trail
# Who changed what and when?
history = vc.get_history(prompt_id)
for v in history:
    print(f"{v['author']} changed it on {v['timestamp']}: {v['commit_message']}")
```

---

### **Validation Module** (`promptengine/validation/`)

#### `validator.py` - Quality Control

**Purpose**: Ensure prompts meet quality standards before deployment.

##### **Class 1: `ValidationRule` - A Single Check**

```python
class ValidationRule:
    """Represents a validation rule for prompts."""

    def __init__(self, name, validator, error_message, severity="error"):
        self.name = name                    # Rule identifier
        self.validator = validator          # Function: str -> bool
        self.error_message = error_message  # Error message
        self.severity = severity            # "error", "warning", or "info"
```

**How it works**:

```python
# Create a rule
rule = ValidationRule(
    name="min_length",
    validator=lambda content: len(content) >= 10,  # Function returns True/False
    error_message="Content must be at least 10 characters",
    severity="warning"
)

# Run validation
is_valid, error = rule.validate("Short")
# Returns: (False, "Content must be at least 10 characters")

is_valid, error = rule.validate("This is long enough")
# Returns: (True, None)
```

---

##### **Class 2: `ValidationResult` - Result Container**

```python
class ValidationResult:
    """Result of prompt validation."""

    def __init__(self):
        self.errors: List[Dict[str, str]] = []    # Critical issues
        self.warnings: List[Dict[str, str]] = []  # Should fix
        self.info: List[Dict[str, str]] = []      # FYI

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0  # Valid if no errors (warnings OK)
```

**Structure**:

```python
result = ValidationResult()
result.errors = [
    {"rule": "not_empty", "message": "Prompt is empty"}
]
result.warnings = [
    {"rule": "min_length", "message": "Prompt is too short"}
]
result.info = [
    {"rule": "keyword_check", "message": "Consider adding 'please'"}
]

result.is_valid  # False (has errors)
result.has_warnings  # True
```

---

##### **Class 3: `PromptValidator` - Validation Engine**

```python
class PromptValidator:
    """Validates prompts against a set of rules."""

    def __init__(self):
        self.rules: List[ValidationRule] = []
        self._add_default_rules()  # Adds built-in rules
```

**Default Rules**:

1. **not_empty** (error): Content is not empty
2. **min_length** (warning): At least 10 characters
3. **max_length** (error): No more than 50,000 characters
4. **no_todo_placeholders** (warning): No "TODO" or "FIXME"
5. **balanced_braces** (error): `{{` and `}}` are balanced (for templates)

**Key Methods**:

##### **Add Custom Rules**

```python
validator = PromptValidator()

# Add a rule
validator.add_rule(
    name="must_be_polite",
    validator=lambda content: "please" in content.lower() or "thank" in content.lower(),
    error_message="Prompt should include polite language",
    severity="info"
)

# Remove a rule
validator.remove_rule("min_length")
```

##### **Validate a Prompt**

```python
prompt = Prompt(
    name="test",
    content="Hi"  # Too short
)

result = validator.validate(prompt)

if not result.is_valid:
    print("Validation failed!")
    for error in result.errors:
        print(f"  {error['rule']}: {error['message']}")

for warning in result.warnings:
    print(f"  WARNING - {warning['rule']}: {warning['message']}")

# Output:
# WARNING - min_length: Prompt content is too short (minimum 10 characters)
```

##### **Batch Validation**

```python
prompts = [prompt1, prompt2, prompt3]

results = validator.validate_batch(prompts)
# Returns: {
#     "prompt1": ValidationResult(...),
#     "prompt2": ValidationResult(...),
#     "prompt3": ValidationResult(...)
# }

for name, result in results.items():
    if not result.is_valid:
        print(f"{name} failed validation")
```

---

##### **Class 4: `PromptTester` - Template Testing**

```python
class PromptTester:
    """Test prompts with mock or real responses."""

    def __init__(self):
        self.test_cases: List[Dict[str, Any]] = []
```

**Purpose**: Test that templates render correctly with different variables.

**Usage**:

```python
tester = PromptTester()

# Add test cases
tester.add_test_case(
    name="test_friendly_chatbot",
    variables={"personality": "friendly", "domain": "coding"},
    expected_keywords=["friendly", "coding"],  # Must appear in output
    expected_patterns=[r"Hello.*user"]         # Regex that must match
)

tester.add_test_case(
    name="test_professional_chatbot",
    variables={"personality": "professional", "domain": "business"},
    expected_keywords=["professional", "business"]
)

# Run all tests on a template
template = PromptTemplate(
    name="chatbot",
    template="You are a {{personality}} assistant specializing in {{domain}}.",
    variables=["personality", "domain"]
)

results = tester.run_tests(template)

# Returns:
# {
#     "test_friendly_chatbot": {
#         "passed": True,
#         "rendered_content": "You are a friendly assistant specializing in coding.",
#         "missing_keywords": [],
#         "missing_patterns": []
#     },
#     "test_professional_chatbot": {
#         "passed": True,
#         "rendered_content": "You are a professional assistant...",
#         "missing_keywords": [],
#         "missing_patterns": []
#     }
# }

for test_name, result in results.items():
    if result["passed"]:
        print(f"✓ {test_name}")
    else:
        print(f"✗ {test_name}")
        print(f"  Missing keywords: {result['missing_keywords']}")
```

---

##### **Helper Functions**

**`create_length_rule`** - Custom length validation

```python
from promptengine.validation.validator import create_length_rule

rule = create_length_rule(
    min_length=50,
    max_length=500,
    severity="warning"
)

validator.rules.append(rule)
```

**`create_keyword_rule`** - Keyword presence check

```python
from promptengine.validation.validator import create_keyword_rule

# Must contain at least one of these
rule = create_keyword_rule(
    keywords=["helpful", "friendly", "professional"],
    require_all=False,  # At least one
    severity="info"
)

# Must contain ALL of these
rule = create_keyword_rule(
    keywords=["you are", "assistant"],
    require_all=True,
    severity="warning"
)
```

**`create_pattern_rule`** - Regex pattern matching

```python
from promptengine.validation.validator import create_pattern_rule

rule = create_pattern_rule(
    pattern=r"You are (a|an) .+ assistant",
    description="Should introduce role",
    severity="info"
)
```

---

**Real-World Validation Example**:

```python
# Production validator with strict rules
validator = PromptValidator()

# Remove lenient defaults
validator.remove_rule("min_length")

# Add strict production rules
validator.add_rule(
    "min_length_production",
    lambda content: len(content) >= 100,
    "Production prompts must be at least 100 characters",
    severity="error"
)

validator.add_rule(
    "has_role_definition",
    lambda content: "you are" in content.lower() or "your role" in content.lower(),
    "Prompt must define the AI's role",
    severity="error"
)

validator.add_rule(
    "no_profanity",
    lambda content: not any(word in content.lower() for word in PROFANITY_LIST),
    "Prompt contains inappropriate language",
    severity="error"
)

# Validate before deployment
result = validator.validate(production_prompt)
if not result.is_valid:
    raise Exception(f"Cannot deploy: {result.errors}")
```

---

## 🔄 Complete Workflow Example

**Scenario**: Building a chatbot system with multiple prompt variants

```python
from promptengine import (
    PromptTemplate,
    PromptRegistry,
    VersionControl,
    PromptValidator
)

# 1. CREATE prompts
template = PromptTemplate(
    name="customer_support_bot",
    template="""You are a {{tone}} customer support AI for {{company}}.

Your responsibilities:
- Answer customer questions about {{product}}
- {{additional_instruction}}
- Maintain a {{tone}} and helpful demeanor

Customer inquiry: {{inquiry}}""",
    variables=["tone", "company", "product", "additional_instruction", "inquiry"],
    default_values={
        "tone": "professional",
        "additional_instruction": "Escalate complex issues to human agents"
    },
    tags=["customer-support", "chatbot"],
    description="Customer support chatbot template"
)

# 2. ORGANIZE in registry
registry = PromptRegistry()
registry.add(template)
registry.save("company_prompts.json")

# 3. VALIDATE before use
validator = PromptValidator()
validator.add_rule(
    "mentions_company",
    lambda content: "{{company}}" in content or len(content) > 50,
    "Must mention company name",
    severity="warning"
)

result = validator.validate(template)
if not result.is_valid:
    raise Exception(f"Template validation failed: {result.errors}")

# 4. RENDER for production
prompt = template.render(
    tone="friendly",
    company="Acme Corp",
    product="Widget Pro",
    inquiry="How do I reset my password?"
)

# 5. VERSION the rendered prompt
vc = VersionControl(storage_path="production_versions.json")
version_id = vc.save_version(
    prompt,
    commit_message="Production v1 - friendly tone",
    author="ProductTeam"
)

# 6. USE with LLM
import openai

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": prompt.content},
        {"role": "user", "content": "I forgot my password"}
    ]
)

# 7. LATER: Update and version
prompt.update_content(prompt.content.replace("friendly", "professional"))
vc.save_version(
    prompt,
    commit_message="Changed to professional tone",
    author="ProductTeam"
)

# 8. A/B TEST: Load different versions
if user_segment == "enterprise":
    prompt = vc.get_version(prompt.id, version_number=2)  # Professional
else:
    prompt = vc.get_version(prompt.id, version_number=1)  # Friendly

# 9. ROLLBACK if needed
if customer_complaints > threshold:
    vc.rollback(prompt.id, version_number=1)  # Back to friendly
```

---

## 📊 Data Storage Formats

### **Registry Storage** (`prompts.json`)

```json
{
  "prompts": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "simple_translator",
      "content": "Translate the following to French:",
      "description": "Simple French translator",
      "metadata": {
        "created_by": "alice",
        "team": "localization"
      },
      "tags": ["translation", "french"],
      "created_at": "2024-01-15T10:30:00.000000",
      "updated_at": "2024-01-15T10:30:00.000000"
    }
  ],
  "templates": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440111",
      "name": "chatbot_template",
      "template": "You are a {{personality}} {{role}}. {{instructions}}",
      "description": "Flexible chatbot template",
      "variables": ["personality", "role", "instructions"],
      "default_values": {
        "personality": "helpful",
        "role": "assistant"
      },
      "metadata": {},
      "tags": ["chatbot", "flexible"],
      "created_at": "2024-01-15T11:00:00.000000",
      "updated_at": "2024-01-16T09:15:00.000000"
    }
  ]
}
```

### **Version Control Storage** (`versions.json`)

```json
{
  "version_histories": {
    "550e8400-e29b-41d4-a716-446655440000": [
      {
        "version_id": "770e8400-e29b-41d4-a716-446655440222",
        "version_number": 1,
        "parent_version": null,
        "prompt_data": {
          "id": "550e8400-e29b-41d4-a716-446655440000",
          "name": "simple_translator",
          "content": "Translate to French:",
          "description": "Simple French translator",
          "metadata": {},
          "tags": ["translation"],
          "created_at": "2024-01-15T10:30:00.000000",
          "updated_at": "2024-01-15T10:30:00.000000"
        },
        "prompt_type": "prompt",
        "commit_message": "Initial version",
        "author": "alice",
        "timestamp": "2024-01-15T10:30:00.000000"
      },
      {
        "version_id": "880e8400-e29b-41d4-a716-446655440333",
        "version_number": 2,
        "parent_version": 1,
        "prompt_data": {
          "id": "550e8400-e29b-41d4-a716-446655440000",
          "name": "simple_translator",
          "content": "Translate the following text to French:",
          "description": "Simple French translator",
          "metadata": {},
          "tags": ["translation", "french"],
          "created_at": "2024-01-15T10:30:00.000000",
          "updated_at": "2024-01-16T14:20:00.000000"
        },
        "prompt_type": "prompt",
        "commit_message": "Made instruction clearer",
        "author": "bob",
        "timestamp": "2024-01-16T14:20:00.000000"
      }
    ]
  },
  "current_versions": {
    "550e8400-e29b-41d4-a716-446655440000": 2
  }
}
```

---

## 🎯 Key Design Patterns

### **1. Serialization Pattern**

Every class can convert to/from dictionaries and JSON:

```python
# To dict/JSON
data = obj.to_dict()
json_str = obj.to_json()

# From dict/JSON
obj = ClassName.from_dict(data)
obj = ClassName.from_json(json_str)
```

**Why?** Enables saving to files, databases, APIs, etc.

---

### **2. Type Flexibility with Union Types**

```python
def add(self, item: Union[Prompt, PromptTemplate]) -> None:
    if isinstance(item, Prompt):
        self.prompts[item.name] = item
    elif isinstance(item, PromptTemplate):
        self.templates[item.name] = item
```

**Why?** Handle both Prompts and Templates with one method.

---

### **3. UUID for Identification**

```python
self.id = prompt_id or str(uuid4())
# Example: "550e8400-e29b-41d4-a716-446655440000"
```

**Why?**
- Globally unique (no collisions)
- Name can change, ID stays the same
- Track across systems

---

### **4. Immutable Snapshots**

Version control stores complete snapshots, not diffs:

```python
self.prompt_data = prompt.to_dict()  # Full copy
```

**Why?**
- Simple to implement
- Fast to retrieve any version
- No dependency chain (can delete middle versions)

**Trade-off**: Uses more storage than diff-based systems

---

### **5. Composition Over Inheritance**

Classes are composed, not inherited:

```python
class PromptRegistry:
    def __init__(self):
        self.prompts: Dict[str, Prompt] = {}  # Composition
        self.templates: Dict[str, PromptTemplate] = {}
```

**Why?** More flexible and easier to understand.

---

### **6. Optional Auto-persistence**

```python
vc = VersionControl(storage_path="file.json")
vc.save_version(prompt)  # Auto-saves to file

# vs

vc = VersionControl()  # No storage
vc.save_version(prompt)  # Only in memory
```

**Why?** Use in-memory for tests, file-based for production.

---

## 🚀 Integration Patterns

### **Pattern 1: Flask REST API**

```python
from flask import Flask, request, jsonify
from promptengine import PromptRegistry

app = Flask(__name__)
registry = PromptRegistry()
registry.load("prompts.json")

@app.route("/api/prompts/<name>/render", methods=["POST"])
def render(name):
    template = registry.get_template(name)
    variables = request.json
    prompt = template.render(**variables)
    return jsonify({"content": prompt.content})

# Usage:
# POST /api/prompts/chatbot/render
# Body: {"personality": "friendly", "role": "helper"}
```

---

### **Pattern 2: Multi-tenant Prompts**

```python
def get_registry(tenant_id):
    registry = PromptRegistry()
    registry.load(f"prompts_{tenant_id}.json")
    return registry

# Usage
tenant_registry = get_registry("acme-corp")
prompt = tenant_registry.get_prompt("onboarding")
```

---

### **Pattern 3: Environment-specific Prompts**

```python
import os

env = os.getenv("ENV", "development")
registry = PromptRegistry()
registry.load(f"prompts_{env}.json")

# Files:
# prompts_development.json
# prompts_staging.json
# prompts_production.json
```

---

### **Pattern 4: Prompt Caching**

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_rendered_prompt(template_name, **kwargs):
    template = registry.get_template(template_name)
    prompt = template.render(**kwargs)
    return prompt.content

# Identical calls hit cache
content1 = get_rendered_prompt("chatbot", personality="friendly")
content2 = get_rendered_prompt("chatbot", personality="friendly")  # Cached
```

---

### **Pattern 5: Prompt Analytics**

```python
class AnalyticsRegistry(PromptRegistry):
    def __init__(self):
        super().__init__()
        self.usage_stats = {}

    def get_prompt(self, name):
        prompt = super().get_prompt(name)
        self.usage_stats[name] = self.usage_stats.get(name, 0) + 1
        return prompt

    def popular_prompts(self, top_n=10):
        return sorted(
            self.usage_stats.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
```

---

## 📚 Examples Directory

### `examples/basic_usage.py`

**5 complete examples**:

1. **Simple Prompt**: Create a basic Prompt object
2. **Template with Variables**: Use PromptTemplate with Jinja2
3. **Registry Usage**: Organize prompts, search, save/load
4. **Version Control**: Save versions, view history, diffs, rollback
5. **Complete Integration**: All components working together

**Run**: `python examples/basic_usage.py`

---

### `examples/validation_examples.py`

**5 validation examples**:

1. **Basic Validation**: Default validation rules
2. **Custom Rules**: Add your own validation logic
3. **Template Testing**: Test templates with PromptTester
4. **Batch Validation**: Validate multiple prompts at once
5. **Production Workflow**: Strict validation for deployment

**Run**: `python examples/validation_examples.py`

---

### `examples/integration_guide.md`

**Integration tutorials**:

1. **Flask API**: REST API for serving prompts
2. **FastAPI**: Modern async API with Pydantic
3. **CLI Tool**: Command-line interface with Click
4. **Database**: SQLAlchemy integration for persistence
5. **Best Practices**: Caching, monitoring, security

---

## 🧪 Testing

### `tests/test_prompt.py`

**Unit tests cover**:

- Prompt creation and serialization
- Template rendering with variables
- Default values and missing variables
- Template validation
- Error handling for invalid templates

**Run tests**:

```bash
pip install -e ".[dev]"
pytest tests/
pytest tests/ -v          # Verbose
pytest tests/ --cov       # With coverage
```

---

## 🎓 Learning Path

### **Beginner** (30 minutes)

1. Read `QUICKSTART.md`
2. Run `examples/basic_usage.py`
3. Create your first prompt and template

### **Intermediate** (2 hours)

1. Read this file (ARCHITECTURE.md)
2. Run `examples/validation_examples.py`
3. Build a simple Flask API using the integration guide
4. Experiment with version control

### **Advanced** (1 day)

1. Read the source code in `promptengine/`
2. Write custom validation rules
3. Integrate with your database
4. Build a production prompt management system
5. Contribute improvements

---

## 🛠️ Extending PromptEngine

### **Add a New Storage Backend**

```python
class DatabaseRegistry(PromptRegistry):
    def __init__(self, db_connection):
        super().__init__()
        self.db = db_connection

    def save(self, *args, **kwargs):
        # Override to save to database
        for name, prompt in self.prompts.items():
            self.db.save("prompts", name, prompt.to_dict())
```

---

### **Add Prompt Encryption**

```python
from cryptography.fernet import Fernet

class EncryptedPrompt(Prompt):
    def __init__(self, *args, encryption_key=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cipher = Fernet(encryption_key) if encryption_key else None

    def to_dict(self):
        data = super().to_dict()
        if self.cipher:
            data['content'] = self.cipher.encrypt(
                data['content'].encode()
            ).decode()
        return data
```

---

### **Add Prompt Analytics**

```python
from datetime import datetime

class AnalyticsPrompt(Prompt):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.usage_count = 0
        self.last_used = None
        self.total_tokens = 0

    def use(self, llm_response):
        self.usage_count += 1
        self.last_used = datetime.utcnow().isoformat()
        self.total_tokens += len(llm_response.split())
```

---

## 📖 Summary

**PromptEngine** is a complete system for managing AI prompts with:

- **Core Classes**: `Prompt` and `PromptTemplate` for creating prompts
- **Registry**: Organize, search, and store prompts
- **Version Control**: Track changes like Git
- **Validation**: Quality control before deployment
- **Testing**: Test templates with different inputs
- **Integration**: Easy to integrate with any Python app

**File Organization**:
- `core/` - Fundamental prompt classes
- `version_control/` - Git-like versioning
- `validation/` - Quality control
- `examples/` - Working code examples
- `tests/` - Unit tests

**Key Features**:
- Jinja2 templates with variables
- JSON/YAML serialization
- Version history and diffs
- Custom validation rules
- Batch operations
- Multi-tenant support

Start with `QUICKSTART.md`, then dive into `examples/` to see it in action!
