# @lmmp/charts — TypeScript

Módulo genérico independente de React para aplicações LMMP. Inclui:

1. `PlotlyRenderer`: exibe e atualiza figuras nativas Plotly.js (`data`, `layout`, `config`, `frames?`) recebidas do Python.
2. `validateParametricDocument` e `evaluateBindings`: usam `parametric/expressions` e `parametric/svg` para validar o contrato `lmmp-parametric-svg` e calcular atualizações (`patches`) de atributos SVG a partir dos parâmetros alterados.

O **renderizador SVG com manipulação segura do DOM** e o componente React **ainda não estão implementados**. Nunca insira `document.svg` diretamente no DOM sem sanitização; consulte `../../docs/specifications/parametric_svg.md`.

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

## SVG paramétrico: cálculo de patches

```ts
import { validateParametricDocument, evaluateBindings } from "@lmmp/charts";
const document = validateParametricDocument(svgContractJson);
const patches = evaluateBindings(document, { theta: 35 });
// patches: [{target, attribute, value}, ...]
// O controlador de DOM seguro será implementado na próxima etapa.
```
