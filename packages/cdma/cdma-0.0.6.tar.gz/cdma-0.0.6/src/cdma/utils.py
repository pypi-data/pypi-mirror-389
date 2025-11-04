from itertools import cycle
from typing import Literal

import napari
import numpy as np
import skimage
from matplotlib import pyplot as plt


def image_info(
    stack: np.ndarray,
    hist_downsample_factor: int = 8,
    yscale: Literal["log", "linear"] = "log",
    hist: bool = True,
) -> None:
    """Prints basic information about an image and optionally its histogram.

    Args:
        stack (np.ndarray): Image data.
        hist_downsample_factor (int): Downsample factor for the histogram.
        yscale (str): Scale for the y-axis of the histogram. Default is "log".
        hist (bool): Whether to plot the histogram. Default is True.

    Returns:
        None
    """
    print(f"\t Shape: {stack.shape}")
    print(f"\t Range: {stack.min()}-{stack.max()}")
    print(f"\t Dtype: {stack.dtype}")
    print(f"\t Unique: {np.unique(stack[::hist_downsample_factor]).shape[0]}")
    print(f"\t Memory: {stack.nbytes / 1e9:.2f} GB")

    if not hist:
        return None
    plt.figure()
    plt.hist(stack[::hist_downsample_factor].ravel(), bins=256)
    if yscale == "log":
        plt.yscale("log")
    return None


def show_in_napari(image_stack: np.ndarray, *label_stacks: np.ndarray) -> napari.Viewer:
    """Show an image and labels in napari. Labels must be binary, i.e., 0 for background and 1 for foreground.

    Args:
        image_stack (np.ndarray): Image data.
        label_stacks (np.ndarray): Label data. Can be multiple.

    Returns:
        napari.Viewer: Napari viewer with the image and labels.
    """
    mask_colors = ["red", "green", "blue", "yellow", "magenta", "cyan"]
    viewer = napari.Viewer()
    viewer.add_image(image_stack)
    for color, label_stack in zip(cycle(mask_colors), label_stacks):
        if label_stack is not None:
            viewer.add_labels(label_stack, colormap={1: color})
    return viewer


def rescale_to_unit_interval(
    stack: np.ndarray,
    downsample_factor: int,
    percentiles: tuple[float, float],
    dask_mode: bool = False,
) -> np.ndarray:
    """Stretch the contrast of the image using the percentiles p.

    This removes outliers and groups them together at the ends of the histogram. By default, the percentiles are
    calculated on a downsampled version of the image to speed up the process.

    Args:
        stack (np.array): Image to stretch.
        downsample_factor (int): Factor by which to downsample the image for percentile calculation.
        percentiles (tuple): Percentiles to use for contrast stretching.
        dask_mode (bool): Whether to use dask for percentile calculation. Slower for small images, faster for large ones.
    """
    if stack.ndim != 3:
        raise ValueError("Input stack must be 3D.")
    if stack.dtype != np.float32:
        raise ValueError("Input stack must be float32.")

    if dask_mode:
        import dask.array as da

        stack_dask = da.from_array(stack, chunks="auto")
        p1, p2 = da.nanpercentile(
            stack_dask,
            q=(percentiles[0], percentiles[1]),
        ).compute()
    else:
        if downsample_factor < 1 or stack.shape[0] // downsample_factor < 5:
            raise ValueError(
                "Downsampling factor should not be < 1 or downsample the image to less than 5 pixels in z."
            )
        p1, p2 = np.nanpercentile(
            stack[::downsample_factor, ::downsample_factor, ::downsample_factor],
            q=(percentiles[0], percentiles[1]),
        )
    img_rescale = skimage.exposure.rescale_intensity(
        stack, in_range=(p1, p2), out_range=(0, 1)
    )
    return img_rescale
