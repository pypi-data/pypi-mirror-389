"""
Developer utilities for visualizing color palettes.

This module is not part of the core package but provides tools to inspect
and validate palettes during development.
"""

import math

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ischemist.colors import ColorPalette
from ischemist.plotly import Styler


def plot_palettes(
    palettes: dict[str, ColorPalette],
    cols: int = 4,
    title: str = "Color Palette Preview",
) -> go.Figure:
    """
    Generates a Plotly figure to visualize a dictionary of ColorPalettes.

    Each palette is displayed as a continuous horizontal bar in a subplot grid.
    Detailed color information is available on hover.

    Args:
        palettes: A dictionary mapping palette names (str) to ColorPalette objects.
        cols: The number of columns to use in the subplot grid.
        title: The main title for the figure.

    Returns:
        A `go.Figure` object containing the visualization.
    """
    if not palettes:
        return go.Figure()

    n_palettes = len(palettes)
    rows = math.ceil(n_palettes / cols)
    palette_names = list(palettes.keys())

    fig = make_subplots(
        rows=rows,
        cols=cols,
        subplot_titles=palette_names,
        # horizontal_spacing=0.04,
        # vertical_spacing=0.10,
    )

    for i, (name, palette) in enumerate(palettes.items()):
        row = (i // cols) + 1
        col = (i % cols) + 1

        colors = [str(c) for c in palette]
        bar = go.Bar(
            y=[1] * len(colors),  # Dummy y-axis for stacking
            x=[1] * len(colors),  # Each color gets an equal segment
            marker_color=colors,
            orientation="h",
            showlegend=False,
            hovertemplate=f"<b>{name}</b><br>%{{marker.color}}<extra></extra>",
        )
        fig.add_trace(bar, row=row, col=col)

    fig.update_layout(
        title_text=title,
        plot_bgcolor="#fdfdfd",
        paper_bgcolor="#fdfdfd",
        height=100 + 140 * rows,
        width=max(800, 250 * cols),
        bargap=0,  # Creates a continuous bar
        showlegend=False,
    )

    # Hide all axis ticks and labels for a cleaner look
    fig.update_xaxes(showticklabels=False, visible=False)
    fig.update_yaxes(showticklabels=False, visible=False)
    Styler(dark=False).apply_style(fig)

    return fig
