from __future__ import annotations

import os
import pathlib
import time

import dask.array.image
import joblib
import numpy as np
import skimage.io


def load_stack(
    path: str | pathlib.Path,
    suffix: str = "tif",
    image_range: tuple[int, int, int] | None = None,
    verbose: int = 0,
    dask_mode: bool = True,
) -> np.ndarray:
    """Loads a stack of images from a folder and returns them as a numpy array.

    It is possible to only load a subset of the images by specifying the image_range as (start, stop, step).
    The verbose parameter can be used to print information about the loading process, like time and memory usage.


    Args:
        path (str): Path to the folder containing the images.
        suffix (str): File extension of the images.
        image_range (tuple): Range of images to load.
        verbose (int): If >0, prints information about the loading process.
        dask_mode (bool): If True, use dask.array.image to load the images.

    Returns:
        np.ndarray: 3D array containing the images.

    Raises:
        ValueError: If no images are found in the folder."""
    if dask_mode:
        start = time.time()
        verbose > 0 and print("Loading images from: ", path, "...")
        if path[-1] != "/":
            path = path + "/"
        stack = dask.array.image.imread(path.__str__() + "*" + suffix).compute()
        verbose and print(
            "Loaded stack with shape {} and a size of {:.2f} GB in {:.2f} s.".format(
                stack.shape, stack.nbytes / 1e9, time.time() - start
            )
        )
        return stack
    start = time.time()
    verbose > 0 and print("Loading images from: ", path, "...")
    files = [
        os.path.join(path, file) for file in os.listdir(path) if file.endswith(suffix)
    ]
    if len(files) == 0:
        raise ValueError(
            "No images found in path '{}' matching the given extension.".format(path)
        )
    if image_range is None:
        image_range = (0, len(files), 1)
    imgs = skimage.io.imread_collection(
        files[image_range[0] : image_range[1] : image_range[2]]
    )
    stack = np.array(imgs)
    if verbose:
        print(
            "Loaded stack with shape {} and a size of {:.2f} GB in {:.2f} s.".format(
                stack.shape, stack.nbytes / 1e9, time.time() - start
            )
        )
    return stack


def save_stack(
    stack: np.ndarray,
    path: str | pathlib.Path,
    suffix: str = ".tiff",
    filenames: list[str] | None = None,
    overwrite: bool = True,
    dtype: np.dtype | None = None,
    multithread: bool = True,
    verbose: bool = True,
) -> None:
    """Saves a stack of images to a folder.

    Args:
        stack (np.ndarray): Stack of images.
        path (str): Path to the folder where the images will be saved.
        suffix (str): File extension of the images. Default is ".tiff".
        filenames (list[str]): List of filenames to save the images with. If None, the images will be saved as
                    sliceXXXX.png or sliceXXXX.tif.
        multithread (bool): If True, save images in parallel.
        verbose (bool): If True, prints information about the saving process.
        overwrite (bool): If True, overwrites existing files in the folder. Default is True.
        dtype (np.dtype): If specified, the stack will be converted to this dtype before saving. Default is None.

    Raises:
        ValueError: If the input stack is not a 3D numpy array.
        RuntimeError: If saving to .png and the image is not in uint8 or uint16 format.
        RuntimeError: If dtype is specified and the image is not in the range [0, 1].

    Examples:
        >>> import numpy as np
        >>> from cdma.io import save_stack
        >>> stack = np.random.rand(10, 256, 256)  # Example stack of 10 images
        >>> save_stack(stack, path="output_images", suffix=".png", dtype=np.uint8)


    """

    def save_im(im, filename, func=None) -> None:
        """Use skimage.io to single images."""
        if func is None:
            skimage.io.imsave(filename, im, check_contrast=False)
        else:
            skimage.io.imsave(filename, func(im), check_contrast=False)

    start_time = time.time()
    # Validate inputs
    if stack.ndim != 3 or not isinstance(stack, np.ndarray):
        raise ValueError("Input stack must be a 3D numpy array.")

    if suffix == ".png" and stack.dtype not in [np.uint8, np.uint16] and dtype is None:
        raise RuntimeError(
            "Saving to .png requires the image to be in uint8 or uint16 format."
            " Consider specifying a dtype."
        )

    # Determine the saving function based on dtype
    if dtype is not None:
        supported_dtypes = [np.uint8, np.uint16, "uint8", "uint16"]
        if dtype not in supported_dtypes:
            NotImplementedError(
                f"Unsupported dtype {dtype}. Specify either of {supported_dtypes}."
            )
        if stack.min() < 0 or stack.max() > 1:
            RuntimeError(
                "When specifying a dtype, the image must be in the range [0, 1]. Consider normalizing or stretching the contrast first."
            )
        if dtype == np.uint8 or dtype == "uint8":
            save_func = float_to_uint8
        elif dtype == np.uint16 or dtype == "uint16":
            save_func = float_to_uint16
        else:
            RuntimeError("What happened?")
    else:
        save_func = None

    # Set up the directory and filenames
    max_cores = (
        joblib.cpu_count() // 2
    )  # limit cores (for hyperthreading reasons? Testing needed)
    path = pathlib.Path(path)

    if verbose:
        print(f"Saving stack to: {path}")
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    if overwrite:
        files_in_folder = list(path.glob(f"*{suffix}"))
        for file in files_in_folder:
            file.unlink(missing_ok=True)

    if filenames is None:
        filenames = [
            path / pathlib.Path("slice{:04d}{:s}".format(i, suffix))
            for i in range(stack.shape[0])
        ]

    # Save in parallel
    if multithread:
        tasks = [
            joblib.delayed(save_im)(im, filename, save_func)
            for im, filename in zip(stack, filenames)
        ]
        joblib.Parallel(n_jobs=max_cores, backend="threading")(tasks)
    else:
        for im, filename in zip(stack, filenames):
            save_im(im, filename, save_func)
    if verbose:
        print(
            f"Finished saving {len(filenames)} slices in {time.time() - start_time:.2f} s."
        )


def float_to_uint8(im: np.ndarray) -> np.ndarray:
    """Convert a float image with range [0, 1] to uint8."""
    return (im * (2**8 - 1)).astype(np.uint8)


def float_to_uint16(im: np.ndarray) -> np.ndarray:
    """Convert a float image with range [0, 1] to uint16."""
    return (im * (2**16 - 1)).astype(np.uint16)
