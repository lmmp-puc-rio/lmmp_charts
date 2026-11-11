# LMMP Charts — Parametric SVG JSON Contract

**Contract**: `format: "lmmp-parametric-svg"`, `version: "1.0.0"`.

This is a **transport contract version**, independent of the `lmmp_charts`
**development version `0.4.0`**. This contract is integrated into the development repository but has not yet been released.

## Implemented scope

This increment implements (a) the same JSON expression evaluator in Python
and TypeScript, (b) a typed/validated parametric document, (c) calculation
of target SVG attribute patches and (d) a Python builder that generates the
complete v5 interfacial diagram with parametric angle, color, and text
bindings. It does **not** embed SVG in a browser or provide a React component.
Approved geometry / Plotly output is unchanged.

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
constraint fails, no patch list is returned. The future renderer should apply
all patches only after successful evaluation, atomically at one frame boundary.

## Deliberate security boundary

This stage NEVER evaluates arbitrary JavaScript or Python source; it accepts
only a fixed operation grammar and enforces complexity limits. But the
`svg` markup is currently only checked for type/size. **Do not inject it into
DOM via `innerHTML` yet**. The forthcoming SVG renderer MUST parse and
sanitize SVG with a strict element/attribute allowlist, reject scripts/event
handlers/foreign objects/external resources, and apply `textContent` as text.
Binding string values for CSS/paths will also require attribute-specific
validation before DOM application.

## Future work

1. Implement the generic SVG DOM controller with sanitization, differential
   updates, and `requestAnimationFrame` batching; no reload or HTTP per slider.
2. Add the React wrapper and cross-language/browser regression tests.

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
