import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { PlotlyRenderer, parseFigure } from '../dist/index.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const samplePath = path.resolve(here, '../../../examples/output_plotly.json');
const reference = JSON.parse(fs.readFileSync(samplePath, 'utf8'));

function mockPlotly() {
  const calls = [];
  return {
    calls,
    newPlot: async (element, value) => { calls.push(['newPlot', element, value]); },
    react: async (element, value) => { calls.push(['react', element, value]); },
    purge: element => { calls.push(['purge', element]); },
    Plots: { resize: async element => { calls.push(['resize', element]); } }
  };
}

test('accepts the exact Plotly JSON returned by InterfacialChart', () => {
  const normalized = parseFigure(reference);
  assert.strictEqual(normalized, reference);
  assert.ok(reference.data.length > 0);
  assert.ok(reference.layout && reference.config);
});

test('accepts JSON strings without rewriting the figure', () => {
  const normalized = parseFigure(JSON.stringify(reference));
  assert.deepEqual(normalized, reference);
});

test('render passes the entire figure to newPlot', async () => {
  const engine = mockPlotly();
  await new PlotlyRenderer(engine).render('plot', reference);
  assert.equal(engine.calls[0][0], 'newPlot');
  assert.strictEqual(engine.calls[0][2], reference);
});

test('update passes the figure to react', async () => {
  const engine = mockPlotly();
  await new PlotlyRenderer(engine).update('plot', JSON.stringify(reference));
  assert.equal(engine.calls[0][0], 'react');
  assert.deepEqual(engine.calls[0][2], reference);
});

test('resizes and destroys via Plotly API', async () => {
  const engine = mockPlotly();
  const renderer = new PlotlyRenderer(engine);
  await renderer.resize('plot');
  renderer.destroy('plot');
  assert.deepEqual(engine.calls.map(c => c[0]), ['resize', 'purge']);
});

test('rejects malformed JSON input', () => {
  assert.throws(() => parseFigure('{ broken'), SyntaxError);
});

test('rejects figures lacking trace arrays', () => {
  assert.throws(() => parseFigure({ data: {} }), TypeError);
  assert.throws(() => parseFigure({ data: ['invalid'] }), TypeError);
  assert.throws(() => parseFigure([]), TypeError);
});

test('rejects malformed layout, config and frames', () => {
  assert.throws(() => parseFigure({data:[], layout:[]}), TypeError);
  assert.throws(() => parseFigure({data:[], config:'bad'}), TypeError);
  assert.throws(() => parseFigure({data:[], frames:[null]}), TypeError);
});

test('supports animation frames and non-interfacial chart types', async () => {
  const chart = {data:[{type:'bar', x:['a'], y:[1]}], frames:[{name:'one', data:[{y:[2]}]}]};
  const engine = mockPlotly();
  await new PlotlyRenderer(engine).render('plot', chart);
  assert.deepEqual(engine.calls[0][2], chart);
});

test('propagates engine errors (no silent success)', async () => {
  const engine = mockPlotly();
  engine.react = async () => {throw new Error('failed to render');};
  await assert.rejects(() => new PlotlyRenderer(engine).update('plot', reference), /failed to render/);
});

test('reports unavailable resize API clearly', async () => {
  const engine = mockPlotly();
  delete engine.Plots;
  await assert.rejects(() => new PlotlyRenderer(engine).resize('plot'), /Plots.resize/);
});
