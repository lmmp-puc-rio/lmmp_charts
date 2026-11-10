/** Validation and dry-run binding evaluation for parametric SVG documents.
 * No browser DOM access: the future renderer will sanitize SVG before insertion.
 */
import { evaluateExpression, references, ExpressionError, validParameterName } from "../expressions/evaluator.js";
import type { ParametricSvgDocument, ParameterValues, AttributePatch, ParameterSpec } from "../../types/parametricSvg.js";

const allowedAttributes = new Set([
  "d", "transform", "fill", "stroke", "stroke-width", "stroke-dasharray",
  "opacity", "x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "rx", "ry",
  "points", "textContent",
]);
const textualAttributes = new Set([
  "d", "transform", "fill", "stroke", "stroke-dasharray", "points", "textContent",
]);
const own = (x: object, k: string) => Object.prototype.hasOwnProperty.call(x, k);
const isObject = (x: unknown): x is Record<string, unknown> =>
  typeof x === "object" && x !== null && !Array.isArray(x);
const sameKeys = (x: Record<string, unknown>, expected: string[]): boolean =>
  Object.keys(x).length === expected.length && expected.every(k => own(x, k));
const number = (x: unknown): x is number => typeof x === "number" && Number.isFinite(x);

function validateParameters(raw: unknown): Record<string, ParameterSpec> {
  if (!isObject(raw) || Object.keys(raw).length > 100) throw new TypeError("Invalid parameters object");
  const parameters: Record<string, ParameterSpec> = Object.create(null);
  for (const [name, spec] of Object.entries(raw)) {
    if (!validParameterName(name) || !isObject(spec) ||
        !Object.keys(spec).every(k => ["type", "value", "min", "max", "unit"].includes(k))) {
      throw new TypeError("Malformed parameter declaration");
    }
    if (spec.type === "number") {
      if (!number(spec.value) || (own(spec, "min") && !number(spec.min)) ||
          (own(spec, "max") && !number(spec.max))) throw new TypeError("Nonfinite numeric parameter");
      if (number(spec.min) && spec.value < spec.min || number(spec.max) && spec.value > spec.max ||
          number(spec.min) && number(spec.max) && spec.min > spec.max) {
        throw new RangeError("Parameter out of bounds");
      }
    } else if (spec.type === "string") {
      if (typeof spec.value !== "string" || spec.value.length > 2000 ||
          own(spec, "min") || own(spec, "max")) throw new TypeError("Invalid string parameter");
    } else throw new TypeError("Unsupported parameter type");
    if (own(spec, "unit") && typeof spec.unit !== "string") throw new TypeError("unit must be a string");
    parameters[name] = spec as unknown as ParameterSpec;
  }
  return parameters;
}

export function validateParametricDocument(input: unknown): ParametricSvgDocument {
  if (!isObject(input) || input.format !== "lmmp-parametric-svg" || input.version !== "1.0.0" ||
      !Object.keys(input).every(k => ["format", "version", "svg", "parameters", "bindings", "constraints"].includes(k))) {
    throw new TypeError("Unsupported SVG document format or version");
  }
  if (typeof input.svg !== "string" || !input.svg.trim() || input.svg.length > 2_000_000) {
    throw new TypeError("Invalid SVG markup");
  }
  const parameters = validateParameters(input.parameters);
  const rawConstraints: unknown = input.constraints ?? [];
  if (!Array.isArray(input.bindings) || input.bindings.length > 512 ||
      !Array.isArray(rawConstraints) || rawConstraints.length > 50) {
    throw new TypeError("Invalid bindings or constraints");
  }
  for (const binding of input.bindings) {
    if (!isObject(binding) || !sameKeys(binding, ["target", "attribute", "expression"]) ||
        typeof binding.target !== "string" || binding.target.length > 128 ||
        !/^[A-Za-z][A-Za-z0-9_-]*$/.test(binding.target) ||
        typeof binding.attribute !== "string" || !allowedAttributes.has(binding.attribute)) {
      throw new TypeError("Malformed SVG binding");
    }
    for (const ref of references(binding.expression)) if (!own(parameters, ref)) {
      throw new ExpressionError("Unknown binding variable: " + ref);
    }
  }
  for (const c of rawConstraints) {
    if (!isObject(c) || !sameKeys(c, ["expression", "message"]) ||
        typeof c.message !== "string" || c.message.length > 500) throw new TypeError("Malformed constraint");
    for (const ref of references(c.expression)) if (!own(parameters, ref)) {
      throw new ExpressionError("Unknown constraint variable: " + ref);
    }
  }
  const document = input as unknown as ParametricSvgDocument;
  evaluateBindings(document); // Check initial values and operator validity.
  return document;
}

export function evaluateBindings(document: ParametricSvgDocument, overrides: ParameterValues = {}): AttributePatch[] {
  for (const name of Object.keys(overrides)) if (!own(document.parameters, name)) {
    throw new RangeError("Unknown parameter: " + name);
  }
  const input: Record<string, ParameterSpec> = Object.create(null);
  for (const [name, spec] of Object.entries(document.parameters)) {
    input[name] = {...spec, value: own(overrides, name) ? overrides[name] as number | string : spec.value};
  }
  const checked = validateParameters(input);
  const values: ParameterValues = Object.create(null);
  for (const [name, spec] of Object.entries(checked)) values[name] = spec.value;
  for (const constraint of document.constraints) {
    if (evaluateExpression(constraint.expression, values) !== true) {
      throw new RangeError(constraint.message);
    }
  }
  return document.bindings.map(binding => {
    const value = evaluateExpression(binding.expression, values);
    if (textualAttributes.has(binding.attribute)) {
      if (typeof value !== "string") throw new ExpressionError("Binding must produce text");
    } else if (!number(value)) throw new ExpressionError("Binding must produce a finite number");
    return { target: binding.target, attribute: binding.attribute, value } as AttributePatch;
  });
}
