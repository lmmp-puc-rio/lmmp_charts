"""Approved v5 presentation constants: changes require visual re-approval."""

from __future__ import annotations

# These values match the approved v5 figure exactly.  They are intentionally
# named here to avoid accidentally drifting when the renderer is refactored.
FIGURE_LAYOUT = {
    "template": "plotly_white",
    "showlegend": False,
    "width": 850,
    "height": 1150,
    "autosize": False,
    "margin": {"l": 16, "r": 16, "t": 15, "b": 15},
    "paper_bgcolor": "#ffffff",
    "plot_bgcolor": "#ffffff",
    "hovermode": False,
    "dragmode": False,
    "xaxis": {"range": [0, 12], "visible": False, "fixedrange": True, "constrain": "domain"},
    "yaxis": {"range": [0, 17], "visible": False, "fixedrange": True,
              "scaleanchor": "x", "scaleratio": 1},
}

# Separate from the figure spec. Applied when rendering in the JavaScript GUI.
RENDER_CONFIG = {"displayModeBar": False, "responsive": True}
