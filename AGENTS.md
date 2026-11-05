# lmmp_charts — diretrizes do repositório para Codex

Leia `docs/development/codex_handoff.md`, `docs/architecture/decisions.md` e `docs/architecture/project_structure.md` antes de alterar a arquitetura.

## Decisões aprovadas (2026-11-05)
- Raiz `docs/` para documentação em Markdown.
- Pacotes irmãos `packages/python/` e `packages/typescript/`.
- Em Python, `charts/` expõe as classes públicas (ex.: `InterfacialChart`); `rendering/` reúne implementações gráficas (ex.: `rendering/plotly/interfacial_builder.py` com `InterfacialBuilder`).
- **Não adicionar camada `scene/`**. Manter o padrão Chart + Builder por tecnologia.
- Não confundir `rendering/` Python (produz representação) com `renderers/` TypeScript (exibe/atualiza no navegador).
- Versão de desenvolvimento 0.4.0, sem afirmar release/tag. Contrato JSON `lmmp-parametric-svg` v1.0.0, versionamento próprio.

## Qualidade e escopo
- Preserve a geometria e a aparência da referência interfacial v5. O modelo `Wettability` usa os três ângulos absolutos medidos do lado molhante; o gráfico requer 0 <= theta_receding < theta < theta_advancing < 90 graus.
- Python é responsável por modelos, validação, geometria e geração de saída; o TypeScript é responsável por interpretar/atualizar o gráfico no frontend sem duplicar fórmulas científicas específicas.
- O contrato SVG paramétrico é implementado nos avaliadores de Python/TS; **o SVG interfacial completo, a sanitização/atualização DOM e o wrapper React continuam pendentes**. Não afirmar que existem nem executar strings SVG não sanitizadas.
- Sem código arbitrário (`eval`, `Function`) em expressões. Manter operações e atributos numa allowlist e adicionar limites de complexidade.
- Mantenha compatibilidade de `from lmmp_charts import InterfacialChart, Wettability` e `InterfacialChart.generate()` retornando JSON Plotly por padrão.
- Não fazer migrações de arquitetura ou alterações visuais grandes sem aprovação explícita.

## Testes
- Python: `PYTHONPATH=packages/python/src python -m unittest discover -s tests/python -p 'test_*.py' -v`
- Playground: `PYTHONPATH=packages/python/src python -m unittest discover -s examples/standalone/interfacial_playground -p 'test_*.py' -v`
- TypeScript: `cd packages/typescript && npm test`
- Python build: `cd packages/python && uv build` (pode ser `uv build --offline` com cache disponível).

Registre decisões novas em `docs/architecture/decisions.md` após aprovação e preserve os testes de equivalência v5/entre linguagens.
