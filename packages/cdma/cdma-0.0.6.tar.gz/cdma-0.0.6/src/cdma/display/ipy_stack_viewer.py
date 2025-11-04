import abc
from io import BytesIO

import numpy as np
import skimage.color
from IPython.display import display
from ipywidgets import GridspecLayout, IntSlider, Layout, widgets
from PIL import Image
from skimage.exposure import rescale_intensity


class BaseViewer(abc.ABC):
    """Abstract base class for viewers.

    The API takes inspiration from napari."""

    def __init__(self):
        super().__init__()

    @abc.abstractmethod
    def show(self):
        pass

    @abc.abstractmethod
    def add_image(self, image):
        pass

    @abc.abstractmethod
    def add_mask(self, mask):
        pass


class NapariViewer(BaseViewer):
    def __init__(self):
        super().__init__()
        try:
            import napari
        except ImportError:
            raise ImportError(
                "Napari is not installed. Please install it to use NapariViewer."
            )
        self.viewer = napari.Viewer()

    def add_image(self, image):
        self.viewer.add_image(image)

    def add_mask(self, mask):
        self.viewer.add_labels(mask)

    def show(self):
        import napari

        napari.run()


class IPyViewer(BaseViewer):
    def __init__(self, scale=1):
        super().__init__()
        self.image = None
        self.masks = []  # List of (mask, transparency)
        self.scale = scale
        self.image_size = 300 * scale
        self.gap = 10 * scale
        self.current_x_slice = None
        self.current_y_slice = None
        self.current_z_slice = None
        self.layout = None
        self.z_slider = None
        self.y_slider = None
        self.x_slider = None
        self.z_slice_image = None
        self.y_slice_image = None
        self.x_slice_image = None

    def add_image(self, image):
        if image.ndim == 2:
            image = image[np.newaxis, :, :]
        if image.ndim != 3:
            raise ValueError("Input image must be 2D or 3D numpy array.")
        image = self._rescale_stack(image)
        self.image = image
        self.z_size, self.y_size, self.x_size = image.shape
        self.current_x_slice = self.x_size // 2
        self.current_y_slice = self.y_size // 2
        self.current_z_slice = self.z_size // 2
        self.init_layout()

    def add_mask(self, mask, transparency=0.5):
        mask = self._rescale_stack(mask)
        self.masks.append((mask, transparency))

    def show(self):
        display(self.layout)

    def init_layout(self):
        self.z_slider = IntSlider(
            value=self.current_z_slice,
            min=0,
            max=self.z_size - 1,
            step=1,
            description="Z Slice",
        )
        self.y_slider = IntSlider(
            value=self.current_y_slice,
            min=0,
            max=self.y_size - 1,
            step=1,
            description="Y Slice",
        )
        self.x_slider = IntSlider(
            value=self.current_x_slice,
            min=0,
            max=self.x_size - 1,
            step=1,
            description="X Slice",
        )
        self.z_slice_image = widgets.Image(
            value=self.prep_image_z(self.current_z_slice),
            format="png",
            layout=Layout(height=f"{self.image_size}px"),
        )
        self.y_slice_image = widgets.Image(
            value=self.prep_image_y(self.current_y_slice),
            format="png",
            layout=Layout(height=f"{self.image_size}px"),
        )
        self.x_slice_image = widgets.Image(
            value=self.prep_image_x(self.current_x_slice),
            format="png",
            layout=Layout(height=f"{self.image_size}px"),
        )
        gl = GridspecLayout(
            2,
            3,
            height=f"{self.image_size + 10 * self.gap}px",
            width=f"{self.image_size * 3 + 5 * self.gap}px",
            align_items="center",
            justify="center",
            grid_gap=f"{self.gap}px",
        )
        gl[0, 0] = self.z_slice_image
        gl[0, 1] = self.y_slice_image
        gl[0, 2] = self.x_slice_image
        gl[1, 0] = self.z_slider
        gl[1, 1] = self.y_slider
        gl[1, 2] = self.x_slider
        self.x_slider.observe(
            lambda change: self.update_x_slice(change["new"]), names="value"
        )
        self.y_slider.observe(
            lambda change: self.update_y_slice(change["new"]), names="value"
        )
        self.z_slider.observe(
            lambda change: self.update_z_slice(change["new"]), names="value"
        )
        self.layout = gl

    def update_x_slice(self, slice_idx):
        self.current_x_slice = slice_idx
        self.update_slices()

    def update_y_slice(self, slice_idx):
        self.current_y_slice = slice_idx
        self.update_slices()

    def update_z_slice(self, slice_idx):
        self.current_z_slice = slice_idx
        self.update_slices()

    def update_slices(self):
        self.x_slice_image.value = self.prep_image_x(self.current_x_slice)
        self.y_slice_image.value = self.prep_image_y(self.current_y_slice)
        self.z_slice_image.value = self.prep_image_z(self.current_z_slice)

    def blend_masks(self, base_slice, mask_slices):
        blended = base_slice.astype(np.float32) / 255.0
        for mask, alpha in mask_slices:
            mask_bin = (mask > 0).astype(np.float32)
            mask_rgb = np.stack(
                [mask_bin, np.zeros_like(mask_bin), np.zeros_like(mask_bin)], axis=-1
            )
            blended = blended * (1 - alpha * mask_bin[..., None]) + mask_rgb * (
                alpha * mask_bin[..., None]
            )
        blended = (blended * 255).astype(np.uint8)
        return blended

    def prep_image_x(self, slice_idx):
        if self.image is None:
            return b""
        base_slice = skimage.color.gray2rgb(self.image[:, :, slice_idx])
        mask_slices = [(mask[:, :, slice_idx], alpha) for mask, alpha in self.masks]
        if mask_slices:
            base_slice = self.blend_masks(base_slice, mask_slices)
        base_slice[:, self.current_y_slice, :] = [0, 255, 0]
        base_slice[self.current_z_slice, :, :] = [0, 0, 255]
        padded = self.pad_to_square(base_slice)
        return self.arr2mem_repr(padded)

    def prep_image_y(self, slice_idx):
        if self.image is None:
            return b""
        base_slice = skimage.color.gray2rgb(self.image[:, slice_idx, :])
        mask_slices = [(mask[:, slice_idx, :], alpha) for mask, alpha in self.masks]
        if mask_slices:
            base_slice = self.blend_masks(base_slice, mask_slices)
        base_slice[:, self.current_x_slice, :] = [255, 0, 0]
        base_slice[self.current_z_slice, :, :] = [0, 0, 255]
        padded = self.pad_to_square(base_slice)
        return self.arr2mem_repr(padded)

    def prep_image_z(self, slice_idx):
        if self.image is None:
            return b""
        base_slice = skimage.color.gray2rgb(self.image[slice_idx, :, :])
        mask_slices = [(mask[slice_idx, :, :], alpha) for mask, alpha in self.masks]
        if mask_slices:
            base_slice = self.blend_masks(base_slice, mask_slices)
        base_slice[:, self.current_x_slice, :] = [255, 0, 0]
        base_slice[:, self.current_y_slice, :] = [0, 255, 0]
        padded = self.pad_to_square(base_slice)
        return self.arr2mem_repr(padded)

    @staticmethod
    def pad_to_square(arr):
        max_dim = max(arr.shape[:2])
        padded = np.zeros((max_dim, max_dim, 3), dtype=arr.dtype)
        start_x = (max_dim - arr.shape[0]) // 2
        start_y = (max_dim - arr.shape[1]) // 2
        padded[
            start_x : start_x + arr.shape[0], start_y : start_y + arr.shape[1], :
        ] = arr
        return padded

    @staticmethod
    def arr2mem_repr(arr):
        image = Image.fromarray(arr)
        imgBytes = BytesIO()
        image.save(imgBytes, format="png")
        mem_repr = imgBytes.getvalue()
        return mem_repr

    @staticmethod
    def _rescale_stack(arr):
        arr = rescale_intensity(arr.copy(), out_range=(0, 2**8 - 1))
        arr = arr.astype(np.uint8)
        return arr


class StackViewer:
    def __init__(self, stack, scale=1):
        self.stack = self._rescale_stack(stack)
        self.z_size, self.y_size, self.x_size = stack.shape
        self.scale = scale
        self.image_size = 300 * scale
        self.gap = 10 * scale
        self.current_x_slice, self.current_y_slice, self.current_z_slice = (
            self.x_size // 2,
            self.y_size // 2,
            self.z_size // 2,
        )
        self.layout = None
        self.z_slider = None
        self.y_slider = None
        self.x_slider = None
        self.z_slice_image = None
        self.y_slice_image = None
        self.x_slice_image = None

        self.init_layout()

    def init_layout(self):
        self.z_slider = IntSlider(
            value=self.z_size // 2,
            min=0,
            max=self.z_size - 1,
            step=1,
            description="Z Slice",
        )
        self.y_slider = IntSlider(
            value=self.y_size // 2,
            min=0,
            max=self.y_size - 1,
            step=1,
            description="Y Slice",
        )
        self.x_slider = IntSlider(
            value=self.x_size // 2,
            min=0,
            max=self.x_size - 1,
            step=1,
            description="X Slice",
        )
        self.z_slice_image = widgets.Image(
            value=self.prep_image_z(self.current_z_slice),
            format="png",
            layout=Layout(height=f"{self.image_size}px"),
        )
        self.y_slice_image = widgets.Image(
            value=self.prep_image_y(self.current_y_slice),
            format="png",
            layout=Layout(height=f"{self.image_size}px"),
        )
        self.x_slice_image = widgets.Image(
            value=self.prep_image_x(self.current_x_slice),
            format="png",
            layout=Layout(height=f"{self.image_size}px"),
        )
        gl = GridspecLayout(
            2,
            3,
            height=f"{self.image_size + 10 * self.gap}px",
            width=f"{self.image_size * 3 + 5 * self.gap}px",
            align_items="center",
            justify="center",
            grid_gap=f"{self.gap}px",
        )
        gl[0, 0] = self.z_slice_image
        gl[0, 1] = self.y_slice_image
        gl[0, 2] = self.x_slice_image
        gl[1, 0] = self.z_slider
        gl[1, 1] = self.y_slider
        gl[1, 2] = self.x_slider
        self.x_slider.observe(
            lambda change: self.update_x_slice(change["new"]), names="value"
        )
        self.y_slider.observe(
            lambda change: self.update_y_slice(change["new"]), names="value"
        )
        self.z_slider.observe(
            lambda change: self.update_z_slice(change["new"]), names="value"
        )
        self.layout = gl

    def show(self):
        display(self.layout)

    def update_x_slice(self, slice_idx):
        self.current_x_slice = slice_idx
        self.update_slices()

    def update_slices(self):
        self.x_slice_image.value = self.prep_image_x(self.current_x_slice)
        self.y_slice_image.value = self.prep_image_y(self.current_y_slice)
        self.z_slice_image.value = self.prep_image_z(self.current_z_slice)

    def update_y_slice(self, slice_idx):
        self.current_y_slice = slice_idx
        self.update_slices()

    def update_z_slice(self, slice_idx):
        self.current_z_slice = slice_idx
        self.update_slices()

    def prep_image_x(self, slice_idx):
        slice = self.stack[:, :, slice_idx]
        slice_rgb = skimage.color.gray2rgb(slice)
        # add cross-section lines for the other slices
        slice_rgb[:, self.current_y_slice, :] = [0, 255, 0]
        slice_rgb[self.current_z_slice, :, :] = [0, 0, 255]
        padded = self.pad_to_square(slice_rgb)
        mem_repr = self.arr2mem_repr(padded)
        return mem_repr

    def prep_image_y(self, slice_idx):
        slice = self.stack[:, slice_idx, :]
        slice_rgb = skimage.color.gray2rgb(slice)
        # add cross-section lines for the other slices
        slice_rgb[:, self.current_x_slice, :] = [255, 0, 0]
        slice_rgb[self.current_z_slice, :, :] = [0, 0, 255]
        padded = self.pad_to_square(slice_rgb)
        mem_repr = self.arr2mem_repr(padded)
        return mem_repr

    def prep_image_z(self, slice_idx):
        slice = self.stack[slice_idx, :, :]
        slice_rgb = skimage.color.gray2rgb(slice)
        # add cross-section lines for the other slices
        slice_rgb[:, self.current_x_slice, :] = [255, 0, 0]
        slice_rgb[self.current_y_slice, :, :] = [0, 255, 0]
        padded = self.pad_to_square(slice_rgb)
        mem_repr = self.arr2mem_repr(padded)
        return mem_repr

    @staticmethod
    def pad_to_square(arr):
        max_dim = max(arr.shape[:2])
        padded = np.zeros((max_dim, max_dim, 3), dtype=arr.dtype)
        start_x = (max_dim - arr.shape[0]) // 2
        start_y = (max_dim - arr.shape[1]) // 2
        padded[
            start_x : start_x + arr.shape[0], start_y : start_y + arr.shape[1], :
        ] = arr
        return padded

    @staticmethod
    def arr2mem_repr(arr):
        image = Image.fromarray(arr)
        imgBytes = BytesIO()
        image.save(imgBytes, format="png")
        mem_repr = imgBytes.getvalue()
        return mem_repr

    @staticmethod
    def _rescale_stack(arr):
        arr = rescale_intensity(arr.copy(), out_range=(0, 2**8 - 1))
        arr = arr.astype(np.uint8)
        return arr
