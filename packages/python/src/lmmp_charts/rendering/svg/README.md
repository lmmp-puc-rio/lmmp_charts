# SVG generation — planned

The Python builder that generates the complete parametric interfacial SVG is **not implemented yet**.

A future `interfacial_builder.py` should expose an `InterfacialBuilder`, shared only by the `svg` namespace, and use `parametric/svg` contracts and `geometry/` without a new `scene/` abstraction.

Do not insert the current `ParametricSvgDocument.svg` string directly into the browser DOM: the secure renderer and sanitization are pending.
