"""Configuration loading for Zelos extensions.

Provides JSON Schema default application and validation for extension configs.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping
import json
import os
import re

from jsonschema import ValidationError, validators


class ConfigError(RuntimeError):
    """Configuration loading error."""


class ConfigValidationError(ConfigError):
    """Configuration validation error.

    Attributes:
        errors: List of error messages
        field_errors: Dict mapping field paths to errors
    """

    def __init__(
        self,
        message: str,
        *,
        errors: list[str] | None = None,
        field_errors: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.errors = errors or []
        self.field_errors = field_errors or {}


def _deep_merge(base: dict, updates: dict) -> dict:
    """Deep merge updates into base, recursively merging nested dicts."""
    result = base.copy()
    for key, value in updates.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _resolve_ref(schema: Mapping[str, Any], root: Mapping[str, Any]) -> Mapping[str, Any]:
    """Resolve $ref using JSON Pointer, recursively resolving transitive refs."""
    ref = schema.get("$ref")
    if not ref or not ref.startswith("#/"):
        return schema

    # Navigate JSON Pointer path
    target = root
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        try:
            target = target[part]
        except (KeyError, TypeError) as e:
            raise ConfigError(f"Invalid $ref {ref!r}: path '{part}' not found") from e

    # Recursively resolve transitive $refs
    if isinstance(target, dict) and "$ref" in target:
        target = _resolve_ref(target, root)

    # Merge properties alongside $ref
    if extras := {k: v for k, v in schema.items() if k != "$ref"}:
        return {**target, **extras}
    return target


def _apply_defaults(
    schema: Mapping[str, Any] | bool,
    data: Any,
    validator_class: type,
    root: Mapping[str, Any] | None = None,
    _visited: set[int] | None = None,
    _property_exists: bool = True,
) -> Any:
    """Apply defaults from schema to data.

    Args:
        schema: JSON Schema (can be dict or boolean)
        data: Configuration data
        validator_class: jsonschema validator class
        root: Root schema for $ref resolution
        _visited: Set of visited schema IDs for cycle detection
        _property_exists: Whether the property existed in original data (for null handling)
    """
    if root is None:
        root = schema if isinstance(schema, dict) else {}
    if _visited is None:
        _visited = set()

    # Handle boolean schemas
    if isinstance(schema, bool):
        return data

    # Resolve $ref first (including transitive refs)
    schema = _resolve_ref(schema, root)

    # Cycle detection - check AFTER resolving $ref to detect actual schema cycles
    schema_id = id(schema)
    if schema_id in _visited:
        return data if _property_exists else None
    _visited.add(schema_id)

    try:
        schema_type = schema.get("type")
        default = schema.get("default")

        # Initialize value
        if not _property_exists:
            # Property didn't exist in original data - use defaults
            if default is not None:
                value = deepcopy(default)
            elif schema_type == "object":
                value = {}
            elif schema_type == "array":
                value = []
            elif "anyOf" in schema or "oneOf" in schema or "allOf" in schema:
                # Has composition keywords - don't return None yet, process them below
                value = None
            else:
                return None
        elif data is None:
            # Property existed but was explicitly None - preserve it
            return None
        else:
            # Property exists with non-None value
            value = deepcopy(data) if isinstance(data, (dict, list)) else data
            # Merge defaults
            if isinstance(default, dict) and isinstance(value, dict):
                value = _deep_merge(deepcopy(default), value)

        # Composition keywords
        if "allOf" in schema:
            for sub in schema["allOf"]:
                value = _apply_defaults(sub, value, validator_class, root, _visited, True)

        if "anyOf" in schema or "oneOf" in schema:
            # Try each option until one validates
            for opt in schema.get("anyOf") or schema.get("oneOf", []):
                sub = _resolve_ref(opt, root) if isinstance(opt, dict) else opt
                candidate = _apply_defaults(
                    sub,
                    deepcopy(value) if value is not None else None,
                    validator_class,
                    root,
                    _visited,
                    _property_exists,
                )
                try:
                    validator_class(sub).validate(candidate)
                    value = candidate
                    break
                except ValidationError:
                    continue

        # Object properties
        if (schema_type == "object" or "properties" in schema) and isinstance(value, dict):
            for prop, sub in schema.get("properties", {}).items():
                prop_exists = prop in value
                updated = _apply_defaults(sub, value.get(prop), validator_class, root, _visited, prop_exists)
                if updated is not None or prop_exists:
                    value[prop] = updated

        # Pattern properties - apply defaults to matching existing properties
        if "patternProperties" in schema and isinstance(value, dict):
            for pattern, prop_schema in schema["patternProperties"].items():
                for prop_name in list(value.keys()):
                    if re.match(pattern, prop_name):
                        value[prop_name] = _apply_defaults(
                            prop_schema, value[prop_name], validator_class, root, _visited, True
                        )

        # Arrays
        if schema_type == "array" and isinstance(value, list):

            def schema_for_index(idx: int) -> Any:
                prefix_items = schema.get("prefixItems")
                if isinstance(prefix_items, list):
                    if idx < len(prefix_items):
                        return prefix_items[idx]
                    items_schema = schema.get("items")
                    if isinstance(items_schema, list):
                        if idx < len(items_schema):
                            return items_schema[idx]
                        additional = schema.get("additionalItems")
                        if additional is None:
                            return True
                        return additional
                    if items_schema is None:
                        return True
                    return items_schema

                items_schema = schema.get("items")
                if isinstance(items_schema, list):
                    if idx < len(items_schema):
                        return items_schema[idx]
                    additional = schema.get("additionalItems")
                    if additional is None:
                        return True
                    return additional

                if items_schema is None:
                    return True
                return items_schema

            # Apply defaults to existing entries
            for index, item_value in enumerate(value):
                item_schema = schema_for_index(index)
                if isinstance(item_schema, (dict, bool)):
                    value[index] = _apply_defaults(
                        item_schema,
                        item_value,
                        validator_class,
                        root,
                        _visited,
                        True,
                    )

            # Fill up to minItems when defaults are available
            min_items = schema.get("minItems")
            if isinstance(min_items, int) and len(value) < min_items:
                for index in range(len(value), min_items):
                    item_schema = schema_for_index(index)
                    if not isinstance(item_schema, (dict, bool)):
                        break
                    item_default = _apply_defaults(
                        item_schema,
                        None,
                        validator_class,
                        root,
                        _visited,
                        False,
                    )
                    if item_default is None:
                        break
                    value.append(deepcopy(item_default))

        return value
    finally:
        _visited.discard(schema_id)


def _build_validation_error(errors: list, prefix: str) -> ConfigValidationError:
    """Build structured validation error from jsonschema errors."""
    error_messages = []
    field_errors = {}
    for error in errors:
        path = ".".join(str(p) for p in error.absolute_path) or "<root>"
        error_messages.append(f"  • {path}: {error.message}")
        field_errors[path] = error.message

    return ConfigValidationError(
        f"{prefix}:\n" + "\n".join(error_messages),
        errors=error_messages,
        field_errors=field_errors,
    )


def load_config(
    *,
    config_path: str | Path = "config.json",
    schema_path: str | Path = "config.schema.json",
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Load and validate extension configuration.

    Loads config and schema files from current directory, applies defaults,
    validates, and merges overrides.

    Args:
        config_path: Config file path (default: "config.json")
        schema_path: Schema file path (default: "config.schema.json")
        overrides: Runtime overrides to merge (optional)

    Returns:
        Merged configuration dictionary with defaults applied

    Raises:
        ConfigValidationError: If validation fails
        FileNotFoundError: If required files don't exist
        JSONDecodeError: If files contain invalid JSON

    Example:
        >>> config = load_config()
        >>> config = load_config(overrides={"debug": True})
        >>> config = load_config(config_path="custom.json")
    """
    # Load files from current directory
    env_config_path = os.environ.get("ZELOS_CONFIG_PATH")
    resolved_config_path = env_config_path if env_config_path and config_path == "config.json" else config_path

    schema_file = Path(schema_path)
    config_file = Path(resolved_config_path)

    schema_data = json.loads(schema_file.read_text()) if schema_file.exists() else {}
    config_data = json.loads(config_file.read_text()) if config_file.exists() else {}

    # Apply schema defaults and validate
    if schema_data:
        validator_class = validators.validator_for(schema_data)
        result = _apply_defaults(schema_data, config_data, validator_class)

        if errors := list(validator_class(schema_data).iter_errors(result)):
            raise _build_validation_error(errors, "Configuration validation failed")
    else:
        result = config_data

    # Apply overrides and re-validate
    if overrides:
        result = _deep_merge(result, overrides)

        if schema_data:
            if errors := list(validator_class(schema_data).iter_errors(result)):
                raise _build_validation_error(errors, "Configuration validation failed (after overrides)")

    return result
