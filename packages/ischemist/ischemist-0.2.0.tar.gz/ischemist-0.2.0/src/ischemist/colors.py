"""
Core color definitions and palette management.

This module provides immutable data structures for colors (`Color`) and collections
of colors (`ColorPalette`). It includes a robust sampling method to select
perceptually distant colors from a palette and a central registry for all
pre-defined palettes.

Key Design Choices:
  - Immutability: `Color` and `ColorPalette` are frozen dataclasses. Once created,
    they cannot be changed, ensuring predictable behavior.
  - Central Registry: All palettes are stored in a single `PALETTES` dictionary,
    making them easy to browse, access, and extend.
  - Principled Sampling: The `ColorPalette.sample` method uses `numpy.linspace` for
    evenly distributed color selection and `itertools.cycle` for requests larger
    than the palette size, providing superior results to simple modulo arithmetic.
"""

from __future__ import annotations

import colorsys
import functools
import itertools
from collections.abc import Iterator
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Color:
    """Represents an immutable color in hexadecimal format."""

    hex_code: str

    def __post_init__(self) -> None:
        """Validates the hex code format."""
        if not isinstance(self.hex_code, str) or not self.hex_code.startswith("#"):
            raise ValueError(f"Hex code must be a string starting with '#', got: {self.hex_code}")

        hex_value = self.hex_code[1:]
        if len(hex_value) != 6 or not all(c in "0123456789abcdefABCDEF" for c in hex_value):
            raise ValueError(f"Invalid hex color code: {self.hex_code}")

    @classmethod
    def from_rgb(cls, r: int, g: int, b: int) -> Color:
        """Creates a Color instance from RGB values (0-255)."""
        for val in (r, g, b):
            if not 0 <= val <= 255:
                raise ValueError("RGB values must be between 0 and 255.")
        return cls(f"#{r:02x}{g:02x}{b:02x}")

    @functools.cached_property
    def rgb(self) -> tuple[int, int, int]:
        """Returns the color as an (R, G, B) tuple."""
        hex_value = self.hex_code[1:]
        return int(hex_value[0:2], 16), int(hex_value[2:4], 16), int(hex_value[4:6], 16)

    @functools.cached_property
    def hsv(self) -> tuple[float, float, float]:
        """Returns the color as an (H, S, V) tuple with values in [0, 1]."""
        r, g, b = self.rgb
        return colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)

    def to_rgba_str(self, alpha: float = 1.0) -> str:
        """Returns the color as an 'rgba(r, g, b, a)' string."""
        if not 0.0 <= alpha <= 1.0:
            raise ValueError("Alpha must be between 0.0 and 1.0.")
        r, g, b = self.rgb
        return f"rgba({r}, {g}, {b}, {alpha})"

    def __str__(self) -> str:
        return self.hex_code


@dataclass(frozen=True)
class ColorPalette:
    """
    An immutable collection of `Color` objects.
    Provides methods for sampling perceptually distant colors.
    """

    colors: tuple[Color, ...] = field(default_factory=tuple)

    @classmethod
    def from_hex_codes(cls, hex_codes: list[str]) -> ColorPalette:
        """Creates a ColorPalette from a list of hex color strings."""
        # Ensure '#' prefix for consistency
        processed_codes = [code if code.startswith("#") else f"#{code}" for code in hex_codes]
        return cls(tuple(Color(code) for code in processed_codes))

    def sample(self, n: int, as_hex: bool = False, reverse: bool = False) -> list[Color] | list[str]:
        """
        Selects `n` perceptually distant colors from the palette.

        - If `n` is less than or equal to the palette size, it selects evenly
          spaced colors using `numpy.linspace`.
        - If `n` is greater than the palette size, it cycles through the colors.

        Args:
            n: The number of colors to select.
            as_hex: If True, returns a list of hex strings instead of `Color` objects.
            reverse: If True, samples from the reversed palette.

        Returns:
            A list of `Color` objects or hex strings.
        """
        if n < 0:
            raise ValueError("Number of colors to sample (n) cannot be negative.")
        if n == 0:
            return []

        palette = self.colors[::-1] if reverse else self.colors
        palette_size = len(palette)

        if palette_size == 0:
            return []

        if n > palette_size:
            # Cycle through the palette for requests larger than its size
            selected_colors = list(itertools.islice(itertools.cycle(palette), n))
        else:
            # Select N evenly-spaced indices
            if n == 1:
                # Handle edge case to avoid division by zero
                indices = [0]
            else:
                # The core logic: map the range [0, n-1] to [0, palette_size-1]
                indices = [round(i * (palette_size - 1) / (n - 1)) for i in range(n)]
            selected_colors = [palette[i] for i in indices]

        if as_hex:
            return [color.hex_code for color in selected_colors]
        return selected_colors

    def __len__(self) -> int:
        return len(self.colors)

    def __getitem__(self, index: int) -> Color:
        return self.colors[index]

    def __iter__(self) -> Iterator[Color]:
        return iter(self.colors)


# fmt:off
# --- Palette Registry ---
# Central dictionary holding all available color palettes.
PALETTES: dict[str, ColorPalette] = {

    "qualitative_light": ColorPalette.from_hex_codes([
        '#ff4d4d', '#ff7f50', '#ffff00', '#00ff7f', '#00ffff', '#1e90ff',
        '#9370db', '#ff69b4', '#cd5c5c', '#8fbc8f', '#ffd700', '#32cd32',
        '#00bfff', '#ff00ff', '#ff8c00'
    ]),

    # Diverging Palettes
    "green_yellow_20": ColorPalette.from_hex_codes([
        '#006400', '#0d6a00', '#1a6f01', '#267502', '#337b02', '#408002', '#4c8603',
        '#598c03', '#669204', '#739704', '#809d05', '#8ca306', '#99a806', '#a6ae06',
        '#b2b407', '#bfba08', '#ccbf08', '#d9c508', '#e6cb09', '#f2d00a'
    ]),
    "blue_red_20": ColorPalette.from_hex_codes([
        '#2f00ff', '#3906f8', '#440cf1', '#4e11ea', '#5917e3', '#631ddc', '#6d22d5',
        '#7828ce', '#822ec7', '#8d34c0', '#973ab9', '#a13fb2', '#ac45ab', '#b64ba4',
        '#c1509d', '#cb5696', '#d55c8f', '#e06288', '#ea6881', '#f56d7a'
    ]),
}
# fmt:on
