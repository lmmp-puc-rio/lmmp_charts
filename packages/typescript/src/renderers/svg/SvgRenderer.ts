import { evaluateBindings, validateParametricDocument } from "../../parametric/svg/document.js";
import type {
  AttributePatch,
  ParameterValues,
  ParametricSvgDocument,
} from "../../types/parametricSvg.js";

const SVG_NS = "http://www.w3.org/2000/svg";
const XMLNS_NS = "http://www.w3.org/2000/xmlns/";
const MAX_ELEMENTS = 10_000;

const elementAttributes: Record<string, ReadonlySet<string>> = {
  svg: new Set(["xmlns", "width", "height", "viewBox", "preserveAspectRatio"]),
  title: new Set(),
  desc: new Set(),
  g: new Set(["id", "transform", "opacity"]),
  rect: new Set([
    "id", "x", "y", "width", "height", "rx", "ry", "fill", "fill-opacity",
    "stroke", "stroke-width", "stroke-dasharray", "opacity", "transform",
  ]),
  path: new Set([
    "id", "d", "fill", "fill-opacity", "stroke", "stroke-width",
    "stroke-dasharray", "opacity", "transform",
  ]),
  text: new Set([
    "id", "x", "y", "fill", "font-family", "font-size", "text-anchor",
    "dominant-baseline", "opacity",
  ]),
  circle: new Set([
    "id", "cx", "cy", "r", "fill", "fill-opacity", "stroke", "stroke-width",
    "stroke-dasharray", "opacity", "transform",
  ]),
  ellipse: new Set([
    "id", "cx", "cy", "rx", "ry", "fill", "fill-opacity", "stroke",
    "stroke-width", "stroke-dasharray", "opacity", "transform",
  ]),
  line: new Set([
    "id", "x1", "y1", "x2", "y2", "stroke", "stroke-width",
    "stroke-dasharray", "opacity", "transform",
  ]),
  polyline: new Set([
    "id", "points", "fill", "fill-opacity", "stroke", "stroke-width",
    "stroke-dasharray", "opacity", "transform",
  ]),
  polygon: new Set([
    "id", "points", "fill", "fill-opacity", "stroke", "stroke-width",
    "stroke-dasharray", "opacity", "transform",
  ]),
};

const patchableAttributes = new Set([
  "d", "transform", "fill", "stroke", "stroke-width", "stroke-dasharray",
  "opacity", "x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "rx",
  "ry", "points", "textContent",
]);

const textOnlyElements = new Set(["title", "desc", "text"]);

function finiteNumbers(value: string, count?: number): number[] {
  const parts = value.trim().split(/[\s,]+/);
  if (!parts.length || parts.some(part => !part)) {
    throw new TypeError("Invalid SVG numeric attribute");
  }
  const numbers = parts.map(Number);
  if ((count !== undefined && numbers.length !== count) ||
      numbers.some(number => !Number.isFinite(number) || Math.abs(number) > 1_000_000)) {
    throw new TypeError("Invalid SVG numeric attribute");
  }
  return numbers;
}

function validatePathData(value: string): void {
  const tokenPattern = /([MLCQAZmlcqaz])|([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)/y;
  const tokens: Array<string | number> = [];
  let position = 0;
  while (position < value.length) {
    while (position < value.length && /[\s,]/.test(value[position]!)) position++;
    if (position === value.length) break;
    tokenPattern.lastIndex = position;
    const match = tokenPattern.exec(value);
    if (!match) throw new TypeError("SVG path contains unsupported syntax");
    tokens.push(match[1] ?? Number(match[2]));
    position = tokenPattern.lastIndex;
    if (tokens.length > 8_192) throw new RangeError("SVG path is too complex");
  }

  const argumentCounts: Record<string, number> = { M: 2, L: 2, C: 6, Q: 4, A: 7, Z: 0 };
  let index = 0;
  let commands = 0;
  while (index < tokens.length) {
    const command = tokens[index++];
    if (typeof command !== "string") throw new TypeError("SVG path command expected");
    const upper = command.toUpperCase();
    const argumentCount = argumentCounts[upper];
    if (argumentCount === undefined || (commands === 0 && upper !== "M")) {
      throw new TypeError("SVG path command is not allowed");
    }
    if (index + argumentCount > tokens.length) {
      throw new TypeError("SVG path command has incomplete coordinates");
    }
    const args = tokens.slice(index, index + argumentCount);
    if (args.some(argument => typeof argument !== "number" ||
        !Number.isFinite(argument) || Math.abs(argument) > 1_000_000)) {
      throw new TypeError("SVG path coordinates must be finite numbers");
    }
    if (upper === "A") {
      const [rx, ry, , largeArc, sweep] = args as number[];
      if (rx! < 0 || ry! < 0 || (largeArc !== 0 && largeArc !== 1) ||
          (sweep !== 0 && sweep !== 1)) {
        throw new TypeError("Invalid SVG arc parameters");
      }
    }
    index += argumentCount;
    commands++;
    if (commands > 1_000) throw new RangeError("SVG path has too many commands");
  }
  if (commands === 0) throw new TypeError("SVG path cannot be empty");
}

function validatePaint(value: string): void {
  const namedOrHex = /^(?:none|transparent|currentColor|[a-zA-Z]{1,24}|#[\da-fA-F]{3,8})$/;
  const functional = /^rgba?\(\s*\d{1,3}(?:\.\d+)?%?\s*,\s*\d{1,3}(?:\.\d+)?%?\s*,\s*\d{1,3}(?:\.\d+)?%?(?:\s*,\s*(?:0|1|0?\.\d+))?\s*\)$/;
  if (!namedOrHex.test(value) && !functional.test(value)) {
    throw new TypeError("Unsafe or unsupported SVG paint value");
  }
}

function validateTransform(value: string): void {
  const functionPattern = /(translate|scale|rotate|matrix)\(([^()]*)\)/gy;
  let position = 0;
  let count = 0;
  while (position < value.length) {
    while (position < value.length && /[\s,]/.test(value[position]!)) position++;
    if (position === value.length) break;
    functionPattern.lastIndex = position;
    const match = functionPattern.exec(value);
    if (!match) throw new TypeError("Unsupported SVG transform");
    const args = finiteNumbers(match[2]!);
    const expected: Record<string, number[]> = {
      translate: [1, 2],
      scale: [1, 2],
      rotate: [1, 3],
      matrix: [6],
    };
    if (!expected[match[1]!]!.includes(args.length)) {
      throw new TypeError("Invalid SVG transform arguments");
    }
    position = functionPattern.lastIndex;
    if (++count > 16) throw new RangeError("SVG transform is too complex");
  }
  if (!count) throw new TypeError("SVG transform cannot be empty");
}

function validateAttribute(tag: string, name: string, value: string): void {
  if (value.length > 8_192) throw new RangeError("SVG attribute is too long");
  if (!elementAttributes[tag]?.has(name)) {
    throw new TypeError(`SVG attribute ${name} is not allowed on ${tag}`);
  }
  if (name === "id") {
    if (!/^[A-Za-z][A-Za-z0-9_-]{0,127}$/.test(value)) {
      throw new TypeError("Invalid SVG element id");
    }
  } else if (name === "d") validatePathData(value);
  else if (name === "points") {
    const points = finiteNumbers(value);
    if (points.length < 4 || points.length % 2 !== 0 || points.length > 8_192) {
      throw new TypeError("Invalid SVG points attribute");
    }
  } else if (name === "fill" || name === "stroke") validatePaint(value);
  else if (name === "transform") validateTransform(value);
  else if (name === "viewBox") {
    const [x, y, width, height] = finiteNumbers(value, 4);
    if (width! <= 0 || height! <= 0) throw new TypeError("Invalid SVG viewBox");
    void x;
    void y;
  } else if (name === "preserveAspectRatio") {
    if (!/^(?:none|x(?:Min|Mid|Max)Y(?:Min|Mid|Max))(?:\s+(?:meet|slice))?$/.test(value)) {
      throw new TypeError("Invalid SVG preserveAspectRatio");
    }
  } else if (name === "stroke-dasharray") {
    const dashes = finiteNumbers(value);
    if (!dashes.length || dashes.some(dash => dash < 0)) {
      throw new TypeError("Invalid SVG stroke-dasharray");
    }
  } else if (name === "font-family") {
    if (!/^[A-Za-z0-9 ,_-]{1,100}$/.test(value)) throw new TypeError("Invalid SVG font-family");
  } else if (name === "text-anchor") {
    if (!["start", "middle", "end"].includes(value)) throw new TypeError("Invalid SVG text-anchor");
  } else if (name === "dominant-baseline") {
    if (!["auto", "middle", "central", "hanging"].includes(value)) {
      throw new TypeError("Invalid SVG dominant-baseline");
    }
  } else if (name === "opacity" || name === "fill-opacity") {
    const [opacity] = finiteNumbers(value, 1);
    if (opacity! < 0 || opacity! > 1) throw new TypeError("Invalid SVG opacity");
  } else if (name !== "xmlns") {
    const [number] = finiteNumbers(value, 1);
    if (name === "width" || name === "height" || name === "r" ||
        name === "rx" || name === "ry" || name === "stroke-width" || name === "font-size") {
      if (number! < 0) throw new TypeError(`SVG ${name} cannot be negative`);
    }
  }
}

interface SanitizedSvg {
  root: SVGSVGElement;
  targets: Map<string, Element>;
}

function sanitizeSvg(markup: string, targetDocument: Document): SanitizedSvg {
  if (markup.length > 2_000_000 || /<!DOCTYPE/i.test(markup)) {
    throw new TypeError("SVG markup is too large or contains a document type");
  }
  if (typeof DOMParser === "undefined") {
    throw new Error("SVG rendering requires a browser DOMParser");
  }
  const parsed = new DOMParser().parseFromString(markup, "image/svg+xml");
  if (parsed.doctype || parsed.getElementsByTagName("parsererror").length) {
    throw new TypeError("SVG markup is not valid XML");
  }
  const sourceRoot = parsed.documentElement;
  if (!sourceRoot || sourceRoot.localName !== "svg" || sourceRoot.namespaceURI !== SVG_NS) {
    throw new TypeError("SVG document root must be an SVG element");
  }

  const targets = new Map<string, Element>();
  let elementCount = 0;
  let textLength = 0;

  const cloneElement = (source: Element): Element => {
    const tag = source.localName;
    if (source.namespaceURI !== SVG_NS || !elementAttributes[tag] ||
        (tag === "svg" && source !== sourceRoot)) {
      throw new TypeError(`SVG element ${tag} is not allowed`);
    }
    if (++elementCount > MAX_ELEMENTS) throw new RangeError("SVG contains too many elements");
    const clean = targetDocument.createElementNS(SVG_NS, tag);
    for (const attribute of Array.from(source.attributes)) {
      if (attribute.namespaceURI === XMLNS_NS && attribute.name === "xmlns" &&
          tag === "svg" && attribute.value === SVG_NS) {
        clean.setAttribute("xmlns", SVG_NS);
        continue;
      }
      if (attribute.namespaceURI !== null) {
        throw new TypeError("Namespaced SVG attributes are not allowed");
      }
      validateAttribute(tag, attribute.name, attribute.value);
      if (attribute.name === "id") {
        if (targets.has(attribute.value)) throw new TypeError("Duplicate SVG element id");
        targets.set(attribute.value, clean);
      }
      clean.setAttribute(attribute.name, attribute.value);
    }

    for (const child of Array.from(source.childNodes)) {
      if (child.nodeType === Node.ELEMENT_NODE) {
        if (textOnlyElements.has(tag)) throw new TypeError(`${tag} cannot contain SVG elements`);
        clean.appendChild(cloneElement(child as Element));
      } else if (child.nodeType === Node.TEXT_NODE) {
        const text = child.nodeValue ?? "";
        textLength += text.length;
        if (textLength > 20_000 ||
            (!textOnlyElements.has(tag) && text.trim().length > 0)) {
          throw new TypeError("Unexpected SVG text content");
        }
        if (textOnlyElements.has(tag)) clean.appendChild(targetDocument.createTextNode(text));
      } else {
        throw new TypeError("Unsupported SVG node type");
      }
    }
    return clean;
  };

  const root = cloneElement(sourceRoot) as SVGSVGElement;
  if (!root.hasAttribute("xmlns")) root.setAttribute("xmlns", SVG_NS);
  return { root, targets };
}

export class SvgRenderer {
  private container: Element | undefined;
  private document: ParametricSvgDocument | undefined;
  private targets = new Map<string, Element>();
  private root: SVGSVGElement | undefined;

  /** Sanitize, mount and initialize an SVG contract document. */
  mount(container: Element, input: unknown): void {
    const contract = validateParametricDocument(input);
    const sanitized = sanitizeSvg(contract.svg, container.ownerDocument);
    const patches = evaluateBindings(contract);
    this.validatePatches(patches, sanitized.targets);
    this.applyPatches(patches, sanitized.targets);

    if (this.root && this.root.parentElement === this.container && this.container !== container) {
      this.root.remove();
    }
    container.replaceChildren(sanitized.root);
    this.container = container;
    this.document = contract;
    this.targets = sanitized.targets;
    this.root = sanitized.root;
  }

  /** Evaluate and apply a complete binding update before the browser paints. */
  update(overrides: ParameterValues): void {
    if (!this.document) throw new Error("No SVG document is mounted");
    const patches = evaluateBindings(this.document, overrides);
    this.validatePatches(patches, this.targets);
    this.applyPatches(patches, this.targets);
  }

  /** Remove the mounted SVG and release references to its document. */
  destroy(): void {
    if (this.root && this.root.parentElement === this.container) this.root.remove();
    this.container = undefined;
    this.document = undefined;
    this.targets.clear();
    this.root = undefined;
  }

  private validatePatches(
    patches: AttributePatch[],
    targets: Map<string, Element>,
  ): void {
    for (const patch of patches) {
      const target = targets.get(patch.target);
      if (!target || !patchableAttributes.has(patch.attribute)) {
        throw new TypeError("SVG binding target or attribute is not allowed");
      }
      if (patch.attribute === "textContent") {
        if (!textOnlyElements.has(target.localName) || typeof patch.value !== "string" ||
            patch.value.length > 2_000) {
          throw new TypeError("SVG text binding is invalid");
        }
      } else {
        if (typeof patch.value !== "string" ||
            !elementAttributes[target.localName]?.has(patch.attribute)) {
          throw new TypeError("SVG binding does not match its target element");
        }
        validateAttribute(target.localName, patch.attribute, patch.value);
      }
    }
  }

  private applyPatches(patches: AttributePatch[], targets: Map<string, Element>): void {
    for (const patch of patches) {
      const target = targets.get(patch.target)!;
      if (patch.attribute === "textContent") target.textContent = patch.value as string;
      else target.setAttribute(patch.attribute, patch.value as string);
    }
  }
}
