# Standalone interfacial SVG playground

This playground connects the Python `Wettability` model and
`InterfacialBuilder` to the browser `SvgRenderer`. Python creates the
`lmmp-parametric-svg` document; the TypeScript renderer validates and
sanitizes its SVG markup, then applies parameter bindings in the browser.
Angle, label, and color edits use the shared expression evaluator and do not
send a request or duplicate scientific formulas.

From the repository root, build TypeScript and run the local server:

```bash
cd packages/typescript
npm test
cd ../..
PYTHONPATH=packages/python/src python examples/standalone/interfacial_svg_playground/server.py
```

Open <http://127.0.0.1:8766>. The server only binds to localhost. The
**Gerar documento SVG** button submits edited JSON to Python; individual
parameter controls update the mounted SVG locally. No external CDN or React
integration is used.
