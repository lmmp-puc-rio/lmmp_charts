/** Run after `cd packages/renderer && npm run build` from repository root:
 *    node examples/parametric_contract_demo.mjs
 */
import {readFileSync} from 'node:fs';
import {validateParametricDocument,evaluateBindings} from '../packages/typescript/dist/index.js';
const fixture=new URL('../tests/integration/fixtures/parametric_contract.json',import.meta.url);
const document=validateParametricDocument(JSON.parse(readFileSync(fixture,'utf-8')));
console.log('Initial patches:\n'+JSON.stringify(evaluateBindings(document),null,2));
console.log('Updated patches:\n'+JSON.stringify(evaluateBindings(document,{theta:35,theta_receding:20,theta_advancing:80}),null,2));
