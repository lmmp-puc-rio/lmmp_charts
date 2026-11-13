# Python SVG builder

`InterfacialBuilder.build(wettability)` returns a validated
`ParametricSvgDocument` containing the complete interfacial diagram. Its
bindings update all three angles, both fluid names and colors, and the rock
label while preserving the approved geometry.

The builder uses `geometry/` and the `lmmp-parametric-svg` 1.0.0 contract.
The Plotly builder and `InterfacialChart.generate()` default are unchanged.

The output is transport data, not markup for direct DOM insertion. Do not pass
its `svg` string to `innerHTML`; browser rendering must go through the
TypeScript `SvgRenderer`, which parses and recreates only allowlisted SVG nodes.
