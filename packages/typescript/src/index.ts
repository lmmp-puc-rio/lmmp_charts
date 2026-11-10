/** Public entry point: generic Plotly renderer and parametric SVG contract. */
export { PlotlyRenderer, parseFigure } from "./renderers/plotly/PlotlyRenderer.js";
export type { JsonObject, PlotlyEngine, PlotlyFigure, PlotlyFigureInput } from "./types/plotly.js";

export { evaluateExpression, references, ExpressionError } from "./parametric/expressions/evaluator.js";
export { validateParametricDocument, evaluateBindings } from "./parametric/svg/document.js";
export type { Expression, Scalar } from "./parametric/expressions/evaluator.js";
export type {
  ParametricSvgDocument, ParameterSpec, AttributePatch, ParameterValues
} from "./types/parametricSvg.js";
