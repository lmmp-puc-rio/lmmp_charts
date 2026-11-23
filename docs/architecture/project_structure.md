# Estrutura de pastas e responsabilidades

Aprovada em 2026-11-05. Não há camada intermediária `scene/`.

```text
lmmp_charts/
├── .gitignore
├── AGENTS.md               # Instruções persistentes para Codex no repositório
├── README.md
├── docs/
│   ├── architecture/       # Estrutura e decisões
│   ├── specifications/     # Contratos de dados e representações
│   └── development/        # Continuidade, testes e etapas seguintes
├── packages/
│   ├── python/
│   │   ├── pyproject.toml   # Build do pacote lmmp-charts com uv
│   │   └── src/lmmp_charts/
│   │       ├── models/      # Modelos e validações de entrada
│   │       ├── geometry/    # Formas genéricas e geometria de domínio
│   │       │   ├── curves.py      # Operações matemáticas para curvas
│   │       │   ├── rectangle.py   # Primitiva Rectangle
│   │       │   ├── triangle.py    # Primitiva Triangle
│   │       │   └── interfacial.py # Cálculo de regiões e meniscos
│   │       ├── charts/      # Facades públicas: interfacial_chart.py
│   │       ├── expressions/ # Avaliador e contrato matemático declarativo
│   │       └── rendering/  # Geração de representações gráficas Python
│   │           ├── plotly/  # interfacial_builder.py e primitivas específicas
│   │           └── svg/     # Builder SVG paramétrico PLANEJADO
│   └── typescript/
│       ├── package.json    # Pacote npm @lmmp/charts
│       └── src/
│           ├── types/      # Contratos TypeScript
│           ├── expressions/# Avaliador declarativo de expressões
│           ├── parametric/ # Validação e avaliação de bindings SVG
│           ├── renderers/  # Exibição/atualização gráfica no browser
│           │   ├── plotly/  # Implementado
│           │   └── svg/     # Controle do DOM seguro PLANEJADO
│           └── react/      # Componentes wrappers PLANEJADOS
├── tests/                  # Testes Python e de integração, com fixtures de referência
└── examples/               # Playground, Django/React previstos, fixtures
```

## Fluxos

Python: `models` -> `geometry/InterfacialGeometry` -> `charts` / `rendering/<technology>/InterfacialBuilder` -> representação gráfica.

`geometry/Rectangle`, `geometry/Triangle` e `geometry/CurveGeometry` são componentes geométricos sem conhecimento de gráficos específicos. `geometry/InterfacialGeometry` compõe essas primitivas para calcular as regiões e curvas do domínio interfacial. Os builders convertem as coordenadas resultantes para Plotly, SVG ou outros formatos.

SVG (planejado): `models` -> `charts` + `geometry` + `expressions` -> `rendering/svg` -> `ParametricSvgDocument` -> TypeScript `expressions` + `parametric` + `renderers/svg` -> React.

## Design dos Builders

- `charts/interfacial_chart.py` define `InterfacialChart`, interface pública e coordenação.
- `rendering/plotly/interfacial_builder.py` define `InterfacialBuilder`, especialista em construir as representações Plotly usando a geometria compartilhada.
- `rendering/svg/interfacial_builder.py` terá futuramente outro `InterfacialBuilder` no namespace SVG. A duplicidade de nomes simples em namespaces diferentes é intencional, não é duplicidade de geometria.
- Primitivas compartilhadas são preferíveis quando úteis. Não introduzir `scene/` sem decisão explícita.
