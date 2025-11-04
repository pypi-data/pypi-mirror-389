import seaborn as sns

CDMA_BLUE = "#004899"
CDMA_ORANGE = "#f59f19"


def cdma_palette_sequential(
    color: str = "blue", kind: str = "light", as_cmap=False, reverse=True, n_colors=10
):
    """
    Create a sequential color palette with CDMA colors.

    Parameters
    ----------
    color : str
        The base color for the palette. Default is "blue".
    kind : str
        The kind of palette to create. Can be "light" or "dark". Default is "light".
    as_cmap : bool
        If True, return a colormap object. Default is False.
    reverse : bool
        If True, reverse the palette. Default is True.
    n_colors : int
        The number of colors in the palette. Only applies if as_cmap=False. Default is 10.

    Returns
    -------
    list or matplotlib.colors.LinearSegmentedColormap
        A list of colors or a colormap object.
    """
    base_colors = {"blue": "#004899", "orange": "#f59f19"}
    palette_kinds = {"light": sns.light_palette, "dark": sns.dark_palette}
    base_color = base_colors.get(color, "#004899")
    palette_kind = palette_kinds.get(kind, sns.light_palette)
    palette = palette_kind(
        base_color, as_cmap=as_cmap, reverse=reverse, n_colors=n_colors
    )
    return palette


def cdma_palette_diverging(
    reverse=False, as_cmap: bool = False, n_colors: int = 10, kind="light"
):
    """
    Create a diverging color palette for CDMA.

    Parameters
    ----------
    reverse : bool
        If True, start the palette from blue. Default is False.
    as_cmap : bool
        If True, return a colormap object. Default is False.
    n_colors : int
        The number of colors in the palette. Only applies if as_cmap=False. Default is 10.
    kind : str
        The kind of palette to create. Can be "light" or "dark". Default is "light".

    Returns
    -------
    list or matplotlib.colors.LinearSegmentedColormap
        A list of colors or a colormap object.
    """
    if not reverse:
        palette = sns.diverging_palette(
            h_neg=44.39,
            h_pos=256.1,
            s=98,
            l=60,
            sep=1,
            as_cmap=as_cmap,
            n=n_colors,
            center=kind,
        )
    else:
        palette = sns.diverging_palette(
            h_neg=256.1,
            h_pos=44.39,
            s=98.0,
            l=60.0,
            sep=1,
            n=n_colors,
            as_cmap=as_cmap,
            center=kind,
        )
    return palette
