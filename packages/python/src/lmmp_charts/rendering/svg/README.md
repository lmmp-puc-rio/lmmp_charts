# Python SVG builder

`InterfacialBuilder.build(wettability)` returns a validated
`ParametricSvgDocument` containing the complete v5 interfacial diagram. Its
bindings update all three angles, both fluid names and colors, and the rock
label while preserving the approved geometry.

The builder uses `geometry/` and the `lmmp-parametric-svg` 1.0.0 contract.
The Plotly builder and `InterfacialChart.generate()` default are unchanged.

The output is not sanitized for browser DOM insertion. Do not pass its `svg`
string directly to `innerHTML`; the safe TypeScript SVG renderer remains
pending.
