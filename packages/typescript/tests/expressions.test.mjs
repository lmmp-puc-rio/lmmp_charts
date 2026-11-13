import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {evaluateExpression, references, validateParametricDocument, evaluateBindings} from '../dist/index.js';
const root = new URL('../../../tests/integration/fixtures/', import.meta.url);
const load = name => JSON.parse(readFileSync(new URL(name, root), 'utf8'));
const fixture = load('expressions.json').numbers;
const docJson = load('parametric_contract.json');
const patchRef = load('expected_patches.json');
const c = value => ({const:value});
const op = (name,...args) => ({op:name,args});
const v = name => ({var:name});
const clone = x => structuredClone(x);

for (const entry of fixture.cases) {
  test('shared expression: '+entry.name, () => {
    const actual = evaluateExpression(entry.expression, fixture.variables);
    if (typeof entry.expected === 'number') assert.ok(Math.abs(actual-entry.expected)<1e-10, entry.name);
    else assert.deepEqual(actual, entry.expected);
  });
}

test('references and nested parameter names',()=> assert.deepEqual([...references(op('mul',v('theta'),v('wetting.size')))].sort(),['theta','wetting.size']));
test('nonfinite result rejected',()=> assert.throws(()=>evaluateExpression(op('div',c(1),c(0)),{})));
test('unknown operation rejected',()=> assert.throws(()=>evaluateExpression(op('import',c('os')),{})));
test('arbitrary syntax not accepted',()=> assert.throws(()=>evaluateExpression({op:'add',args:[c(1),c(2)],evil:'x'},{})));
test('prototype parameter blocked',()=> assert.throws(()=>evaluateExpression(v('__proto__'),{'__proto__':1})));
test('bad SVG arc flags rejected',()=> assert.throws(()=>evaluateExpression({op:'path',commands:[{cmd:'A',values:[c(3),c(4),c(0),c(2),c(0),c(3),c(4)]}]},{})));
test('conditional lazy evaluation',()=> assert.equal(evaluateExpression(op('if',c(true),c(3),op('div',c(1),c(0))),{}),3));
test('depth guard',()=>{let e=c(1);for(let i=0;i<42;i++)e=op('neg',e);assert.throws(()=>evaluateExpression(e,{}));});

test('contract: validated and evaluated on JS initial values',()=>{
  const doc = validateParametricDocument(docJson);
  const result = evaluateBindings(doc);
  assert.equal(result.length,patchRef.initial.length);
  for(let i=0;i<result.length;i++) {
    assert.equal(result[i].target, patchRef.initial[i].target);
    assert.equal(result[i].attribute, patchRef.initial[i].attribute);
    if(typeof result[i].value === 'number') assert.ok(Math.abs(result[i].value-patchRef.initial[i].value)<1e-10);
    else assert.equal(result[i].value,patchRef.initial[i].value);
  }
});
test('contract: updated values match Python',()=>{
  const doc=validateParametricDocument(docJson);
  const actual=evaluateBindings(doc,{theta:35,theta_receding:20,theta_advancing:80});
  for(let i=0;i<actual.length;i++){
    if(typeof actual[i].value === 'number') assert.ok(Math.abs(actual[i].value-patchRef.updated[i].value)<1e-10);
    else assert.equal(actual[i].value, patchRef.updated[i].value);
  }
});
test('contract: cross-parameter constraints',()=>{
  const doc=validateParametricDocument(docJson);
  assert.throws(()=>evaluateBindings(doc,{theta:80}),/Avanço/);
  assert.throws(()=>evaluateBindings(doc,{theta:10}),/Recuo/);
});
test('contract: numerical bounds and value types',()=>{
  const doc=validateParametricDocument(docJson);
  assert.throws(()=>evaluateBindings(doc,{theta:-1}));
  assert.throws(()=>evaluateBindings(doc,{theta:'bad'}));
  assert.throws(()=>evaluateBindings(doc,{'wetting.name':'X'.repeat(3000)}));
});
test('contract: unsupported version',()=>{
  const data=clone(docJson);data.version='2.0.0';
  assert.throws(()=>validateParametricDocument(data));
});
test('contract: unsafe binding attribute rejected',()=>{
  const data=clone(docJson);data.bindings[0].attribute='onload';
  assert.throws(()=>validateParametricDocument(data));
});
test('contract: unknown variable',()=>{
  const data=clone(docJson);data.bindings[0].expression={var:'unknown'};
  assert.throws(()=>validateParametricDocument(data));
});

test('contract: cross-language dynamic angle grid',()=>{
  const doc=validateParametricDocument(docJson);
  for(const entry of load('cross_language_grid.json')) {
    const result=evaluateBindings(doc,entry.overrides);
    for(let i=0;i<result.length;i++){
      assert.equal(result[i].target,entry.patches[i].target);
      assert.equal(result[i].attribute,entry.patches[i].attribute);
      if(typeof result[i].value==='number') assert.ok(Math.abs(result[i].value-entry.patches[i].value)<1e-10,`theta ${entry.overrides.theta}`);
      else assert.equal(result[i].value,entry.patches[i].value);
    }
  }
});
