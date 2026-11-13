# LMMP Charts v0.4.0 — Relatório de integração

Status: integração dos componentes aprovados, **sem release/tag Git**.

## Escopo

- Empacotamento Python com `uv_build` via `packages/python/pyproject.toml`.
- Camada Python de expressões declarativas e contrato `ParametricSvgDocument`.
- Camada TypeScript equivalente: expressões, validação do contrato e cálculo de patches.
- Renderizador Plotly.js genérico (`PlotlyRenderer`) mantendo a injeção da instância Plotly.js.
- Preservados: `models`, `geometry`, `backends/plotly`, `charts/InterfacialChart` e desenhos visuais de referência v5.

## Execução e resultados

| Verificação | Resultado |
|---|---|
| Python: `PYTHONPATH=packages/python/src python -m unittest discover -s tests/python -p 'test_*.py' -v` | **114/114 aprovados** |
| TypeScript: `npm test` em `packages/renderer` | **39/39 aprovados**; inclui compilação `tsc` |
| Playground: `PYTHONPATH=packages/python/src python -m unittest discover -s examples/standalone/interfacial_playground -p 'test_*.py' -v` | **9/9 aprovados** |
| Build Python: `uv build --offline` | **Aprovado**; wheel e sdist gerados |
| Conteúdo do wheel | Inclui `lmmp_charts/expressions/` e o restante do pacote |

**Total de testes unitários/integrados executados: 162, sem falhas.**

### Arquivos de log

Os logs desta execução foram disponibilizados junto ao ZIP de artefatos de teste, ou individualmente em `/mnt/data/`:

- `lmmp_charts_integrated_python_tests.log`
- `lmmp_charts_integrated_renderer_tests.log`
- `lmmp_charts_integrated_playground_tests.log`
- `lmmp_charts_integrated_uv_build.log`

## Limites funcionais

O contrato SVG paramétrico **não é ainda o SVG interfacial completo aprovado na versão 5**. Ele calcula patches de atributos e é acompanhado de fixture de exemplo. Ainda faltam o backend Python que produz o SVG interfacial parametrizado, o controlador TypeScript com sanitização do SVG e o componente React.

O documento SVG fornecido ao interpretador é validado estruturalmente, mas não é sanitizado para inserção no navegador. **Não inserir SVG arbitrário no DOM diretamente.**

## Versionamento

- Biblioteca Python: `0.4.0` (versão de desenvolvimento).
- Pacote TypeScript: `0.4.0` (versão de desenvolvimento).
- Contrato JSON paramétrico: `1.0.0` (versão independente do contrato).
