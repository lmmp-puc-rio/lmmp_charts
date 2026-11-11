# lmmp_charts

**Versão de desenvolvimento:** `0.4.0` — ainda sem release ou tag Git.

Biblioteca de gráficos científicos LMMP, com API de geração em Python e interpretação/apresentação no navegador em TypeScript. Estrutura aprovada: `charts/` + `rendering/<technology>/interfacial_builder.py`, **sem `scene/`**.

## Pacotes

- [`packages/python`](packages/python): `models`, `geometry`, `charts`, `parametric/expressions`, `parametric/svg`, `rendering/plotly` e o builder SVG paramétrico em `rendering/svg`. A classe pública é `InterfacialChart`.
- [`packages/typescript`](packages/typescript): `PlotlyRenderer` sem dependência de React e avaliação do contrato SVG paramétrico (`parametric/expressions` + `parametric/svg`). Bindings paramétricos Plotly, controlador DOM SVG e wrapper React ainda estão pendentes. Nome npm: `@lmmp/charts`.
- [`docs`](docs): arquitetura, decisões, contrato SVG, relatório e instruções de continuidade para Codex/VS Code.

## Python — desenvolvimento

```bash
uv pip install --editable ./packages/python
# ou, em um projeto gerenciado pelo uv:
uv add --editable /caminho/para/lmmp_charts/packages/python

PYTHONPATH=packages/python/src python -m unittest discover -s tests/python -p 'test_*.py'

cd packages/python && uv build
```

```python
from lmmp_charts import InterfacialChart, Wettability
model = Wettability.from_json_file('examples/interface_config.json')
payload = InterfacialChart(model).generate()  # dict Plotly data/layout/config
```

`kaleido` é dependência opcional para exportações estáticas (`.[image]`); Chrome/Chromium pode ser necessário.

## TypeScript — desenvolvimento

```bash
cd packages/typescript
npm install
npm test
```

```typescript
import { PlotlyRenderer, validateParametricDocument, evaluateBindings } from '@lmmp/charts';
// Injete a instância Plotly.js no construtor; sem CDN obrigatória.
```

## Playground local

```bash
PYTHONPATH=packages/python/src python examples/standalone/interfacial_playground/server.py
```

Acesse `http://127.0.0.1:8765`. O JavaScript Plotly usado no exemplo é fornecido localmente.

## Documentação e continuidade no Codex

Leia primeiro [`AGENTS.md`](AGENTS.md) e [`docs/development/codex_handoff.md`](docs/development/codex_handoff.md).

- [Arquitetura e pastas](docs/architecture/project_structure.md)
- [Decisões aprovadas](docs/architecture/decisions.md)
- [Contrato SVG paramétrico v1.0.0](docs/specifications/parametric_svg.md)
- [Próximas etapas](docs/development/roadmap.md)
- [Comandos de testes](docs/development/testing.md)
- [Publicar no GitHub e abrir no Codex](docs/development/github_setup.md)
- [Validação da reorganização](docs/development/validation_2026-11-05.md)
- [Relatório anterior de integração](docs/development/integration_report_previous.md)

**Limites atuais:** o builder Python gera o SVG interfacial completo e seus bindings paramétricos, mas o markup não é sanitizado para inserção direta no DOM. O renderizador SVG seguro no browser e os componentes React ainda não foram implementados. Não alterar a geometria ou aparência da referência visual v5 sem aprovação explícita.
