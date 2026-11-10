import type { Expression, Scalar } from "../parametric/expressions/evaluator.js";

export interface ParameterSpec {
  type: "number" | "string";
  value: number | string;
  min?: number;
  max?: number;
  unit?: string;
}
export interface SvgBinding {
  target: string;
  attribute: string;
  expression: Expression;
}
export interface ParameterConstraint {
  expression: Expression;
  message: string;
}
/** Versioned transport object: SVG markup is not trusted/sanitized by this type. */
export interface ParametricSvgDocument {
  format: "lmmp-parametric-svg";
  version: "1.0.0";
  svg: string;
  parameters: Record<string, ParameterSpec>;
  bindings: SvgBinding[];
  constraints: ParameterConstraint[];
}
export type ParameterValues = Record<string, Scalar>;
export interface AttributePatch {
  target: string;
  attribute: string;
  value: number | string;
}
