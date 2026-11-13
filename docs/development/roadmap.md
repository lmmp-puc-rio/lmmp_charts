# Próximos incrementos

1. [x] Implementar `rendering/svg/interfacial_builder.py` no Python, gerando o SVG interfacial completo e bindings paramétricos para ângulos, cores e textos usando `lmmp-parametric-svg` v1.0.0; validar a paridade geométrica.
2. [x] Criar `packages/typescript/src/renderers/svg/SvgRenderer.ts`: analisar e sanitizar o SVG com allowlist, validar patches por atributo, aplicar atualização parcial/atômica e limitar a complexidade; nenhum `innerHTML` direto com conteúdo não validado.
3. Criar `packages/typescript/src/react/ParametricSvgChart.tsx` e, se necessário, `PlotlyChart.tsx`, mantendo o núcleo sem dependência de React.
4. Testar integração real no navegador/Tauri, perfis de latência e a equivalência com as geometrias aprovadas.
5. Registrar resultados no repositório e só avançar para novos gráficos após aprovação do escopo de cada incremento.

O contrato SVG agora também inclui renderização segura no DOM e um playground standalone. Wrappers React e testes de navegador automatizados continuam pendentes.
