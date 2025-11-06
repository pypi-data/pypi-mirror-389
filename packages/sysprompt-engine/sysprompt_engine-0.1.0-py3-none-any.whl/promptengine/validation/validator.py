"""Validation and testing framework for prompts."""

import re
from typing import Any, Callable, Dict, List, Optional, Union

from promptengine.core.prompt import Prompt, PromptTemplate


class ValidationRule:
    """Represents a validation rule for prompts."""

    def __init__(
        self,
        name: str,
        validator: Callable[[str], bool],
        error_message: str,
        severity: str = "error",
    ):
        """
        Initialize a validation rule.

        Args:
            name: Name of the rule
            validator: Function that takes content string and returns True if valid
            error_message: Error message to show if validation fails
            severity: 'error', 'warning', or 'info'
        """
        self.name = name
        self.validator = validator
        self.error_message = error_message
        self.severity = severity

    def validate(self, content: str) -> tuple[bool, Optional[str]]:
        """
        Validate content against this rule.

        Args:
            content: Content to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            is_valid = self.validator(content)
            return is_valid, None if is_valid else self.error_message
        except Exception as e:
            return False, f"Validation error: {str(e)}"


class ValidationResult:
    """Result of prompt validation."""

    def __init__(self):
        """Initialize an empty validation result."""
        self.errors: List[Dict[str, str]] = []
        self.warnings: List[Dict[str, str]] = []
        self.info: List[Dict[str, str]] = []

    def add_issue(self, rule_name: str, message: str, severity: str) -> None:
        """Add a validation issue."""
        issue = {"rule": rule_name, "message": message}
        if severity == "error":
            self.errors.append(issue)
        elif severity == "warning":
            self.warnings.append(issue)
        else:
            self.info.append(issue)

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
        }

    def __str__(self) -> str:
        status = "VALID" if self.is_valid else "INVALID"
        return f"ValidationResult(status={status}, errors={len(self.errors)}, warnings={len(self.warnings)})"


class PromptValidator:
    """Validates prompts against a set of rules."""

    def __init__(self):
        """Initialize validator with default rules."""
        self.rules: List[ValidationRule] = []
        self._add_default_rules()

    def _add_default_rules(self) -> None:
        """Add default validation rules."""
        # Rule: Check minimum length
        self.add_rule(
            "min_length",
            lambda content: len(content.strip()) >= 10,
            "Prompt content is too short (minimum 10 characters)",
            severity="warning",
        )

        # Rule: Check maximum length
        self.add_rule(
            "max_length",
            lambda content: len(content) <= 50000,
            "Prompt content exceeds maximum length (50,000 characters)",
            severity="error",
        )

        # Rule: Check for empty content
        self.add_rule(
            "not_empty",
            lambda content: len(content.strip()) > 0,
            "Prompt content is empty",
            severity="error",
        )

        # Rule: Check for common placeholders
        self.add_rule(
            "no_todo_placeholders",
            lambda content: "TODO" not in content.upper()
            and "FIXME" not in content.upper(),
            "Prompt contains TODO or FIXME placeholders",
            severity="warning",
        )

        # Rule: Check for balanced braces (for templates)
        def check_balanced_braces(content: str) -> bool:
            open_count = content.count("{{")
            close_count = content.count("}}")
            return open_count == close_count

        self.add_rule(
            "balanced_braces",
            check_balanced_braces,
            "Template has unbalanced braces ({{ and }})",
            severity="error",
        )

    def add_rule(
        self,
        name: str,
        validator: Callable[[str], bool],
        error_message: str,
        severity: str = "error",
    ) -> None:
        """
        Add a custom validation rule.

        Args:
            name: Name of the rule
            validator: Function that validates content
            error_message: Error message if validation fails
            severity: 'error', 'warning', or 'info'
        """
        rule = ValidationRule(name, validator, error_message, severity)
        self.rules.append(rule)

    def remove_rule(self, name: str) -> bool:
        """
        Remove a validation rule by name.

        Args:
            name: Name of the rule to remove

        Returns:
            True if removed, False if not found
        """
        original_length = len(self.rules)
        self.rules = [r for r in self.rules if r.name != name]
        return len(self.rules) < original_length

    def validate(self, prompt: Union[Prompt, PromptTemplate]) -> ValidationResult:
        """
        Validate a prompt or template.

        Args:
            prompt: Prompt or PromptTemplate to validate

        Returns:
            ValidationResult object
        """
        result = ValidationResult()

        # Get content based on type
        if isinstance(prompt, Prompt):
            content = prompt.content
        elif isinstance(prompt, PromptTemplate):
            content = prompt.template_str
        else:
            result.add_issue("type_check", "Invalid prompt type", "error")
            return result

        # Run all validation rules
        for rule in self.rules:
            is_valid, error_msg = rule.validate(content)
            if not is_valid and error_msg:
                result.add_issue(rule.name, error_msg, rule.severity)

        return result

    def validate_batch(
        self, prompts: List[Union[Prompt, PromptTemplate]]
    ) -> Dict[str, ValidationResult]:
        """
        Validate multiple prompts.

        Args:
            prompts: List of prompts to validate

        Returns:
            Dictionary mapping prompt names to validation results
        """
        results = {}
        for prompt in prompts:
            name = prompt.name
            results[name] = self.validate(prompt)
        return results


class PromptTester:
    """Test prompts with mock or real responses."""

    def __init__(self):
        """Initialize the tester."""
        self.test_cases: List[Dict[str, Any]] = []

    def add_test_case(
        self,
        name: str,
        variables: Dict[str, Any],
        expected_keywords: Optional[List[str]] = None,
        expected_patterns: Optional[List[str]] = None,
    ) -> None:
        """
        Add a test case for a template.

        Args:
            name: Name of the test case
            variables: Variables to use for rendering
            expected_keywords: Keywords that should appear in rendered output
            expected_patterns: Regex patterns that should match in output
        """
        self.test_cases.append(
            {
                "name": name,
                "variables": variables,
                "expected_keywords": expected_keywords or [],
                "expected_patterns": expected_patterns or [],
            }
        )

    def run_tests(
        self, template: PromptTemplate
    ) -> Dict[str, Dict[str, Union[bool, str, List[str]]]]:
        """
        Run all test cases on a template.

        Args:
            template: PromptTemplate to test

        Returns:
            Dictionary of test results
        """
        results = {}

        for test_case in self.test_cases:
            name = test_case["name"]
            variables = test_case["variables"]
            expected_keywords = test_case["expected_keywords"]
            expected_patterns = test_case["expected_patterns"]

            try:
                # Render the template
                prompt = template.render(**variables)
                content = prompt.content

                # Check for expected keywords
                missing_keywords = [
                    kw for kw in expected_keywords if kw not in content
                ]

                # Check for expected patterns
                missing_patterns = [
                    pat for pat in expected_patterns if not re.search(pat, content)
                ]

                passed = len(missing_keywords) == 0 and len(missing_patterns) == 0

                results[name] = {
                    "passed": passed,
                    "rendered_content": content[:200] + "..."
                    if len(content) > 200
                    else content,
                    "missing_keywords": missing_keywords,
                    "missing_patterns": missing_patterns,
                }
            except Exception as e:
                results[name] = {
                    "passed": False,
                    "error": str(e),
                    "missing_keywords": [],
                    "missing_patterns": [],
                }

        return results

    def clear_tests(self) -> None:
        """Clear all test cases."""
        self.test_cases.clear()


def create_length_rule(
    min_length: int, max_length: int, severity: str = "warning"
) -> ValidationRule:
    """
    Create a custom length validation rule.

    Args:
        min_length: Minimum length in characters
        max_length: Maximum length in characters
        severity: Rule severity

    Returns:
        ValidationRule object
    """
    return ValidationRule(
        f"length_{min_length}_{max_length}",
        lambda content: min_length <= len(content) <= max_length,
        f"Content length must be between {min_length} and {max_length} characters",
        severity=severity,
    )


def create_keyword_rule(
    keywords: List[str], require_all: bool = False, severity: str = "info"
) -> ValidationRule:
    """
    Create a rule that checks for specific keywords.

    Args:
        keywords: List of keywords to check for
        require_all: If True, all keywords must be present; if False, at least one
        severity: Rule severity

    Returns:
        ValidationRule object
    """
    if require_all:
        validator = lambda content: all(kw in content for kw in keywords)
        message = f"Content must contain all keywords: {', '.join(keywords)}"
    else:
        validator = lambda content: any(kw in content for kw in keywords)
        message = f"Content must contain at least one keyword: {', '.join(keywords)}"

    return ValidationRule(
        f"keyword_check_{'all' if require_all else 'any'}",
        validator,
        message,
        severity=severity,
    )


def create_pattern_rule(
    pattern: str, description: str, severity: str = "warning"
) -> ValidationRule:
    """
    Create a rule that checks for a regex pattern.

    Args:
        pattern: Regex pattern to match
        description: Description of what the pattern checks
        severity: Rule severity

    Returns:
        ValidationRule object
    """
    return ValidationRule(
        f"pattern_{pattern[:20]}",
        lambda content: bool(re.search(pattern, content)),
        f"Content does not match pattern: {description}",
        severity=severity,
    )
