"""Build the approved interfacial diagram as a parametric SVG document."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any
from xml.sax.saxutils import escape, quoteattr

from lmmp_charts.geometry.interfacial import InterfacialGeometry
from lmmp_charts.models.wettability import Wettability
from lmmp_charts.parametric.expressions.evaluator import evaluate
from lmmp_charts.parametric.svg.document import ParametricSvgDocument

_WIDTH = 850
_HEIGHT = 1150
_Y_RANGE = 17.0
_PIXELS_PER_UNIT = 1120 / _Y_RANGE
_VIEWBOX = "-0.451 -0.228 12.902 17.456"
_MAX_ANGLE = math.nextafter(90.0, 0.0)


def _const(value: int | float | str | bool) -> dict[str, Any]:
    return {"const": value}


def _var(name: str) -> dict[str, Any]:
    return {"var": name}


def _op(name: str, *args: dict[str, Any]) -> dict[str, Any]:
    return {"op": name, "args": list(args)}


def _path(*commands: tuple[str, Sequence[dict[str, Any]]]) -> dict[str, Any]:
    return {
        "op": "path",
        "commands": [
            {"cmd": command, "values": list(values)}
            for command, values in commands
        ],
    }


def _format_number(value: int | float) -> str:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("SVG coordinates must be finite")
    result = f"{number:.6f}".rstrip("0").rstrip(".")
    return "0" if result in ("", "-0") else result


def _coordinates_path(points: Sequence[Sequence[float]], *, close: bool = True) -> str:
    if len(points) == 0:
        raise ValueError("An SVG path requires at least one point")
    parts = [f"M {_format_number(points[0][0])} {_format_number(points[0][1])}"]
    parts.extend(
        f"L {_format_number(point[0])} {_format_number(point[1])}"
        for point in points[1:]
    )
    if close:
        parts.append("Z")
    return " ".join(parts)


def _element(tag: str, attributes: dict[str, str], content: str | None = None) -> str:
    attrs = " ".join(f"{name}={quoteattr(value)}" for name, value in attributes.items())
    if content is None:
        return f"<{tag} {attrs}/>"
    return f"<{tag} {attrs}>{content}</{tag}>"


def _px(value: float) -> str:
    return _format_number(value / _PIXELS_PER_UNIT)


class InterfacialBuilder:
    """Create the interfacial diagram and its parameter-to-SVG bindings.

    The returned document is a transport representation, not sanitized markup
    for direct insertion into a browser DOM.
    """

    def __init__(self) -> None:
        self._geometry = InterfacialGeometry()

    def build(self, model: Wettability) -> ParametricSvgDocument:
        """Return a validated parametric SVG document for ``model``."""
        if not isinstance(model, Wettability):
            raise TypeError("InterfacialBuilder requires a Wettability instance")
        if not (0 <= model.theta_receding < model.theta < model.theta_advancing < 90):
            raise ValueError("The approved interfacial figure requires angles < 90°")

        geometry = self._geometry.calculate(model)
        rectangle = geometry.flat_interface
        triangle = geometry.corner_interface
        parameters: dict[str, dict[str, Any]] = {
            "theta": {"type": "number", "value": model.theta, "min": 0, "max": _MAX_ANGLE, "unit": "deg"},
            "theta_advancing": {
                "type": "number", "value": model.theta_advancing, "min": 0,
                "max": _MAX_ANGLE, "unit": "deg",
            },
            "theta_receding": {
                "type": "number", "value": model.theta_receding, "min": 0,
                "max": _MAX_ANGLE, "unit": "deg",
            },
            "wetting.name": {"type": "string", "value": model.wetting_fluid.name},
            "wetting.color": {"type": "string", "value": model.wetting_fluid.color},
            "non_wetting.name": {"type": "string", "value": model.non_wetting_fluid.name},
            "non_wetting.color": {"type": "string", "value": model.non_wetting_fluid.color},
            "rock.name": {"type": "string", "value": model.rock.name},
        }
        values = {name: parameter["value"] for name, parameter in parameters.items()}
        bindings: list[dict[str, Any]] = []

        def bind(target: str, attribute: str, expression: dict[str, Any]) -> Any:
            bindings.append({
                "target": target,
                "attribute": attribute,
                "expression": expression,
            })
            return evaluate(expression, values)

        theta = _var("theta")
        advancing = _var("theta_advancing")
        receding = _var("theta_receding")
        degrees = lambda angle: _op("radians", angle)
        sin = lambda angle: _op("sin", degrees(angle))
        cos = lambda angle: _op("cos", degrees(angle))
        add = lambda left, right: _op("add", left, right)
        sub = lambda left, right: _op("sub", left, right)
        mul = lambda left, right: _op("mul", left, right)

        rect_contact = tuple(float(value) for value in rectangle.contact_point)
        rect_end = (8.45, 15.30)
        rect_control2 = (7.45, 14.45)
        rect_control1 = (
            add(_const(rect_contact[0]), mul(_const(2.10), cos(theta))),
            add(_const(rect_contact[1]), mul(_const(2.10), sin(theta))),
        )
        rect_interface = _path(
            ("M", (_const(rect_contact[0]), _const(rect_contact[1]))),
            ("C", (
                rect_control1[0], rect_control1[1],
                _const(rect_control2[0]), _const(rect_control2[1]),
                _const(rect_end[0]), _const(rect_end[1]),
            )),
        )
        rect_wetting = _path(
            ("M", (_const(rect_contact[0]), _const(rect_contact[1]))),
            ("C", (
                rect_control1[0], rect_control1[1],
                _const(rect_control2[0]), _const(rect_control2[1]),
                _const(rect_end[0]), _const(rect_end[1]),
            )),
            ("L", (_const(10.80), _const(15.30))),
            ("L", (_const(10.80), _const(11.00))),
            ("Z", ()),
        )
        rect_tangent_end = (
            add(_const(rect_contact[0]), mul(_const(2.70), cos(theta))),
            add(_const(rect_contact[1]), mul(_const(2.70), sin(theta))),
        )
        rect_tangent = _path(
            ("M", (_const(rect_contact[0]), _const(rect_contact[1]))),
            ("L", rect_tangent_end),
        )

        sector_radius = 1.20
        sector_start = (rect_contact[0] + sector_radius, rect_contact[1])
        sector_end = (
            add(_const(rect_contact[0]), mul(_const(sector_radius), cos(theta))),
            add(_const(rect_contact[1]), mul(_const(sector_radius), sin(theta))),
        )
        sector_path = _path(
            ("M", (_const(rect_contact[0]), _const(rect_contact[1]))),
            ("L", (_const(sector_start[0]), _const(sector_start[1]))),
            ("A", (
                _const(sector_radius), _const(sector_radius), _const(0), _const(0),
                _const(1), sector_end[0], sector_end[1],
            )),
            ("Z", ()),
        )
        sector_outline = _path(
            ("M", (_const(sector_start[0]), _const(sector_start[1]))),
            ("A", (
                _const(sector_radius), _const(sector_radius), _const(0), _const(0),
                _const(1), sector_end[0], sector_end[1],
            )),
        )

        corner = tuple(float(value) for value in triangle.corner)
        lower = tuple(float(value) for value in triangle.lower_contact)
        inclined = tuple(float(value) for value in triangle.inclined_contact)
        opening = math.radians(30)
        denominator = _op("cos", add(degrees(theta), _const(opening)))
        signed_radius = _op(
            "div",
            _const(float(lower[0] - corner[0]) * math.sin(math.radians(30))),
            denominator,
        )
        radius = _op("abs", signed_radius)
        linear_limit = _op("lt", _op("abs", denominator), _const(1e-9))
        sweep_qp = _op("if", _op("gt", denominator, _const(0)), _const(0), _const(1))
        sweep_pq = _op("if", _op("gt", denominator, _const(0)), _const(1), _const(0))
        meniscus_line = _path(
            ("M", (_const(lower[0]), _const(lower[1]))),
            ("A", (
                radius, radius, _const(0), _const(0), sweep_qp,
                _const(inclined[0]), _const(inclined[1]),
            )),
        )
        meniscus_straight = _path(
            ("M", (_const(lower[0]), _const(lower[1]))),
            ("L", (_const(inclined[0]), _const(inclined[1]))),
        )
        triangle_meniscus = _op("if", linear_limit, meniscus_straight, meniscus_line)
        wetting_arc = _path(
            ("M", (_const(corner[0]), _const(corner[1]))),
            ("L", (_const(inclined[0]), _const(inclined[1]))),
            ("A", (
                radius, radius, _const(0), _const(0), sweep_pq,
                _const(lower[0]), _const(lower[1]),
            )),
            ("Z", ()),
        )
        wetting_line = _path(
            ("M", (_const(corner[0]), _const(corner[1]))),
            ("L", (_const(inclined[0]), _const(inclined[1]))),
            ("L", (_const(lower[0]), _const(lower[1]))),
            ("Z", ()),
        )
        triangle_wetting = _op("if", linear_limit, wetting_line, wetting_arc)

        def direction_endpoint(angle: dict[str, Any], length: float) -> tuple[dict[str, Any], dict[str, Any]]:
            absolute_angle = sub(_const(180), angle)
            return (
                add(_const(lower[0]), mul(_const(length), cos(absolute_angle))),
                add(_const(lower[1]), mul(_const(length), sin(absolute_angle))),
            )

        def ray_path(angle: dict[str, Any], length: float) -> dict[str, Any]:
            return _path(
                ("M", (_const(lower[0]), _const(lower[1]))),
                ("L", direction_endpoint(angle, length)),
            )

        def angle_arc(angle: dict[str, Any], radius_value: float) -> dict[str, Any]:
            endpoint = direction_endpoint(angle, radius_value)
            return _path(
                ("M", (_const(lower[0] - radius_value), _const(lower[1]))),
                ("A", (
                    _const(radius_value), _const(radius_value), _const(0), _const(0),
                    _const(0), endpoint[0], endpoint[1],
                )),
            )

        dynamic_paths = {
            "rectangle-interface": rect_interface,
            "rectangle-wetting-region": rect_wetting,
            "rectangle-tangent": rect_tangent,
            "theta-sector": sector_path,
            "theta-sector-outline": sector_outline,
            "triangle-wetting-region": triangle_wetting,
            "triangle-meniscus": triangle_meniscus,
            "receding-angle-arc": angle_arc(receding, 0.88),
            "advancing-angle-arc": angle_arc(advancing, 1.27),
            "receding-ray": ray_path(receding, 2.05),
            "advancing-ray": ray_path(advancing, 2.35),
            "triangle-tangent": ray_path(theta, 2.0),
        }

        for target, expression in dynamic_paths.items():
            bind(target, "d", expression)
        for target in ("rectangle-non-wetting-region", "triangle-non-wetting-region"):
            bind(target, "fill", _var("non_wetting.color"))
        for target in ("rectangle-wetting-region", "triangle-wetting-region"):
            bind(target, "fill", _var("wetting.color"))

        label_expressions = {
            "theta-label": _op("concat", _const("θ = "), theta, _const("°")),
            "receding-label": _op("concat", _const("θᵣ = "), receding, _const("°")),
            "advancing-label": _op("concat", _const("θₐ = "), advancing, _const("°")),
            "rectangle-wetting-label": _var("wetting.name"),
            "rectangle-non-wetting-label": _var("non_wetting.name"),
            "triangle-wetting-label": _var("wetting.name"),
            "triangle-non-wetting-label": _var("non_wetting.name"),
            "rectangle-rock-label": _var("rock.name"),
            "triangle-rock-label": _var("rock.name"),
        }
        for target, expression in label_expressions.items():
            bind(target, "textContent", expression)

        def initial_path(target: str) -> str:
            value = next(
                binding["expression"] for binding in bindings
                if binding["target"] == target and binding["attribute"] == "d"
            )
            result = evaluate(value, values)
            if not isinstance(result, str):
                raise ValueError(f"SVG path binding {target} did not produce text")
            return result

        def initial_text(target: str) -> str:
            value = next(
                binding["expression"] for binding in bindings
                if binding["target"] == target and binding["attribute"] == "textContent"
            )
            result = evaluate(value, values)
            if not isinstance(result, str):
                raise ValueError(f"SVG text binding {target} did not produce text")
            return result

        nonwet_rectangle = _coordinates_path(rectangle.non_wetting_region)
        nonwet_triangle = _coordinates_path(triangle.non_wetting_region)
        rock_rectangle = _coordinates_path(rectangle.solid_boundary, close=False)
        rock_inclined = _coordinates_path(triangle.inclined_solid_boundary, close=False)
        rock_lower = _coordinates_path(triangle.lower_solid_boundary, close=False)

        drawing = [
            _element("path", {
                "id": "rectangle-non-wetting-region", "d": nonwet_rectangle,
                "fill": model.non_wetting_fluid.color,
            }),
            _element("path", {
                "id": "rectangle-wetting-region", "d": initial_path("rectangle-wetting-region"),
                "fill": model.wetting_fluid.color,
            }),
            _element("path", {
                "id": "rectangle-interface", "d": initial_path("rectangle-interface"),
                "fill": "none", "stroke": "rgba(255,255,255,0.65)",
                "stroke-width": _px(1.1),
            }),
            _element("path", {
                "id": "theta-sector", "d": initial_path("theta-sector"),
                "fill": "rgb(238,238,238)", "fill-opacity": "0.84",
            }),
            _element("path", {
                "id": "theta-sector-outline", "d": initial_path("theta-sector-outline"),
                "fill": "none", "stroke": "rgba(65,65,65,0.56)",
                "stroke-width": _px(1.4),
            }),
            _element("path", {
                "id": "rectangle-tangent", "d": initial_path("rectangle-tangent"),
                "fill": "none", "stroke": "#151515", "stroke-width": _px(4),
                "stroke-dasharray": f"{_px(8)} {_px(8)}",
            }),
            _element("path", {
                "id": "rectangle-rock", "d": rock_rectangle, "fill": "none",
                "stroke": "#171717", "stroke-width": _px(5),
            }),
            _element("path", {
                "id": "triangle-non-wetting-region", "d": nonwet_triangle,
                "fill": model.non_wetting_fluid.color,
            }),
            _element("path", {
                "id": "triangle-wetting-region", "d": initial_path("triangle-wetting-region"),
                "fill": model.wetting_fluid.color,
            }),
            _element("path", {
                "id": "triangle-meniscus", "d": initial_path("triangle-meniscus"),
                "fill": "none", "stroke": "rgba(255,255,255,0.8)",
                "stroke-width": _px(1.4),
            }),
            _element("path", {
                "id": "receding-angle-arc", "d": initial_path("receding-angle-arc"),
                "fill": "none", "stroke": "rgba(20,20,20,0.9)",
                "stroke-width": _px(2.1),
            }),
            _element("path", {
                "id": "advancing-angle-arc", "d": initial_path("advancing-angle-arc"),
                "fill": "none", "stroke": "rgba(20,20,20,0.9)",
                "stroke-width": _px(2.1),
            }),
            _element("path", {
                "id": "receding-ray", "d": initial_path("receding-ray"),
                "fill": "none", "stroke": "white", "stroke-width": _px(4.2),
                "stroke-dasharray": f"{_px(8)} {_px(8)}",
            }),
            _element("path", {
                "id": "advancing-ray", "d": initial_path("advancing-ray"),
                "fill": "none", "stroke": "white", "stroke-width": _px(4.2),
                "stroke-dasharray": f"{_px(8)} {_px(8)}",
            }),
            _element("path", {
                "id": "triangle-tangent", "d": initial_path("triangle-tangent"),
                "fill": "none", "stroke": "#151515", "stroke-width": _px(4),
                "stroke-dasharray": f"{_px(8)} {_px(8)}",
            }),
            _element("path", {
                "id": "triangle-inclined-rock", "d": rock_inclined, "fill": "none",
                "stroke": "#171717", "stroke-width": _px(6),
            }),
            _element("path", {
                "id": "triangle-lower-rock", "d": rock_lower, "fill": "none",
                "stroke": "#171717", "stroke-width": _px(6),
            }),
        ]

        def label(
            target: str,
            x: float,
            y: float,
            color: str,
            size_px: float,
            *,
            static_text: str | None = None,
        ) -> str:
            return _element("text", {
                "id": target,
                "x": _format_number(x),
                "y": _format_number(_Y_RANGE - y),
                "fill": color,
                "font-family": "Arial, sans-serif",
                "font-size": _px(size_px),
                "text-anchor": "middle",
                "dominant-baseline": "central",
            }, escape(initial_text(target) if static_text is None else static_text))

        labels = [
            label("rectangle-non-wetting-label", 3.25, 13.05, "white", 18),
            label("rectangle-wetting-label", 9.30, 13.05, "white", 17),
            label("theta-label", 8.05, 11.67, "#171717", 15),
            label("rectangle-rock-label", 6.0, 10.50, "#171717", 19),
            label("receding-label", 4.08, 3.17, "white", 15),
            label("advancing-label", 8.15, 3.15, "white", 15),
            label("triangle-wetting-label", 3.10, 1.81, "white", 16),
            label("triangle-non-wetting-label", 6.65, 6.24, "white", 17),
            label("triangle-rock-label", 6.0, 0.46, "#171717", 19),
            label("title-label", 6.0, 16.21, "#171717", 31, static_text="Interfaces"),
        ]
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{_WIDTH}" '
            f'height="{_HEIGHT}" viewBox="{_VIEWBOX}" '
            'preserveAspectRatio="xMidYMid meet">'
            '<title>Interfacial chart</title>'
            f'<rect id="background" x="-0.451" y="-0.228" width="12.902" '
            'height="17.456" fill="#ffffff"/>'
            '<g id="drawing" transform="translate(0 17) scale(1 -1)">'
            + "".join(drawing)
            + "</g>"
            + "".join(labels)
            + "</svg>"
        )
        return ParametricSvgDocument.from_dict({
            "format": "lmmp-parametric-svg",
            "version": "1.0.0",
            "svg": svg,
            "parameters": parameters,
            "bindings": bindings,
            "constraints": [
                {
                    "expression": _op("gt", theta, _const(0)),
                    "message": "theta must be positive",
                },
                {
                    "expression": _op("lt", theta, _const(90)),
                    "message": "theta must be below 90 degrees",
                },
                {
                    "expression": _op("lt", receding, theta),
                    "message": "theta_receding must be below theta",
                },
                {
                    "expression": _op("lt", theta, advancing),
                    "message": "theta must be below theta_advancing",
                },
                {
                    "expression": _op("lt", advancing, _const(90)),
                    "message": "theta_advancing must be below 90 degrees",
                },
            ],
        })


__all__ = ["InterfacialBuilder"]
