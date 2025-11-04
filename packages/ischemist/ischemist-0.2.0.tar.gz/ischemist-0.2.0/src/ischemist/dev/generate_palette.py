"""
A developer script for generating high-quality, perceptually uniform color palettes.

This is not part of the installable package but a tool for development.
It uses the `coloraide` library to perform interpolations in the Oklab colorspace,
which is designed for perceptual uniformity.

Why Oklab?
  - Linear interpolation in RGB space creates "muddy" mid-tones and uneven
    perceptual steps.
  - Oklab is a modern colorspace where geometric distance between colors
    corresponds closely to perceived difference, making gradients smooth
    and aesthetically pleasing.

Usage:
  - Run this script directly: `python -m ischemist.dev.palette_generator`
  - Modify the `if __name__ == "__main__"` block to generate new palettes.
  - Copy the printed output into the `PALETTES` dictionary in `ischemist/style/colors.py`.
"""

from coloraide import Color

# --- Core Generator Functions ---


def generate_palette(
    colors: list[str],
    n_points: int,
    space: str = "oklab",
) -> list[str]:
    """
    Generates a palette by interpolating between a series of colors.

    Args:
        colors: A list of two or more hex color strings to define the gradient segments.
        n_points: The total number of colors in the final palette.
        space: The colorspace to perform interpolation in. "oklab" is recommended.

    Returns:
        A list of hex color codes.
    """
    palette = Color.interpolate(colors, space=space)
    return [palette(i / (n_points - 1)).convert("srgb").to_string(hex=True) for i in range(n_points)]


def generate_pastel_palette(n_points: int, lightness: float = 0.9, chroma: float = 0.1) -> list[str]:
    """
    Generates a pastel palette by rotating the hue at a fixed lightness and chroma.

    Args:
        n_points: The number of colors to generate.
        lightness: Oklch lightness value (0-1). Pastels are high, e.g., 0.85-0.95.
        chroma: Oklch chroma value (saturation). Pastels are low, e.g., 0.05-0.15.

    Returns:
        A list of hex color codes.
    """
    colors = []
    for i in range(n_points):
        hue = i * (360 / n_points)
        # Create the color directly in the oklch space
        pastel_color = Color("oklch", [lightness, chroma, hue])
        # Convert to srgb (for display) and then to a hex string
        colors.append(pastel_color.convert("srgb").to_string(hex=True))
    return colors


def print_palette_for_registry(name: str, colors: list[str]):
    """Formats the output for easy copy-pasting."""
    print(f'    "{name}": ColorPalette.from_hex_codes([')

    # Print in rows of 8 for readability
    for i in range(0, len(colors), 10):
        chunk = colors[i : i + 10]
        formatted_chunk = ", ".join(f'"{c}"' for c in chunk)
        print(f"        {formatted_chunk},")
    print("    ]),")
