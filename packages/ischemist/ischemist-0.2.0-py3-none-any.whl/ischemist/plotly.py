"""
Plotting style definitions and utilities for publication-quality figures.

This module provides an immutable, theme-based styling system for Plotly figures.
The Styler class applies a consistent and configurable style, with built-in
support for light and dark themes.

Core Principles:
  - Immutability: Styler instances are immutable. Methods like `with_params` or
    `with_theme` return a NEW `Styler` instance, preventing side effects.
  - Theming: Styles are defined as `StyleConfig` objects and managed in a
    central registry, making the system easily extensible.
  - Simplicity: A single `apply_style` method handles all styling, providing a
    clean and predictable API.

Example:
    # Default light theme
    styler = Styler()
    styler.apply_style(fig)

    # Dark theme via boolean flag (for convenience)
    styler_dark = Styler(dark=True)
    styler_dark.apply_style(fig)

    # Select theme by name
    styler_dark_explicit = Styler(theme='dark')
    styler_dark_explicit.apply_style(fig)

    # Create a styler with custom overrides
    styler_custom = Styler(title_size=24, grid_color="#FF0000")
    styler_custom.apply_style(fig)

    # Create a new styler from an existing one
    styler_modified = styler_dark.with_params(axis_title_size=18)
    styler_modified.apply_style(fig)
"""

from __future__ import annotations

import dataclasses
import functools
from typing import Any

import plotly.graph_objects as go


@dataclasses.dataclass(frozen=True)
class StyleConfig:
    """
    Immutable configuration for figure styling parameters.

    Using frozen=True ensures that once a style configuration is created,
    it cannot be accidentally modified, promoting predictable behavior.
    """

    # Theme metadata
    name: str

    # Font settings
    font_family: str = "Helvetica"
    font_color: str = "#333333"
    title_color: str = "#333333"

    # Font sizes
    title_size: int = 20
    axis_title_size: int = 16
    tick_label_size: int = 16
    legend_size: int = 12
    subplot_title_size: int = 14

    # Axis styling
    show_grid: bool = True
    grid_width: int = 1
    grid_color: str = "#E7E7E7"
    show_zeroline: bool = False
    line_width: int = 2
    line_color: str = "#333333"

    # Layout colors
    plot_background: str = "#FBFCFF"
    paper_background: str = "#FBFCFF"

    # Plotly template for base styling
    template: str | None = None


# --- Theme Definitions ---
THEME_LIGHT = StyleConfig(name="light")

THEME_DARK = dataclasses.replace(
    THEME_LIGHT,
    name="dark",
    font_color="#DFDFDF",
    title_color="#DFDFDF",
    grid_color="#444444",
    line_color="#868686",
    plot_background="black",
    paper_background="black",
    template="plotly_dark",
)

# --- Theme Registry ---
THEMES = {"light": THEME_LIGHT, "dark": THEME_DARK}


class Styler:
    """
    Applies consistent, theme-based styling to Plotly figures.

    Styler instances are immutable. Configuration is provided at initialization
    by selecting a theme and providing optional overrides. To modify a styler,
    use methods like `with_params` or `with_theme` to create a new instance.
    """

    def __init__(
        self,
        theme: str | StyleConfig = "light",
        dark: bool | None = None,
        **overrides: Any,
    ) -> None:
        """
        Initializes the Styler with a configuration.

        Args:
            theme: The name of the theme to use (e.g., 'light', 'dark') or a
                   custom `StyleConfig` instance.
            dark: A convenience flag to select the 'dark' theme. If True, it
                  overrides the `theme` argument.
            **overrides: Keyword arguments to override specific `StyleConfig` parameters.
        """
        if dark:
            theme = "dark"

        if isinstance(theme, str):
            base_config = THEMES.get(theme)
            if base_config is None:
                raise ValueError(f"Unknown theme: '{theme}'. Available themes: {list(THEMES.keys())}")
        elif isinstance(theme, StyleConfig):
            base_config = theme
        else:
            raise TypeError("`theme` must be a string or a StyleConfig instance.")

        self.config: StyleConfig = dataclasses.replace(base_config, **overrides)

    def with_params(self, **kwargs: Any) -> Styler:
        """
        Creates a new Styler with updated configuration parameters.

        Args:
            **kwargs: `StyleConfig` parameters to override.

        Returns:
            A new `Styler` instance with the applied overrides.
        """
        # Create a new config by applying kwargs to the current config
        new_config_dict = {**dataclasses.asdict(self.config), **kwargs}
        return Styler(theme=StyleConfig(**new_config_dict))

    def with_theme(self, theme: str) -> Styler:
        """
        Creates a new Styler based on a different theme, keeping existing overrides.

        Args:
            theme: The name of the new base theme.

        Returns:
            A new `Styler` instance with the new theme.
        """
        # Get the original overrides used to create this styler
        current_config_dict = dataclasses.asdict(self.config)
        base_theme_dict = dataclasses.asdict(THEMES[self.config.name])
        overrides = {k: v for k, v in current_config_dict.items() if base_theme_dict.get(k) != v}

        return Styler(theme=theme, **overrides)

    def copy(self) -> Styler:
        """Creates an identical copy of this Styler."""
        return Styler(theme=self.config)

    @functools.cached_property
    def _axis_style(self) -> dict[str, Any]:
        """Generates the style dictionary for axes."""
        return {
            "showgrid": self.config.show_grid,
            "gridwidth": self.config.grid_width,
            "gridcolor": self.config.grid_color,
            "zeroline": self.config.show_zeroline,
            "linewidth": self.config.line_width,
            "linecolor": self.config.line_color,
            "title_font": self._font(self.config.axis_title_size, bold=True),
            "tickfont": self._font(self.config.tick_label_size),
        }

    def _font(self, size: int, bold: bool = False, for_title: bool = False) -> dict[str, Any]:
        """Helper to create a consistent font dictionary."""
        return {
            "family": self.config.font_family,
            "size": size,
            "color": self.config.title_color if for_title else self.config.font_color,
            "weight": "bold" if bold else "normal",
        }

    def apply_style(self, fig: go.Figure, **layout_kwargs: Any) -> None:
        """
        Applies the complete styling configuration to a Plotly figure.

        Args:
            fig: The Plotly figure to style.
            **layout_kwargs: Additional `fig.update_layout` parameters that will
                             override any styler-defined settings.
        """
        # 1. Apply base template first
        if self.config.template:
            fig.update_layout(template=self.config.template)

        # 2. Apply axes styling
        fig.update_xaxes(**self._axis_style)
        fig.update_yaxes(**self._axis_style)

        # 3. Apply layout styling
        layout_style = {
            "plot_bgcolor": self.config.plot_background,
            "paper_bgcolor": self.config.paper_background,
            "font": self._font(self.config.tick_label_size),
            "title_font": self._font(self.config.title_size, bold=True, for_title=True),
            "legend": {"font": self._font(self.config.legend_size)},
        }
        fig.update_layout(**layout_style)

        # 4. Apply subplot title fonts if they exist
        if fig.layout.annotations:
            subplot_title_font = self._font(self.config.subplot_title_size, bold=True, for_title=True)
            for annotation in fig.layout.annotations:
                # Plotly uses this pattern for `make_subplots` titles.
                if annotation.yref == "paper" and annotation.xanchor == "center":
                    annotation.font = subplot_title_font

        # 5. Apply user-provided overrides last
        if layout_kwargs:
            fig.update_layout(**layout_kwargs)
