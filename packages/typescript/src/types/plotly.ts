/** Minimal structural contract for JSON created by Plotly.py.
 *
 * Plotly.js, rather than this package, validates the full trace schema.
 * This avoids coupling the LMMP chart JSON format to one visualization type.
 */
export type JsonObject = Record<string, unknown>;

export interface PlotlyFigure {
  data: JsonObject[];
  layout?: JsonObject;
  config?: JsonObject;
  frames?: JsonObject[];
}

export type PlotlyFigureInput = PlotlyFigure | string;

/** Subset of the Plotly.js API used by the renderer.
 * Plotly.js is supplied by the consuming GUI, not loaded from a CDN.
 */
export interface PlotlyEngine {
  newPlot(element: HTMLElement | string, figure: PlotlyFigure): Promise<unknown> | unknown;
  react(element: HTMLElement | string, figure: PlotlyFigure): Promise<unknown> | unknown;
  purge(element: HTMLElement | string): void;
  Plots?: {
    resize(element: HTMLElement | string): Promise<unknown> | unknown;
  };
}
