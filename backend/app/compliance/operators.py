"""Safe operator DSL for compliance rules.

Rules declare an operator by name; we dispatch through a fixed table. There is
NO eval/exec and no arbitrary code path, so a malicious rule (or config value)
cannot execute logic. Configuration data is only ever compared, never run.
"""
from __future__ import annotations

from typing import Any, Callable, Dict

from app.normalization.model import INFINITE_TIMEOUT


def _is_true(value: Any, _operand: Any = None) -> bool:
    return value is True


def _is_false(value: Any, _operand: Any = None) -> bool:
    return value is False


def _equals(value: Any, operand: Any) -> bool:
    return value == operand


def _not_equals(value: Any, operand: Any) -> bool:
    return value != operand


def _min(value: Any, operand: Any) -> bool:
    try:
        return value >= operand
    except TypeError:
        return False


def _max(value: Any, operand: Any) -> bool:
    try:
        return value <= operand
    except TypeError:
        return False


def _range(value: Any, operand: Any) -> bool:
    try:
        low, high = operand
        return low <= value <= high
    except (TypeError, ValueError):
        return False


def _present(value: Any, _operand: Any = None) -> bool:
    return value is not None


_OPERATORS: Dict[str, Callable[[Any, Any], bool]] = {
    "is_true": _is_true,
    "is_false": _is_false,
    "equals": _equals,
    "not_equals": _not_equals,
    "min": _min,
    "max": _max,
    "range": _range,
    "present": _present,
}

VALID_OPERATORS = frozenset(_OPERATORS)


def evaluate(op: str, value: Any, operand: Any = None) -> bool:
    """Return True if ``value`` satisfies operator ``op`` against ``operand``."""
    try:
        fn = _OPERATORS[op]
    except KeyError as exc:
        raise ValueError(f"Unknown operator: {op!r}") from exc
    return fn(value, operand)


def describe_expected(op: str, operand: Any) -> str:
    return {
        "is_true": "enabled / yes",
        "is_false": "disabled / no",
        "equals": f"= {operand}",
        "not_equals": f"!= {operand}",
        "min": f">= {operand}",
        "max": f"<= {operand}",
        "range": (
            f"between {operand[0]} and {operand[1]}"
            if isinstance(operand, (list, tuple)) and len(operand) == 2
            else "within allowed range"
        ),
        "present": "configured",
    }.get(op, "compliant value")


def describe_observed(field: str, value: Any) -> str:
    if value is None:
        return "not configured / not detected"
    if field == "idle_timeout_minutes" and isinstance(value, int) and value >= INFINITE_TIMEOUT:
        return "no timeout (session never expires)"
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)
