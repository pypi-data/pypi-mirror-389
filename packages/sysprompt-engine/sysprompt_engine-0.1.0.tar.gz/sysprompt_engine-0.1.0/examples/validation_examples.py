"""Validation and testing examples for PromptEngine."""

from promptengine import Prompt, PromptTemplate, PromptValidator
from promptengine.validation.validator import (
    PromptTester,
    create_length_rule,
    create_keyword_rule,
)


def example_1_basic_validation():
    """Example 1: Basic prompt validation."""
    print("=" * 60)
    print("Example 1: Basic Validation")
    print("=" * 60)

    validator = PromptValidator()

    # Valid prompt
    good_prompt = Prompt(
        name="good_prompt",
        content="You are a helpful AI assistant that provides clear and concise answers.",
    )

    result = validator.validate(good_prompt)
    print(f"Good Prompt Validation: {result}")
    print(f"Is Valid: {result.is_valid}")
    print(f"Errors: {result.errors}")
    print(f"Warnings: {result.warnings}\n")

    # Invalid prompt (too short)
    bad_prompt = Prompt(name="bad_prompt", content="Hi")

    result = validator.validate(bad_prompt)
    print(f"Bad Prompt Validation: {result}")
    print(f"Is Valid: {result.is_valid}")
    print(f"Warnings: {result.warnings}\n")


def example_2_custom_rules():
    """Example 2: Adding custom validation rules."""
    print("=" * 60)
    print("Example 2: Custom Validation Rules")
    print("=" * 60)

    validator = PromptValidator()

    # Add custom rules
    validator.add_rule(
        "must_mention_ai",
        lambda content: "AI" in content or "artificial intelligence" in content.lower(),
        "Prompt should mention AI or artificial intelligence",
        severity="info",
    )

    # Add length rule
    length_rule = create_length_rule(50, 500, severity="warning")
    validator.rules.append(length_rule)

    # Add keyword rule
    keyword_rule = create_keyword_rule(
        ["helpful", "assistant", "professional"], require_all=False, severity="info"
    )
    validator.rules.append(keyword_rule)

    # Test prompt
    prompt = Prompt(
        name="test_prompt",
        content="You are a helpful AI assistant that provides accurate information.",
    )

    result = validator.validate(prompt)
    print(f"Validation Result: {result}")
    print(f"Is Valid: {result.is_valid}")
    print(f"Info messages: {result.info}\n")


def example_3_template_testing():
    """Example 3: Testing prompt templates."""
    print("=" * 60)
    print("Example 3: Template Testing")
    print("=" * 60)

    # Create a template
    template = PromptTemplate(
        name="email_writer",
        template="""Write a {{tone}} email to {{recipient}} about {{topic}}.

The email should:
- Start with a greeting
- {{instruction}}
- End with a sign-off

Context: {{context}}""",
        variables=["tone", "recipient", "topic", "instruction", "context"],
    )

    # Create tester
    tester = PromptTester()

    # Add test cases
    tester.add_test_case(
        name="professional_email",
        variables={
            "tone": "professional",
            "recipient": "the team",
            "topic": "project updates",
            "instruction": "Include key milestones",
            "context": "Q4 planning",
        },
        expected_keywords=["professional", "project updates", "team"],
        expected_patterns=[r"greeting", r"sign-off"],
    )

    tester.add_test_case(
        name="friendly_email",
        variables={
            "tone": "friendly",
            "recipient": "colleagues",
            "topic": "lunch meeting",
            "instruction": "Suggest a time",
            "context": "Team building",
        },
        expected_keywords=["friendly", "lunch", "colleagues"],
    )

    # Run tests
    results = tester.run_tests(template)

    print("Test Results:")
    for test_name, result in results.items():
        status = "PASSED" if result["passed"] else "FAILED"
        print(f"\n{test_name}: {status}")
        if result.get("missing_keywords"):
            print(f"  Missing keywords: {result['missing_keywords']}")
        if result.get("error"):
            print(f"  Error: {result['error']}")


def example_4_batch_validation():
    """Example 4: Batch validation of multiple prompts."""
    print("=" * 60)
    print("Example 4: Batch Validation")
    print("=" * 60)

    validator = PromptValidator()

    prompts = [
        Prompt(
            name="prompt_1",
            content="You are a helpful assistant that answers questions clearly.",
        ),
        Prompt(
            name="prompt_2",
            content="Short",  # This will trigger warnings
        ),
        Prompt(
            name="prompt_3",
            content="You are an AI that provides detailed explanations on technical topics.",
        ),
        PromptTemplate(
            name="template_1",
            template="Generate {{count}} examples of {{topic}}",  # Valid template
            variables=["count", "topic"],
        ),
    ]

    results = validator.validate_batch(prompts)

    print("Batch Validation Results:")
    for name, result in results.items():
        status = "VALID" if result.is_valid else "INVALID"
        print(f"\n{name}: {status}")
        if result.errors:
            print(f"  Errors: {result.errors}")
        if result.warnings:
            print(f"  Warnings: {result.warnings}")


def example_5_validation_workflow():
    """Example 5: Complete validation workflow for production."""
    print("=" * 60)
    print("Example 5: Production Validation Workflow")
    print("=" * 60)

    # Create strict validator for production
    validator = PromptValidator()

    # Remove lenient rules
    validator.remove_rule("min_length")

    # Add strict production rules
    validator.add_rule(
        "min_length_strict",
        lambda content: len(content.strip()) >= 50,
        "Production prompts must be at least 50 characters",
        severity="error",
    )

    validator.add_rule(
        "no_profanity",
        lambda content: not any(
            word in content.lower() for word in ["damn", "hell", "crap"]
        ),
        "Prompt contains inappropriate language",
        severity="error",
    )

    validator.add_rule(
        "has_context",
        lambda content: any(
            phrase in content.lower()
            for phrase in ["you are", "your role", "act as", "context:"]
        ),
        "Prompt should establish context or role",
        severity="warning",
    )

    # Test a production prompt
    production_prompt = Prompt(
        name="production_assistant",
        content="""You are a professional customer support AI assistant.

Your role is to:
1. Listen to customer concerns carefully
2. Provide accurate and helpful information
3. Escalate complex issues when necessary
4. Maintain a friendly and professional tone

Always prioritize customer satisfaction while following company policies.""",
    )

    result = validator.validate(production_prompt)

    print(f"Production Prompt Validation: {result}")
    print(f"\nValidation Details:")
    print(f"  Valid: {result.is_valid}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Warnings: {len(result.warnings)}")

    if result.is_valid:
        print("\n✓ Prompt is ready for production!")
    else:
        print("\n✗ Prompt needs fixes before deployment:")
        for error in result.errors:
            print(f"  - {error['message']}")


if __name__ == "__main__":
    example_1_basic_validation()
    example_2_custom_rules()
    example_3_template_testing()
    example_4_batch_validation()
    example_5_validation_workflow()
