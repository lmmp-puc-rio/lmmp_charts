# Continuidade do projeto no Codex/VS Code

## Objetivo

Desenvolver a biblioteca reutilizável `lmmp_charts` (Python e TypeScript), adotada inicialmente no PoreSIM (Django REST Framework, React + TypeScript, Tauri). A API Python define modelos, validação, geometria e os documentos gráficos; o frontend apresenta/atualiza os gráficos localmente.

## Resumo das decisões de arquitetura aprovadas

- `docs/`, `packages/python/`, `packages/typescript/`.
- Python `charts/` para a classe pública `InterfacialChart`; `rendering/plotly/interfacial_builder.py` para `InterfacialBuilder`, e futuramente `rendering/svg/interfacial_builder.py`.
- `geometry/Rectangle`, `geometry/Triangle` e `geometry/CurveGeometry` são genéricos; `geometry/InterfacialGeometry` compõe essas primitivas para calcular coordenadas sem depender de um formato de renderização.
- **Não utilizar `scene/`.** Abstrações comuns podem ser adicionadas mais tarde mediante necessidade comprovada e aprovação.
- Python `expressions/` e TypeScript `expressions/` avaliam a mesma gramática matemática declarativa, sem executar código recebido no JSON.
- Python `InterfacialChart.generate()` por padrão retorna figura Plotly.js `dict` (data, layout, config). Builders recebem resultados da geometria e geram a representação do formato escolhido.
- Preservar a geometria, os estilos, os traços, as anotações e a posição das fases aprovados.
- O diagrama usa molhabilidade medida **do lado do fluido molhante**, ângulos absolutos com a relação `0 <= theta_receding < theta < theta_advancing < 90` para renderização.
- SVG paramétrico: documento versionado `lmmp-parametric-svg/1.0.0`, atualizador genérico TypeScript sem fórmulas de menisco específicas.

## Estado exato na entrega

Implementado: modelos, geometria, gráfico Plotly de referência, façade `InterfacialChart`, avaliadores de expressões Python/TS, documento SVG paramétrico e cálculo de patches, `PlotlyRenderer` genérico TS, playground HTML local, `uv`/`pyproject.toml`.

Não implementado: geração em Python do gráfico interfacial SVG completo, sanitização/atualização do DOM SVG no TypeScript, wrappers React definitivos. Não afirmar que estão concluídos.

Versões: pacote Python e npm `0.4.0` (desenvolvimento, sem release); contrato SVG `1.0.0`.

## Começo recomendado no Codex

1. Abra a pasta **raiz deste repositório**, não `packages/python` isoladamente.
2. Leia `AGENTS.md`, `README.md`, `docs/architecture/decisions.md` e `docs/architecture/project_structure.md`.
3. Para publicar a base, siga `docs/development/github_setup.md`.
4. Execute os testes descritos em `docs/development/testing.md` antes de propor alterações.
5. Trabalhe nos builders por formato sem alterar a saída Plotly aprovada.
6. Solicite aprovação antes de grandes refatorações ou mudanças no contrato.

## Uso do histórico deste chat

Este arquivo registra decisões tecnicamente relevantes, mas **não contém o texto integral da conversa**. O Codex no VS Code não deve pressupor acesso automático ao histórico ou à memória do projeto ChatGPT. Quando necessário, forneça o link/texto da conversa ou uma síntese adicional no prompt. O conteúdo versionado do repositório é a referência prática mais confiável para continuidade.
