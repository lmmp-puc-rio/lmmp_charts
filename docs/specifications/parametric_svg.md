# LMMP Charts — Parametric SVG JSON Contract

**Contract**: `format: "lmmp-parametric-svg"`, `version: "1.0.0"`.

This is a **transport contract version**, independent of the `lmmp_charts`
**development version `0.4.0`**. This contract is integrated into the development repository but has not yet been released.

## Implemented scope

The implementation includes (a) the same JSON expression evaluator in Python
and TypeScript, (b) a typed/validated parametric document, (c) calculation
of target SVG attribute patches, (d) a Python builder that generates the
complete interfacial diagram and (e) a TypeScript `SvgRenderer` that parses,
sanitizes and updates the SVG in the browser. A standalone local playground
connects the builder and renderer. There is no React component. Approved
geometry / Plotly output is unchanged.

The shared evaluator lives under `parametric/expressions/`; the SVG-specific
document contract and bindings live under `parametric/svg/` in both language
packages. The current evaluator includes SVG path construction for this
contract. Parametric Plotly bindings and updates are not implemented.

## Top-level shape

```json
{
  "format": "lmmp-parametric-svg",
  "version": "1.0.0",
  "svg": "<svg ...>...</svg>",
  "parameters": {
    "theta": {"type": "number", "value": 45, "min": 0, "max": 89, "unit": "deg"},
    "wetting.color": {"type": "string", "value": "#4472C4"}
  },
  "bindings": [
    {"target": "tangent", "attribute": "x2", "expression": {"var": "theta"}}
  ],
  "constraints": [
    {"expression": {"op": "gt", "args": [{"var": "theta"}, {"const": 0}]},
     "message": "theta must be positive"}
  ]
}
```

The example above only demonstrates transport structure. For a complete,
working contract containing actual trig equations, inspect
`tests/integration/fixtures/parametric_contract.json`.

## Expression grammar

* `{"const": number|string|boolean}` — literal scalar
* `{"var": "parameter.name"}` — named parameter, flat key lookup
* `{"op": "...", "args": [ ... ]}` — whitelisted operation
* `{"op": "path", "commands": [{"cmd": "M", "values": [..,..]}, ...]}` —
  SVG path string generation using `M`, `L`, `C`, `Q`, `A`, and `Z`.

Supported operators:

| Group | Operators |
|---|---|
| Arithmetic | `add`, `sub`, `mul`, `div`, `pow`, `neg`, `abs`, `sqrt`, `min`, `max` |
| Trigonometry | `sin`, `cos`, `tan`, `atan2`, `radians`, `degrees` |
| Comparison | `lt`, `lte`, `gt`, `gte`, `eq`, `ne` |
| Control | `if` (lazy), `concat` |

Numbers must be finite; trigonometric input is in **radians** unless converted
using `radians`. `if` is lazily evaluated but the entire expression is
validated. SVG path numbers are rounded to six decimal places in either
runtime. Python and TypeScript numerical floating-point results can differ
slightly; test parity uses numerical tolerance for numbers and exact values for
text/path strings in the included fixtures.

### Binding semantics

* `target` is the ID of an existing SVG element.
* `attribute` is a restricted allowlist: `d`, `transform`, `fill`, `stroke`,
  `stroke-width`, `stroke-dasharray`, `opacity`, `x`, `y`, `x1`, `y1`, `x2`, `y2`,
  `cx`, `cy`, `r`, `rx`, `ry`, `points`, `textContent`.
* `expression` returns a compatible scalar or path string.
* Python `ParametricSvgDocument.evaluate_bindings(overrides)` and TS
  `evaluateBindings(document, overrides)` compute the same list of patches:

```json
[
  {"target": "theta-label", "attribute": "textContent", "value": "θ = 45°"},
  {"target": "wetting-region", "attribute": "fill", "value": "#4472C4"}
]
```

`constraints` allow **cross-parameter rules**, e.g. θᵣ < θ < θₐ. When any
constraint fails, no patch list is returned. `SvgRenderer.update()` evaluates
and validates the complete patch list before changing any node; the DOM
mutations run synchronously in one task before the browser paints.

## Deliberate security boundary

The evaluator NEVER runs arbitrary JavaScript or Python source; it accepts
only a fixed operation grammar and enforces complexity limits. The document
validator checks the transport shape, not whether its markup is safe. Browser
rendering must use `SvgRenderer`, which recreates only allowlisted SVG
elements and attributes, rejects namespaced attributes, event handlers,
scripts, foreign content and external-resource attributes, and applies
`textContent` as text. Binding values are validated according to their target
attribute before any DOM mutation. Never insert `document.svg` directly with
`innerHTML`.

The renderer currently supports `svg`, `title`, `desc`, `g`, `rect`, `path`,
`text`, `circle`, `ellipse`, `line`, `polyline` and `polygon`, with narrowly
allowlisted attributes and numeric/path complexity limits. This is a safe
subset for the current builder, not a general-purpose SVG sanitizer.

## Future work

1. Add broader automated browser and cross-language consistency tests for the
   sanitizer and renderer.
2. Add the React wrapper.

## Running tests

From the repository root:

```bash
PYTHONPATH=packages/python/src python -m unittest discover -s tests/python -p 'test_*.py' -v
cd packages/typescript
npm install --ignore-scripts
npm test
```

`npm install` supplies the TypeScript compiler in ordinary development
systems. No Plotly runtime is needed to evaluate these parametric expressions.
