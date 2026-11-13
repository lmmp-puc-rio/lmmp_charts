/** Public entry point for the parametric SVG contract. */
export { SvgRenderer } from "./renderers/svg/SvgRenderer.js";
export { evaluateExpression, references, ExpressionError } from "./parametric/expressions/evaluator.js";
export { validateParametricDocument, evaluateBindings } from "./parametric/svg/document.js";
export type { Expression, Scalar } from "./parametric/expressions/evaluator.js";
export type {
  ParametricSvgDocument, ParameterSpec, AttributePatch, ParameterValues
} from "./types/parametricSvg.js";
