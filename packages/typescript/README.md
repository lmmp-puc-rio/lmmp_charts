# @lmmp/charts — TypeScript

Módulo genérico independente de React para aplicações LMMP. Inclui
`validateParametricDocument` e `evaluateBindings`, que usam
`parametric/expressions` e `parametric/svg` para validar o contrato
`lmmp-parametric-svg` e calcular atualizações (`patches`) de atributos SVG a
partir dos parâmetros alterados.

O **renderizador SVG com manipulação segura do DOM** e o componente React **ainda não estão implementados**. Nunca insira `document.svg` diretamente no DOM sem sanitização; consulte `../../docs/specifications/parametric_svg.md`.

O renderer Plotly e as atualizações paramétricas de Plotly ainda não estão
implementados.

## Desenvolvimento

```bash
npm install
npm run build
npm test
```

## SVG paramétrico: cálculo de patches

```ts
import { validateParametricDocument, evaluateBindings } from "@lmmp/charts";
const document = validateParametricDocument(svgContractJson);
const patches = evaluateBindings(document, { theta: 35 });
// patches: [{target, attribute, value}, ...]
// O controlador de DOM seguro será implementado na próxima etapa.
```
