"""Basic usage examples for PromptEngine."""

from promptengine import Prompt, PromptTemplate, PromptRegistry, VersionControl


def example_1_simple_prompt():
    """Example 1: Creating a simple prompt."""
    print("=" * 60)
    print("Example 1: Simple Prompt")
    print("=" * 60)

    prompt = Prompt(
        name="greeting_prompt",
        content="You are a helpful AI assistant. Greet the user warmly and ask how you can help.",
        description="A simple greeting prompt",
        tags=["greeting", "assistant"],
    )

    print(f"Created: {prompt}")
    print(f"Content: {prompt.content}\n")


def example_2_template_with_variables():
    """Example 2: Using templates with variables."""
    print("=" * 60)
    print("Example 2: Template with Variables")
    print("=" * 60)

    template = PromptTemplate(
        name="code_reviewer",
        template="""You are a {{expertise}} {{language}} developer.
Review the following code and provide feedback on:
- Code quality and readability
- Best practices
- Potential bugs or issues

Code to review:
```{{language}}
{{code}}
```

Please provide constructive feedback.""",
        variables=["expertise", "language", "code"],
        description="Code review prompt template",
        tags=["code", "review"],
    )

    # Render with specific values
    prompt = template.render(
        expertise="senior",
        language="Python",
        code='def add(a, b):\n    return a + b',
    )

    print(f"Template: {template}")
    print(f"\nRendered Prompt:\n{prompt.content}\n")


def example_3_registry():
    """Example 3: Using the prompt registry."""
    print("=" * 60)
    print("Example 3: Prompt Registry")
    print("=" * 60)

    registry = PromptRegistry()

    # Add some prompts
    prompt1 = Prompt(
        name="summarizer",
        content="Summarize the following text in 3 bullet points.",
        tags=["summarization"],
    )

    prompt2 = Prompt(
        name="translator",
        content="Translate the following text to French.",
        tags=["translation"],
    )

    template1 = PromptTemplate(
        name="task_generator",
        template="Generate {{count}} {{difficulty}} coding tasks about {{topic}}.",
        variables=["count", "difficulty", "topic"],
        tags=["coding", "education"],
    )

    registry.add(prompt1)
    registry.add(prompt2)
    registry.add(template1)

    print(f"Registry: {registry}")
    print(f"Prompts: {registry.list_prompts()}")
    print(f"Templates: {registry.list_templates()}")

    # Search
    results = registry.search("coding")
    print(f"\nSearch results for 'coding': {results}")

    # Save to file
    registry.save("my_prompts.json")
    print("\nRegistry saved to my_prompts.json\n")


def example_4_version_control():
    """Example 4: Version control."""
    print("=" * 60)
    print("Example 4: Version Control")
    print("=" * 60)

    vc = VersionControl(storage_path="prompt_versions.json")

    # Create a prompt
    prompt = Prompt(
        name="assistant_v1",
        content="You are a helpful assistant.",
    )

    # Save first version
    v1_id = vc.save_version(
        prompt, commit_message="Initial version", author="Developer"
    )
    print(f"Saved version 1: {v1_id}")

    # Update the prompt
    prompt.update_content("You are a helpful and friendly AI assistant.")
    v2_id = vc.save_version(
        prompt, commit_message="Made assistant more friendly", author="Developer"
    )
    print(f"Saved version 2: {v2_id}")

    # Update again
    prompt.update_content(
        "You are a helpful, friendly, and knowledgeable AI assistant."
    )
    v3_id = vc.save_version(
        prompt, commit_message="Added knowledgeable attribute", author="Developer"
    )
    print(f"Saved version 3: {v3_id}")

    # View history
    history = vc.get_history(prompt.id)
    print("\nVersion History:")
    for version in history:
        print(
            f"  v{version['version_number']}: {version['commit_message']} (by {version['author']})"
        )

    # View diff
    diff_result = vc.diff(prompt.id, 1, 3)
    if diff_result:
        print(f"\nDiff between v1 and v3:")
        print(diff_result["diff"])

    # Rollback
    print("\nRolling back to version 2...")
    rolled_back = vc.rollback(prompt.id, 2)
    if rolled_back:
        print(f"Rolled back content: {rolled_back.content}\n")


def example_5_integration():
    """Example 5: Complete integration workflow."""
    print("=" * 60)
    print("Example 5: Complete Integration Workflow")
    print("=" * 60)

    # Initialize components
    registry = PromptRegistry()
    vc = VersionControl(storage_path="app_prompts_versions.json")

    # Create a template for your application
    chatbot_template = PromptTemplate(
        name="chatbot_personality",
        template="""You are {{name}}, a {{personality}} chatbot.

Your role: {{role}}

Key traits:
{{traits}}

When responding:
- Use a {{tone}} tone
- {{instruction_1}}
- {{instruction_2}}

Now, respond to the user.""",
        variables=[
            "name",
            "personality",
            "role",
            "traits",
            "tone",
            "instruction_1",
            "instruction_2",
        ],
        default_values={"tone": "friendly", "instruction_1": "Be helpful"},
        tags=["chatbot", "personality"],
    )

    # Add to registry
    registry.add(chatbot_template)

    # Render for different use cases
    customer_service_bot = chatbot_template.render(
        name="ServiceBot",
        personality="professional and empathetic",
        role="customer service representative",
        traits="- Patient and understanding\n- Solution-oriented\n- Clear communicator",
        instruction_2="Focus on resolving issues quickly",
    )

    print("Generated Customer Service Bot Prompt:")
    print(customer_service_bot.content)

    # Version it
    v_id = vc.save_version(
        customer_service_bot,
        commit_message="Initial customer service bot",
        author="Product Team",
    )
    print(f"\nVersioned as: {v_id}")

    # Save everything
    registry.save("application_prompts.json")
    print("\nAll prompts saved and versioned!\n")


if __name__ == "__main__":
    example_1_simple_prompt()
    example_2_template_with_variables()
    example_3_registry()
    example_4_version_control()
    example_5_integration()
