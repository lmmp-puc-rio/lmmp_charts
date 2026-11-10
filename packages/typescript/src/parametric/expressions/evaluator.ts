/** Safe, tiny JSON expression interpreter: no eval(), Function, or dynamic code. */
export type Scalar = number | string | boolean;
export type Expression =
  | { const: Scalar }
  | { var: string }
  | { op: string; args: Expression[] }
  | { op: "path"; commands: Array<{ cmd: string; values: Expression[] }> };

export class ExpressionError extends Error {
  constructor(message: string) { super(message); this.name = "ExpressionError"; }
}

const ARITIES: Record<string, readonly [number, number | null]> = {
  add: [2, null], sub: [2, 2], mul: [2, null], div: [2, 2],
  pow: [2, 2], neg: [1, 1], abs: [1, 1], sqrt: [1, 1],
  sin: [1, 1], cos: [1, 1], tan: [1, 1],
  atan2: [2, 2], radians: [1, 1], degrees: [1, 1],
  min: [2, null], max: [2, null], lt: [2, 2], lte: [2, 2],
  gt: [2, 2], gte: [2, 2], eq: [2, 2], ne: [2, 2],
  if: [3, 3], concat: [1, null],
};
const PATH_ARITIES: Record<string, number> = { M: 2, L: 2, C: 6, Q: 4, A: 7, Z: 0 };
const FORBIDDEN = new Set(["constructor", "prototype", "__proto__"]);
const own = (x: object, k: string) => Object.prototype.hasOwnProperty.call(x, k);
const object = (x: unknown): x is Record<string, unknown> =>
  typeof x === "object" && x !== null && !Array.isArray(x);
const keysEqual = (x: Record<string, unknown>, ...expected: string[]): boolean =>
  Object.keys(x).length === expected.length && expected.every(k => own(x, k));
export function validParameterName(name: unknown): name is string {
  return typeof name === "string" &&
    /^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$/.test(name) &&
    !name.split(".").some(s => FORBIDDEN.has(s));
}
function finite(x: unknown): number {
  if (typeof x !== "number" || !Number.isFinite(x)) {
    throw new ExpressionError("An operator requires finite numbers");
  }
  return x;
}
function scalar(x: unknown): x is Scalar {
  return (typeof x === "string" && x.length <= 2000) ||
    typeof x === "boolean" || (typeof x === "number" && Number.isFinite(x));
}
function numString(value: unknown): string {
  const n = finite(value);
  const s = n.toFixed(6).replace(/0+$/, "").replace(/\.$/, "");
  return !s || s === "-0" ? "0" : s;
}

/** Validate the entire tree, including inactive conditional branches. */
export function references(expression: unknown): Set<string> {
  const seen = new Set<string>();
  let count = 0;
  function walk(node: unknown, depth: number): void {
    count++;
    if (depth > 40 || count > 2048) throw new ExpressionError("Expression complexity limit exceeded");
    if (!object(node)) throw new ExpressionError("Each expression must be an object");
    if (keysEqual(node, "const")) {
      if (!scalar(node.const)) throw new ExpressionError("Unsupported constant type");
      return;
    }
    if (keysEqual(node, "var")) {
      if (!validParameterName(node.var)) throw new ExpressionError("Invalid parameter name");
      seen.add(node.var);
      return;
    }
    if (node.op === "path") {
      if (!keysEqual(node, "op", "commands") || !Array.isArray(node.commands) || node.commands.length > 500)
        throw new ExpressionError("Malformed SVG path");
      for (const c of node.commands) {
        if (!object(c) || !keysEqual(c, "cmd", "values") || typeof c.cmd !== "string" ||
            !own(PATH_ARITIES, c.cmd) || !Array.isArray(c.values) ||
            c.values.length !== PATH_ARITIES[c.cmd]) {
          throw new ExpressionError("Malformed SVG path command");
        }
        for (const v of c.values) walk(v, depth + 1);
      }
      return;
    }
    if (!keysEqual(node, "op", "args") || typeof node.op !== "string" ||
        !own(ARITIES, node.op) || !Array.isArray(node.args)) {
      throw new ExpressionError("Unknown or malformed expression operation");
    }
    const [min, max] = ARITIES[node.op]!;
    if (node.args.length < min || (max !== null && node.args.length > max)) {
      throw new ExpressionError("Invalid number of arguments for " + node.op);
    }
    for (const arg of node.args) walk(arg, depth + 1);
  }
  walk(expression, 0);
  return seen;
}

/** Return a scalar or SVG path string from a versioned JSON expression tree. */
export function evaluateExpression(expression: unknown, variables: Record<string, Scalar>): Scalar {
  const refs = references(expression);
  if (!object(variables)) throw new ExpressionError("Variables must be an object");
  for (const name of refs) if (!own(variables, name)) {
    throw new ExpressionError("Unknown parameter: " + name);
  }
  function run(node: unknown): Scalar {
    if (!object(node)) throw new ExpressionError("Invalid expression");
    if (own(node, "const")) return node.const as Scalar;
    if (own(node, "var")) {
      const value = variables[node.var as string];
      if (!scalar(value)) throw new ExpressionError("Unsupported parameter value");
      return value;
    }
    const op = node.op as string;
    if (op === "path") {
      const chunks: string[] = [];
      const cmds = node.commands as Array<{ cmd: string; values: Expression[] }>;
      for (const c of cmds) {
        const values = c.values.map(run);
        if (c.cmd === "A") {
          if ((values[3] !== 0 && values[3] !== 1) || (values[4] !== 0 && values[4] !== 1)) {
            throw new ExpressionError("SVG arc flags must be 0 or 1");
          }
          if (finite(values[0]) < 0 || finite(values[1]) < 0)
            throw new ExpressionError("SVG arc radii must be nonnegative");
        }
        chunks.push([c.cmd, ...values.map(numString)].join(" ").trim());
      }
      const result = chunks.join(" ");
      if (result.length > 50000) throw new ExpressionError("Output SVG path is too long");
      return result;
    }
    const args = node.args as Expression[];
    if (op === "if") {
      const predicate = run(args[0]);
      if (typeof predicate !== "boolean") throw new ExpressionError("if condition must be boolean");
      return run(args[predicate ? 1 : 2]);
    }
    const values = args.map(run);
    if (op === "concat") {
      const result = values.map(x => String(x)).join("");
      if (result.length > 50000) throw new ExpressionError("Output text is too long");
      return result;
    }
    if (op === "eq") return typeof values[0] === typeof values[1] && values[0] === values[1];
    if (op === "ne") return !(typeof values[0] === typeof values[1] && values[0] === values[1]);
    const n = values.map(finite);
    let result: number | boolean;
    switch (op) {
      case "add": result = n.reduce((a, b) => a + b, 0); break;
      case "sub": result = n[0]! - n[1]!; break;
      case "mul": result = n.reduce((a, b) => a * b, 1); break;
      case "div": result = n[0]! / n[1]!; break;
      case "pow": result = Math.pow(n[0]!, n[1]!); break;
      case "neg": result = -n[0]!; break;
      case "abs": result = Math.abs(n[0]!); break;
      case "sqrt": result = Math.sqrt(n[0]!); break;
      case "sin": result = Math.sin(n[0]!); break;
      case "cos": result = Math.cos(n[0]!); break;
      case "tan": result = Math.tan(n[0]!); break;
      case "atan2": result = Math.atan2(n[0]!, n[1]!); break;
      case "radians": result = n[0]! * Math.PI / 180; break;
      case "degrees": result = n[0]! * 180 / Math.PI; break;
      case "min": result = Math.min(...n); break;
      case "max": result = Math.max(...n); break;
      case "lt": return n[0]! < n[1]!;
      case "lte": return n[0]! <= n[1]!;
      case "gt": return n[0]! > n[1]!;
      case "gte": return n[0]! >= n[1]!;
      default: throw new ExpressionError("Unsupported operation: " + op);
    }
    return finite(result);
  }
  return run(expression);
}
