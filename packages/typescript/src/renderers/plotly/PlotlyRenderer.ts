import type { JsonObject, PlotlyEngine, PlotlyFigure, PlotlyFigureInput } from "../../types/plotly.js";

type Target = HTMLElement | string;

function isObject(value: unknown): value is JsonObject {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

/** Parse a Plotly.py JSON string, or validate a native Plotly figure object.
 *
 * The converter deliberately does not rewrite data, layout, config or frames.
 * This ensures the Python chart definition is faithfully transported to JS.
 */
export function parseFigure(input: PlotlyFigureInput): PlotlyFigure {
  const value: unknown = typeof input === "string" ? JSON.parse(input) : input;
  if (!isObject(value)) {
    throw new TypeError("A Plotly figure must be a JSON object.");
  }
  if (!Array.isArray(value.data) || !value.data.every(isObject)) {
    throw new TypeError("Plotly figure.data must be an array of trace objects.");
  }
  if (value.layout !== undefined && !isObject(value.layout)) {
    throw new TypeError("Plotly figure.layout must be an object.");
  }
  if (value.config !== undefined && !isObject(value.config)) {
    throw new TypeError("Plotly figure.config must be an object.");
  }
  if (value.frames !== undefined &&
      (!Array.isArray(value.frames) || !value.frames.every(isObject))) {
    throw new TypeError("Plotly figure.frames must be an array of objects.");
  }
  return value as unknown as PlotlyFigure;
}

/** Framework-independent bridge from LMMP Python payloads to Plotly.js.
 *
 * The consumer injects the Plotly.js library, enabling local/offline use
 * and straightforward unit testing without a browser or Django.
 */
export class PlotlyRenderer {
  constructor(private readonly plotly: PlotlyEngine) {}

  async render(target: Target, payload: PlotlyFigureInput): Promise<void> {
    await this.plotly.newPlot(target, parseFigure(payload));
  }

  async update(target: Target, payload: PlotlyFigureInput): Promise<void> {
    await this.plotly.react(target, parseFigure(payload));
  }

  async resize(target: Target): Promise<void> {
    if (!this.plotly.Plots?.resize) {
      throw new Error("The Plotly.js instance does not expose Plots.resize().");
    }
    await this.plotly.Plots.resize(target);
  }

  destroy(target: Target): void {
    this.plotly.purge(target);
  }
}
