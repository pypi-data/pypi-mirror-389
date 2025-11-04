import napari
from napari.utils.theme import get_theme, register_theme

CDMA_BLUE = "#004899"
CDMA_ORANGE = "#f59f19"
dark_blue = "#283143"
dark_orange = "#5d431c"
medium_dark_blue = "#334871"
light_blue = "#81a3c9"
white = "#ffffff"
white_blue = "#d0dae7"


def cdma_napari_theme(viewer: napari.Viewer) -> None:
    """Theme for napari with CDMA colors."""
    theme = get_theme("dark")
    theme.id = "cdma"
    theme.canvas = dark_blue
    theme.background = medium_dark_blue
    theme.foreground = dark_blue
    theme.primary = light_blue
    theme.secondary = CDMA_ORANGE
    theme.current = CDMA_ORANGE
    theme.text = white
    theme.highlight = white_blue
    theme.icon = white_blue

    register_theme("cdma", theme, "interactive_reconstruction")
    viewer.theme = "cdma"


def cdma_napari_demo_theme(viewer: napari.Viewer) -> None:
    """Brightly colored theme for napari with CDMA colors."""
    theme = get_theme("dark")
    theme.id = "cdma_demo"
    # theme.canvas = dark_blue
    theme.canvas = white
    theme.background = CDMA_BLUE
    theme.foreground = medium_dark_blue
    theme.primary = light_blue
    theme.secondary = CDMA_ORANGE
    theme.current = CDMA_ORANGE
    theme.text = white
    theme.highlight = white_blue
    theme.icon = white_blue

    register_theme("cdma_demo", theme, "interactive_reconstruction")
    viewer.theme = "cdma_demo"
