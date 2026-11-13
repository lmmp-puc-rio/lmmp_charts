# Estrutura de pastas e responsabilidades

Arquitetura aprovada em 2026-11-10; sem camada intermediária `scene/`.
Pastas marcadas como planejadas descrevem destinos futuros e não implicam APIs implementadas.

```text
lmmp_charts/
├── docs/
│   ├── architecture/       # Estrutura e decisões
│   ├── specifications/     # Contratos de dados e representações
│   └── development/        # Continuidade, testes e etapas seguintes
├── packages/
│   ├── python/
│   │   ├── pyproject.toml   # Build do pacote lmmp-charts com uv
│   │   └── src/lmmp_charts/
│   │       ├── models/      # Modelos e validações de domínio
│   │       ├── geometry/    # Geometria científica independente de renderizador
│   │       │   ├── curves.py      # Operações matemáticas para curvas
│   │       │   ├── rectangle.py   # Primitiva Rectangle
│   │       │   ├── triangle.py    # Primitiva Triangle
│   │       │   └── interfacial.py # Cálculo de regiões e meniscos
│   │       ├── charts/      # API pública e coordenação, ex.: InterfacialChart
│   │       ├── parametric/
│   │       │   ├── expressions/ # Avaliação declarativa compartilhável
│   │       │   ├── svg/         # Documento, validação e bindings SVG
│   │       │   └── plotly/      # Bindings paramétricos PLANEJADOS
│   │       └── rendering/
│   │           ├── plotly/
│   │           │   ├── interfacial_builder.py # Composição da figura Plotly
│   │           │   ├── flat_interface.py      # Interface plana
│   │           │   └── corner_interface.py     # Interface no canto
│   │           └── svg/     # Builder SVG interfacial paramétrico
│   └── typescript/
│       ├── package.json    # Pacote npm @lmmp/charts
│       └── src/
│           ├── types/      # Tipos dos contratos e payloads
│           ├── parametric/
│           │   ├── expressions/ # Avaliador equivalente ao Python
│           │   ├── svg/         # Validação e cálculo de patches SVG
│           │   └── plotly/      # Interpretação paramétrica PLANEJADA
│           ├── renderers/
│           │   ├── plotly/  # Exibição/atualização com Plotly.js
│           │   └── svg/     # Sanitização e atualização SVG segura
│           └── react/      # Wrappers React PLANEJADOS
├── tests/
│   ├── python/              # Testes unitários da biblioteca Python
│   ├── integration/         # Fixtures de paridade entre linguagens
│   └── renderer/            # Testes de integração/browser
└── examples/                # Exemplos e playground local
```

## Responsabilidades e fluxos

- `models/` valida configurações científicas; `geometry/` calcula coordenadas sem dependência de renderizador.
- `charts/` expõe a API pública e coordena as partes do gráfico sem absorver as implementações específicas de tecnologia.
- Em Python, `rendering/<technology>/` produz a representação inicial. O fluxo Plotly implementado é `models` + `geometry` -> `charts/InterfacialChart` -> `rendering/plotly` -> payload Plotly.
- `geometry/Rectangle`, `geometry/Triangle` e `geometry/CurveGeometry` são componentes geométricos sem conhecimento de gráficos específicos. `geometry/InterfacialGeometry` compõe essas primitivas para calcular as regiões e curvas interfaciais.
- `rendering/svg/InterfacialBuilder` usa `InterfacialGeometry` para gerar o SVG paramétrico completo como `ParametricSvgDocument`, com bindings para ângulos, cores e textos. Ele não sanitiza markup para inserção no DOM.
- `parametric/expressions/` avalia a gramática declarativa. O módulo atual também inclui construção de SVG path usada pelo contrato SVG; não há ainda consumidor paramétrico Plotly.
- `parametric/svg/` contém o documento versionado `lmmp-parametric-svg` e calcula patches SVG; isso não sanitiza nem insere markup no DOM.
- `parametric/plotly/` é reservado para definir como valores/bindings paramétricos se relacionarão a `data`/`layout` Plotly. Continua planejado até haver contrato aprovado e implementação.
- `renderers/svg/SvgRenderer` recria no DOM somente elementos e atributos allowlisted, valida os patches e aplica atualizações sem duplicar fórmulas científicas específicas. Não insira diretamente o markup transportado no DOM.
- No TypeScript, `renderers/<technology>/` exibe/atualiza no navegador; não duplica fórmulas científicas específicas.

## Design dos Builders

- `charts/interfacial_chart.py` define `InterfacialChart`, interface pública e coordenação.
- `rendering/plotly/interfacial_builder.py` define `InterfacialBuilder`, que constrói a representação Plotly usando a geometria compartilhada.
- Os renderers Plotly ficam em módulos nomeados pelo componente físico representado (`flat_interface.py` e `corner_interface.py`), não pelas primitivas geométricas usadas no cálculo.
- `rendering/svg/interfacial_builder.py` define um `InterfacialBuilder` separado no namespace SVG; ele produz um documento paramétrico sem alterar a saída Plotly padrão.
- Primitivas compartilhadas são preferíveis quando úteis. Não introduzir `scene/` sem decisão explícita.
