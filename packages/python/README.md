# lmmp-charts — pacote Python

Módulo de modelos, geometria e gráficos para aplicações LMMP. O núcleo de modelos e geometria é independente do backend gráfico; a implementação atual utiliza Plotly.

## Instalação de desenvolvimento

A partir da pasta que contém `packages/`:

```bash
uv pip install --editable ./packages/python
```

Ou, a partir de um projeto gerenciado pelo uv:

```bash
uv add --editable /caminho/para/lmmp_charts/packages/python
```

Para exportação de imagens com Kaleido, instale o extra opcional `image` e verifique os requisitos de navegador do Kaleido instalado:

```bash
uv pip install --editable './packages/python[image]'
```

## Utilização

```python
from lmmp_charts import InterfacialChart, Wettability

config = Wettability.from_json_file("../../examples/interface_config.json")
chart = InterfacialChart(config)
payload = chart.generate()  # dict: data/layout/config
# chart.show()             # opcional, usando renderer Python
```

## Build

```bash
cd packages/python
uv build
```

Este pacote está identificado como versão de desenvolvimento `0.4.0`; não há release publicada.
