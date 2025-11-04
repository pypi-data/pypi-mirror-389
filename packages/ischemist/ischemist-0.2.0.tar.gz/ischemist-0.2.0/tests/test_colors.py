import pytest

from ischemist.colors import Color, ColorPalette


@pytest.fixture
def ten_color_palette() -> ColorPalette:
    """A palette with 10 distinct, easily identifiable colors."""
    hex_codes = [f"#0{i}0000" for i in range(10)]  # #000000, #010000, ..., #090000
    return ColorPalette.from_hex_codes(hex_codes)


@pytest.fixture
def three_color_palette() -> ColorPalette:
    """A small palette for testing cycling."""
    return ColorPalette.from_hex_codes(["#ff0000", "#00ff00", "#0000ff"])


def test_sample_even_distribution(ten_color_palette: ColorPalette):
    """Test if sampling fewer colors than available selects evenly spaced ones."""
    # Request 4 colors from a 10-color palette.
    # Expected indices: round(0*9/3)=0, round(1*9/3)=3, round(2*9/3)=6, round(3*9/3)=9
    result = ten_color_palette.sample(4, as_hex=True)
    expected = ["#000000", "#030000", "#060000", "#090000"]
    assert result == expected


def test_sample_exact_size(ten_color_palette: ColorPalette):
    """Test if sampling the exact size returns the whole palette."""
    result = ten_color_palette.sample(10, as_hex=True)
    assert len(result) == 10
    assert result == [str(c) for c in ten_color_palette.colors]


def test_sample_oversample_cycles(three_color_palette: ColorPalette):
    """Test if oversampling cycles through the palette."""
    # Request 5 colors from a 3-color palette
    result = three_color_palette.sample(5, as_hex=True)
    expected = ["#ff0000", "#00ff00", "#0000ff", "#ff0000", "#00ff00"]
    assert result == expected


def test_sample_n_zero_returns_empty(ten_color_palette: ColorPalette):
    """Test if requesting 0 colors returns an empty list."""
    assert ten_color_palette.sample(0) == []


def test_sample_n_one_returns_first_color(ten_color_palette: ColorPalette):
    """Test if requesting 1 color returns the first element."""
    result = ten_color_palette.sample(1)
    assert len(result) == 1
    assert result[0] == ten_color_palette[0]


def test_sample_from_empty_palette():
    """Test that sampling from an empty palette returns an empty list."""
    empty_palette = ColorPalette.from_hex_codes([])
    assert empty_palette.sample(5) == []


def test_sample_as_hex_parameter(three_color_palette: ColorPalette):
    """Test the `as_hex` flag to ensure correct return types."""
    result_hex = three_color_palette.sample(2, as_hex=True)
    assert isinstance(result_hex[0], str)
    assert result_hex[0].startswith("#")

    result_color = three_color_palette.sample(2, as_hex=False)
    assert isinstance(result_color[0], Color)


def test_sample_reverse_parameter(ten_color_palette: ColorPalette):
    """Test if the `reverse` flag samples from the end of the palette."""
    # Request 4 colors from a 10-color palette, reversed
    result = ten_color_palette.sample(4, reverse=True, as_hex=True)
    # The palette is reversed, so we sample from [#090000, ..., #000000]
    # Indices are still 0, 3, 6, 9 on the *reversed* list
    expected = ["#090000", "#060000", "#030000", "#000000"]
    assert result == expected


# This is the core logic we need to test: `round(i * (palette_size - 1) / (n - 1))`
@pytest.mark.parametrize(
    "palette_size, n_to_sample, expected_indices",
    [
        # The user's "not so clean" example: 10 colors, sample 4.
        # Step is (10-1)/(4-1) = 3.0. Clean division.
        (10, 4, [0, 3, 6, 9]),
        # The user's second example: 10 colors, sample 6.
        # Step is (10-1)/(6-1) = 1.8. This is the key test case for rounding.
        # Indices: 0*1.8=0, 1*1.8=1.8->2, 2*1.8=3.6->4, 3*1.8=5.4->5, 4*1.8=7.2->7, 5*1.8=9
        (10, 6, [0, 2, 4, 5, 7, 9]),
        # A case where rounding .5 comes into play.
        # Step is (8-1)/(7-1) = 7/6 ≈ 1.167.
        # At i=3, index is 3 * 1.167 = 3.5, which rounds to 4.
        (8, 7, [0, 1, 2, 4, 5, 6, 7]),
        # Sampling the full palette should yield all indices.
        (5, 5, [0, 1, 2, 3, 4]),
        # Sampling a prime number from a non-multiple.
        # Step is (12-1)/(5-1) = 11/4 = 2.75
        # Indices: 0, 2.75->3, 5.5->6, 8.25->8, 11
        (12, 5, [0, 3, 6, 8, 11]),
        # Sampling 2 should always give the first and last.
        (20, 2, [0, 19]),
    ],
)
def test_sample_distribution_logic_parameterized(palette_size, n_to_sample, expected_indices):
    """
    Rigorously tests the index selection logic for various non-trivial cases
    where n <= palette_size.
    """
    # Create a dummy palette for testing index selection
    # Using the index in the hex code makes debugging easy, e.g., #00000a is color 10
    hex_codes = [f"#{i:06x}" for i in range(palette_size)]
    palette = ColorPalette.from_hex_codes(hex_codes)

    # The actual colors we expect based on the calculated indices
    expected_colors = [hex_codes[i] for i in expected_indices]

    result = palette.sample(n_to_sample, as_hex=True)
    assert result == expected_colors, (
        f"Failed for palette_size={palette_size}, n_to_sample={n_to_sample}. "
        f"Expected indices {expected_indices} but got different colors."
    )


@pytest.mark.parametrize(
    "palette_size, n_to_sample, expected_pattern",
    [
        # Basic oversampling
        (3, 5, ["c0", "c1", "c2", "c0", "c1"]),
        # Oversampling by exactly one full cycle
        (4, 8, ["c0", "c1", "c2", "c3", "c0", "c1", "c2", "c3"]),
        # Oversampling a small palette by a large amount
        (2, 7, ["c0", "c1", "c0", "c1", "c0", "c1", "c0"]),
    ],
)
def test_sample_cycling_logic_parameterized(palette_size, n_to_sample, expected_pattern):
    """
    Tests the cycling logic for various cases where n > palette_size.
    """
    # Use simple strings for dummy hex codes to make patterns obvious
    hex_codes = [f"#{c}0000" for c in expected_pattern[:palette_size]]  # e.g., ['#c0', '#c1', '#c2']
    palette = ColorPalette.from_hex_codes(hex_codes)

    expected_colors = [f"#{c}0000" for c in expected_pattern]

    result = palette.sample(n_to_sample, as_hex=True)
    assert result == expected_colors
