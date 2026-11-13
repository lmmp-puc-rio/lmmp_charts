# Decisões arquiteturais aprovadas

## 2026-11-05 — estrutura para GitHub e Codex

1. Documentação em Markdown centralizada na raiz `docs/`.
2. Pares de pacotes por linguagem: `packages/python/` e `packages/typescript/` (o nome publicado npm continua `@lmmp/charts`).
3. No Python, renomear `backends/` para **`rendering/`**. Essa camada converte geometria e parâmetros nos formatos gráficos escolhidos; não é o backend servidor da aplicação.
4. Padronizar a classe pública em `charts/interfacial_chart.py`: **`InterfacialChart`**.
5. Padronizar os construtores específicos da tecnologia em `rendering/<technology>/interfacial_builder.py`: **`InterfacialBuilder`**. Classe antiga `InterfacialPlotlyBuilder` mantida apenas como alias de compatibilidade no novo módulo.
6. **Não criar `scene/`**. A divisão Chart + Builder é suficiente no momento; futura abstração exige motivação concreta e nova aprovação.
7. Manter geometria e visual interfacial v5 intactos e preservar a saída padrão Plotly da API pública.

## Decisões anteriores preservadas

- `uv` + `pyproject.toml` para pacote Python `lmmp-charts`, versão de desenvolvimento `0.4.0`.
- `numpy` e `plotly` como dependências diretas obrigatórias; `kaleido` opcional para exportação de imagens estáticas.
- Backend Python de figuras interfaciais Plotly + interpretador de expressões do SVG paramétrico Python/TypeScript.
- O TypeScript deve ser genérico: recebe documentos da API, calcula bindings e atualiza os elementos da GUI sem lógica científica específica da rocha/fluido.
- O SVG interativo completo usará expressões declarativas seguras (não scripts arbitrários embutidos).
- Para o gráfico de contato, o referencial de todos os ângulos é o lado molhante em relação à rocha, com `0 <= theta_receding < theta < theta_advancing < 90`.
- A v5 visual de referência do gráfico interfacial é imutável até aprovação específica para ajustes.

**Status:** reorganização aprovada e incorporada, não constitui release ou tag Git.
