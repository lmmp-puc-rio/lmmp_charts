# @lmmp/charts — TypeScript

Módulo genérico independente de React para aplicações LMMP. Inclui:

1. `PlotlyRenderer`: exibe e atualiza figuras nativas Plotly.js (`data`, `layout`, `config`, `frames?`) recebidas do Python.
2. `SvgRenderer`: valida o contrato `lmmp-parametric-svg`, constrói SVG seguro a partir de uma allowlist e aplica bindings calculados por `parametric/expressions` e `parametric/svg`.

O SVG do contrato é texto de transporte não confiável: não o insira diretamente no DOM. `SvgRenderer.mount(container, input)` usa `DOMParser` apenas para analisar o XML, cria novos nós SVG validados e nunca usa `innerHTML`. `update(overrides)` avalia e valida todos os patches antes de atualizar o DOM; valores `textContent` são aplicados como texto. O componente React ainda não está implementado; consulte `../../docs/specifications/parametric_svg.md` para a allowlist suportada e os limites.

Atualizações paramétricas de Plotly ainda não estão implementadas; `PlotlyRenderer.update` recebe uma figura completa.

## Desenvolvimento

```bash
npm install
npm run build
npm test
```

A aplicação cliente deve fornecer sua instância Plotly.js. O pacote não usa CDN.

## Plotly.js

```ts
import Plotly from "plotly.js-dist-min";
import { PlotlyRenderer } from "@lmmp/charts";
const renderer = new PlotlyRenderer(Plotly);
const figure = await response.json();
await renderer.render("chart", figure);
await renderer.update("chart", figure);
renderer.destroy("chart");
```

## SVG paramétrico

```ts
import { SvgRenderer } from "@lmmp/charts";
const renderer = new SvgRenderer();
renderer.mount(document.querySelector("#chart")!, svgContractJson);
renderer.update({ theta: 35 });
renderer.destroy();
```
