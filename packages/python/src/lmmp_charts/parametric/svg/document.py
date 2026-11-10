"""Versioned, transport-neutral contract for a parametrically updated SVG.

The contract defines the initial SVG markup, the editable parameters, and
parameter-to-SVG bindings. It is *not* an HTML/SVG sanitizer; a future browser
renderer must sanitize markup before attaching it to the DOM.
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass
from typing import Any

from ..expressions.evaluator import ExpressionError, _valid_name, evaluate, references

FORMAT = "lmmp-parametric-svg"
VERSION = "1.0.0"
MAX_BINDINGS = 512
MAX_PARAMETERS = 100
ALLOWED_ATTRIBUTES = {
    "d", "transform", "fill", "stroke", "stroke-width", "stroke-dasharray",
    "opacity", "x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "rx", "ry",
    "points", "textContent",
}


def _is_number(value: Any) -> bool:
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value))


def _checked_parameters(raw: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(raw, dict) or len(raw) > MAX_PARAMETERS:
        raise ValueError("parameters must be an object with up to 100 entries")
    result = {}
    for key, parameter in raw.items():
        if not _valid_name(key) or not isinstance(parameter, dict):
            raise ValueError("Invalid parameter declaration")
        kind = parameter.get("type")
        value = parameter.get("value")
        if kind == "number":
            if not _is_number(value):
                raise ValueError(f"Parameter {key} requires a finite number")
            for field in ("min", "max"):
                if field in parameter and not _is_number(parameter[field]):
                    raise ValueError(f"Parameter {key}.{field} must be finite")
            if "min" in parameter and value < parameter["min"]:
                raise ValueError(f"Parameter {key} below minimum")
            if "max" in parameter and value > parameter["max"]:
                raise ValueError(f"Parameter {key} above maximum")
            if ("min" in parameter and "max" in parameter
                    and parameter["min"] > parameter["max"]):
                raise ValueError(f"Parameter {key} bounds inverted")
        elif kind == "string":
            if not isinstance(value, str) or len(value) > 2000:
                raise ValueError(f"Parameter {key} requires a string <=2000 chars")
            if "min" in parameter or "max" in parameter:
                raise ValueError("String parameters cannot have numeric bounds")
        else:
            raise ValueError(f"Unsupported parameter type for {key}")
        if not set(parameter).issubset({"type", "value", "min", "max", "unit"}):
            raise ValueError(f"Unknown parameter properties for {key}")
        if "unit" in parameter and not isinstance(parameter["unit"], str):
            raise ValueError("unit must be a string")
        result[key] = dict(parameter)
    return result


@dataclass(frozen=True, slots=True)
class ParametricSvgDocument:
    """Typed wrapper for validated, versioned SVG documents."""

    svg: str
    parameters: dict[str, dict[str, Any]]
    bindings: tuple[dict[str, Any], ...]
    constraints: tuple[dict[str, Any], ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ParametricSvgDocument":
        if not isinstance(data, dict):
            raise ValueError("SVG document must be an object")
        if data.get("format") != FORMAT or data.get("version") != VERSION:
            raise ValueError("Unsupported SVG contract format or version")
        if not set(data).issubset({"format", "version", "svg", "parameters", "bindings", "constraints"}):
            raise ValueError("Unexpected SVG contract property")
        svg = data.get("svg")
        if not isinstance(svg, str) or not svg.strip() or len(svg) > 2_000_000:
            raise ValueError("svg must be a nonempty string <=2MB")
        parameters = _checked_parameters(data.get("parameters"))
        raw_bindings = data.get("bindings")
        if not isinstance(raw_bindings, list) or len(raw_bindings) > MAX_BINDINGS:
            raise ValueError("bindings must be an array with up to 512 entries")
        for binding in raw_bindings:
            if not isinstance(binding, dict) or set(binding) != {"target", "attribute", "expression"}:
                raise ValueError("Malformed SVG binding")
            target = binding["target"]
            attr = binding["attribute"]
            if (not isinstance(target, str) or len(target) > 128
                    or not target.replace("-", "").replace("_", "").isalnum()
                    or not target[0].isalpha() or attr not in ALLOWED_ATTRIBUTES):
                raise ValueError("Invalid SVG binding target or attribute")
            refs = references(binding["expression"])
            if not refs.issubset(parameters):
                raise ExpressionError(f"Unknown binding variables: {refs - parameters.keys()}")
        raw_constraints = data.get("constraints", [])
        if not isinstance(raw_constraints, list) or len(raw_constraints) > 50:
            raise ValueError("constraints must be an array with up to 50 entries")
        for constraint in raw_constraints:
            if (not isinstance(constraint, dict) or set(constraint) != {"expression", "message"}
                    or not isinstance(constraint["message"], str)
                    or len(constraint["message"]) > 500):
                raise ValueError("Malformed constraint")
            refs = references(constraint["expression"])
            if not refs.issubset(parameters):
                raise ExpressionError("Unknown constraint variable")
        doc = cls(svg=svg, parameters=copy.deepcopy(parameters),
                  bindings=tuple(copy.deepcopy(raw_bindings)),
                  constraints=tuple(copy.deepcopy(raw_constraints)))
        doc.evaluate_bindings()  # Validate expressions against initial parameter values.
        return doc

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": FORMAT,
            "version": VERSION,
            "svg": self.svg,
            "parameters": copy.deepcopy(self.parameters),
            "bindings": copy.deepcopy(list(self.bindings)),
            "constraints": copy.deepcopy(list(self.constraints)),
        }

    def evaluate_bindings(self, overrides: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Compute SVG attributes for overrides without modifying the document."""
        overrides = {} if overrides is None else overrides
        if not isinstance(overrides, dict) or not set(overrides).issubset(self.parameters):
            raise ValueError("Unknown parameter overrides")
        revised = {name: {**parameter, "value": overrides.get(name, parameter["value"])}
                   for name, parameter in self.parameters.items()}
        parameters = _checked_parameters(revised)
        values = {name: parameter["value"] for name, parameter in parameters.items()}
        for constraint in self.constraints:
            if evaluate(constraint["expression"], values) is not True:
                raise ValueError(constraint["message"])
        result = []
        for binding in self.bindings:
            value = evaluate(binding["expression"], values)
            attr = binding["attribute"]
            if attr in {"d", "transform", "fill", "stroke", "stroke-dasharray", "points", "textContent"}:
                if not isinstance(value, str):
                    raise ExpressionError(f"Binding {attr} must produce a string")
            elif not _is_number(value):
                raise ExpressionError(f"Binding {attr} must produce a finite number")
            result.append({"target": binding["target"], "attribute": attr, "value": value})
        return result
