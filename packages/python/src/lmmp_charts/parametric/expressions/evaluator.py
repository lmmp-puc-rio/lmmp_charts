"""Small, deterministic JSON expression evaluator shared by the SVG contract.

This is deliberately not Python eval(): only a closed list of safe operators is
accepted. It operates on scalar values and SVG path commands, with bounded
expression depth and length. Expressions are supplied by chart authors, not
compiled from arbitrary user strings.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from typing import Any

MAX_DEPTH = 40
MAX_NODES = 2048
MAX_PATH_COMMANDS = 500
MAX_OUTPUT_LENGTH = 50000

VARIABLE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")
FORBIDDEN_SEGMENTS = {"constructor", "prototype", "__proto__"}
OPERATORS: dict[str, tuple[int, int | None]] = {
    "add": (2, None), "sub": (2, 2), "mul": (2, None), "div": (2, 2),
    "pow": (2, 2), "neg": (1, 1), "abs": (1, 1), "sqrt": (1, 1),
    "sin": (1, 1), "cos": (1, 1), "tan": (1, 1),
    "atan2": (2, 2), "radians": (1, 1), "degrees": (1, 1),
    "min": (2, None), "max": (2, None),
    "lt": (2, 2), "lte": (2, 2), "gt": (2, 2), "gte": (2, 2),
    "eq": (2, 2), "ne": (2, 2), "if": (3, 3), "concat": (1, None),
}
PATH_COMMAND_ARGUMENTS = {"M": 2, "L": 2, "C": 6, "Q": 4, "A": 7, "Z": 0}


class ExpressionError(ValueError):
    """Invalid expression, operand, or nonfinite result."""


def _finite(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ExpressionError("An operator requires finite numbers")
    try:
        v = float(value)
    except (OverflowError, ValueError) as e:
        raise ExpressionError("Number is too large") from e
    if not math.isfinite(v):
        raise ExpressionError("Nonfinite numerical value")
    return v


def _valid_name(name: Any) -> bool:
    return (isinstance(name, str) and bool(VARIABLE_NAME.fullmatch(name))
            and not FORBIDDEN_SEGMENTS.intersection(name.split(".")))


def references(expression: Any) -> set[str]:
    """Validate the expression grammar and return referenced parameter names."""
    refs: set[str] = set()
    count = 0

    def walk(node: Any, depth: int) -> None:
        nonlocal count
        count += 1
        if depth > MAX_DEPTH or count > MAX_NODES:
            raise ExpressionError("Expression complexity limit exceeded")
        if not isinstance(node, dict):
            raise ExpressionError("Each expression must be an object")
        if set(node) == {"const"}:
            val = node["const"]
            if type(val) not in (str, bool, int, float):
                raise ExpressionError("Unsupported constant type")
            if type(val) in (int, float):
                _finite(val)
            if isinstance(val, str) and len(val) > 2000:
                raise ExpressionError("String constant too long")
            return
        if set(node) == {"var"}:
            name = node["var"]
            if not _valid_name(name):
                raise ExpressionError("Invalid parameter name")
            refs.add(name)
            return
        op = node.get("op")
        if op == "path":
            if set(node) != {"op", "commands"} or not isinstance(node["commands"], list):
                raise ExpressionError("Malformed SVG path")
            commands = node["commands"]
            if len(commands) > MAX_PATH_COMMANDS:
                raise ExpressionError("Too many SVG path commands")
            for command in commands:
                if not isinstance(command, dict) or set(command) != {"cmd", "values"}:
                    raise ExpressionError("Malformed SVG path command")
                cmd, values = command["cmd"], command["values"]
                if cmd not in PATH_COMMAND_ARGUMENTS or not isinstance(values, list):
                    raise ExpressionError("Unsupported SVG path command")
                if len(values) != PATH_COMMAND_ARGUMENTS[cmd]:
                    raise ExpressionError(f"Invalid {cmd} command arity")
                for part in values:
                    walk(part, depth + 1)
            return
        if (set(node) != {"op", "args"} or op not in OPERATORS
                or not isinstance(node["args"], list)):
            raise ExpressionError("Unknown or malformed expression operation")
        minimum, maximum = OPERATORS[op]
        args = node["args"]
        if len(args) < minimum or (maximum is not None and len(args) > maximum):
            raise ExpressionError(f"Invalid number of arguments for {op}")
        for arg in args:
            walk(arg, depth + 1)

    walk(expression, 0)
    return refs


def _format_num(value: Any) -> str:
    number = _finite(value)
    # Identical documented precision in both evaluators; SVG does not need
    # more than six decimals in the current viewport units.
    out = f"{number:.6f}".rstrip("0").rstrip(".")
    return "0" if out in ("", "-0") else out


def evaluate(expression: Any, variables: Mapping[str, Any]) -> Any:
    """Evaluate a validated JSON expression against flat named parameters."""
    refs = references(expression)
    if not isinstance(variables, Mapping):
        raise ExpressionError("Variables must be a mapping")
    for ref in refs:
        if ref not in variables:
            raise ExpressionError(f"Unknown parameter: {ref}")

    def run(node: dict[str, Any]) -> Any:
        if "const" in node:
            return node["const"]
        if "var" in node:
            val = variables[node["var"]]
            if type(val) not in (str, bool, int, float):
                raise ExpressionError("Unsupported parameter value")
            if type(val) in (int, float):
                _finite(val)
            return val

        op = node["op"]
        if op == "path":
            chunks: list[str] = []
            for command in node["commands"]:
                cmd = command["cmd"]
                values = [run(e) for e in command["values"]]
                if cmd == "A":
                    if values[3] not in (0, 1) or values[4] not in (0, 1):
                        raise ExpressionError("SVG arc flags must be 0 or 1")
                    if _finite(values[0]) < 0 or _finite(values[1]) < 0:
                        raise ExpressionError("SVG arc radii must be nonnegative")
                segment = " ".join([cmd, *(_format_num(v) for v in values)]).strip()
                chunks.append(segment)
            result = " ".join(chunks)
            if len(result) > MAX_OUTPUT_LENGTH:
                raise ExpressionError("Output SVG path is too long")
            return result

        if op == "if":
            condition = run(node["args"][0])
            if not isinstance(condition, bool):
                raise ExpressionError("if condition must be boolean")
            return run(node["args"][1 if condition else 2])

        values = [run(a) for a in node["args"]]
        if op == "concat":
            if not all(type(v) in (str, int, float, bool) for v in values):
                raise ExpressionError("concat requires scalar values")
            result = "".join(str(v).lower() if isinstance(v, bool) else
                             str(int(v)) if isinstance(v, float) and v.is_integer()
                             else str(v) for v in values)
            if len(result) > MAX_OUTPUT_LENGTH:
                raise ExpressionError("Output text is too long")
            return result
        if op in ("eq", "ne"):
            same = ((isinstance(values[0], (float, int)) and not isinstance(values[0], bool)
                     and isinstance(values[1], (float, int)) and not isinstance(values[1], bool)
                     and _finite(values[0]) == _finite(values[1]))
                    or (type(values[0]) is type(values[1]) and values[0] == values[1]))
            return same if op == "eq" else not same
        nums = [_finite(v) for v in values]
        try:
            if op == "add": result = sum(nums)
            elif op == "sub": result = nums[0] - nums[1]
            elif op == "mul": result = math.prod(nums)
            elif op == "div": result = nums[0] / nums[1]
            elif op == "pow": result = math.pow(nums[0], nums[1])
            elif op == "neg": result = -nums[0]
            elif op == "abs": result = abs(nums[0])
            elif op == "sqrt": result = math.sqrt(nums[0])
            elif op == "sin": result = math.sin(nums[0])
            elif op == "cos": result = math.cos(nums[0])
            elif op == "tan": result = math.tan(nums[0])
            elif op == "atan2": result = math.atan2(nums[0], nums[1])
            elif op == "radians": result = math.radians(nums[0])
            elif op == "degrees": result = math.degrees(nums[0])
            elif op == "min": result = min(nums)
            elif op == "max": result = max(nums)
            elif op == "lt": return nums[0] < nums[1]
            elif op == "lte": return nums[0] <= nums[1]
            elif op == "gt": return nums[0] > nums[1]
            elif op == "gte": return nums[0] >= nums[1]
            else: raise ExpressionError(f"Unsupported operation: {op}")
        except (OverflowError, ZeroDivisionError, ValueError) as e:
            raise ExpressionError(f"Invalid arithmetic for {op}") from e
        return _finite(result)

    return run(expression)
