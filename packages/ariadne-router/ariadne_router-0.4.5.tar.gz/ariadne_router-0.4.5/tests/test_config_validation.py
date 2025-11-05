"""Unit tests for the configuration validation framework."""

from __future__ import annotations

from pathlib import Path

import pytest

from ariadne.config.validation import (
    ChoiceRule,
    ConfigurationSchema,
    ConfigurationValidator,
    CustomRule,
    FieldSchema,
    PathRule,
    RangeRule,
    RegexRule,
    TypeRule,
    register_schema,
    validate_config,
)


@pytest.fixture(autouse=True)
def reset_global_validator(monkeypatch: pytest.MonkeyPatch) -> None:
    import ariadne.config.validation as validation_module

    monkeypatch.setattr(validation_module, "_global_validator", None)


def test_type_rule_reports_mismatch() -> None:
    rule = TypeRule(int)
    issue = rule.validate("optimization.level", "high", {})

    assert issue is not None
    assert issue.code == "TYPE_MISMATCH"
    assert issue.context["expected_type"] == "int"


def test_range_rule_detects_out_of_bounds() -> None:
    rule = RangeRule(min_value=1, max_value=5)
    issue = rule.validate("performance.cache_size", 10, {})

    assert issue is not None
    assert "above maximum" in issue.message


def test_choice_rule_case_insensitive() -> None:
    rule = ChoiceRule(["low", "medium", "high"], case_sensitive=False)
    assert rule.validate("performance.level", "Medium", {}) is None
    invalid = rule.validate("performance.level", "invalid", {})
    assert invalid is not None and invalid.code == "INVALID_CHOICE"


def test_regex_rule_enforces_pattern() -> None:
    rule = RegexRule(r"^[a-z]+$")
    assert rule.validate("logging.level", "debug", {}) is None
    assert rule.validate("logging.level", "DEBUG123", {}) is not None


def test_path_rule_checks_constraints(tmp_path: Path) -> None:
    file_path = tmp_path / "config.yaml"
    file_path.write_text("test")

    dir_rule = PathRule(must_exist=True, must_be_dir=True)
    assert dir_rule.validate("paths.data", str(tmp_path), {}) is None
    assert dir_rule.validate("paths.data", str(file_path), {}) is not None

    file_rule = PathRule(must_exist=True, must_be_file=True)
    assert file_rule.validate("paths.file", str(file_path), {}) is None


def test_custom_rule_returns_issue() -> None:
    rule = CustomRule(lambda value, _: "invalid" if value == 0 else None, suggestion="Use non-zero")
    issue = rule.validate("optimization.level", 0, {})

    assert issue is not None
    assert issue.suggestion == "Use non-zero"


def test_field_schema_required_and_optional() -> None:
    schema = FieldSchema(description="Test", required=True, rules=[TypeRule(int)])
    result_missing = schema.validate("field", None, {})
    assert result_missing.error_issues

    result = schema.validate("field", 3, {})
    assert result.is_valid is True


def test_configuration_schema_and_validator() -> None:
    schema = ConfigurationSchema("Example")
    schema.add_field("level", FieldSchema(rules=[ChoiceRule(["low", "high"])]))
    schema.add_field("max", FieldSchema(rules=[RangeRule(min_value=1, max_value=5)], required=False))

    validator = ConfigurationValidator()
    validator.register_schema("example", schema)
    validator.add_global_rule(CustomRule(lambda config, _: None if config.get("level") != "blocked" else "blocked"))

    result = validator.validate({"level": "high", "max": 3}, "example")
    assert result.is_valid is True

    invalid = validator.validate({"level": "invalid"}, "example")
    assert invalid.is_valid is False


def test_global_validate_config(monkeypatch: pytest.MonkeyPatch) -> None:
    schema = ConfigurationSchema("Global example")
    schema.add_field("enabled", FieldSchema(rules=[TypeRule(bool)]))
    register_schema("global", schema)

    valid_result = validate_config({"enabled": True}, "global")
    assert valid_result.is_valid

    invalid_result = validate_config({"enabled": "yes"}, "global")
    assert not invalid_result.is_valid
