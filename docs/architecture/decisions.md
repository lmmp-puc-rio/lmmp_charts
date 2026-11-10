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

## 2026-11-10 — organização da camada paramétrica por formato

1. Agrupar comportamento paramétrico sob `parametric/`, separado de `charts/` e `rendering/`.
2. Colocar o avaliador declarativo compartilhável em `parametric/expressions/`.
3. Colocar o contrato, validação e bindings específicos do SVG em `parametric/svg/`.
4. Reservar `parametric/plotly/` para bindings paramétricos Plotly futuros; não criar APIs/diretórios vazios nem afirmar que esse suporte está implementado.
5. Manter `rendering/<technology>/` como responsabilidade Python para produzir a representação inicial; `renderers/<technology>/` TypeScript exibe e atualiza no navegador.
6. Manter `types/` TypeScript como localização dos tipos de transporte. O avaliador atual inclui construção de SVG path; esse comportamento permanece parte do contrato SVG atual e não representa, por si só, suporte paramétrico Plotly.
7. Não mudar o contrato `lmmp-parametric-svg` v1.0.0, a geometria ou a aparência aprovada do gráfico Plotly.

**Status:** organização de diretórios aprovada; integração paramétrica Plotly, geração do SVG interfacial e renderizador SVG seguro permanecem planejados.
