# Testes e validação

Execute a partir da raiz, salvo indicação contrária:

```bash
PYTHONPATH=packages/python/src python -m unittest discover -s tests/python -p 'test_*.py' -v
PYTHONPATH=packages/python/src python -m unittest discover -s examples/standalone/interfacial_playground -p 'test_*.py' -v
(cd packages/typescript && npm test)
(cd packages/python && uv build)
```

Também é importante comparar `tests/python/fixtures/v5_plotly_reference.json` e a referência geométrica `tests/python/v5_geometry_reference.npz`; nenhuma modificação visual foi autorizada.

O TypeScript requer Node.js e o compilador TypeScript; `npm install` instala as dependências de desenvolvimento. Os resultados registrados em `integration_report_previous.md` correspondem à estrutura **anterior**; a validação desta reorganização deve ser registrada separadamente.
