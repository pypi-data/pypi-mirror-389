import numpy as np
import skimage.draw


def create_fake_stack(
    shape=(2048, 2048, 2048),  # shape is (z, y, x)
    angles_xy=(10, -5),
    center_offset_xy: tuple[int, int] = (0, 0),
    radius_scale=0.5,
    cylinder_value=-200,
    cylinder_noise=0.15,
    background_value=100,
    background_noise=0.3,
):
    stack = (
        np.full(shape, fill_value=background_value, dtype=np.float32)
        + np.random.randn(*shape) * background_noise * background_value
    )
    n_slices = shape[0]
    centers_x, centers_y = (
        np.ones(n_slices) * shape[2] // 2 + center_offset_xy[0],
        np.ones(n_slices) * shape[1] // 2 + center_offset_xy[1],
    )
    # calculate the center coordinates for the individual disks in their respective slice
    radius = int(shape[2] // 2 * radius_scale)
    centers_x, centers_y = (
        (
            centers_x
            + np.tan(angles_xy[0] / 180 * np.pi)
            * np.arange(-shape[0] // 2, shape[0] // 2)
        ).astype(np.int32),
        (
            centers_y
            + np.tan(angles_xy[1] / 180 * np.pi)
            * np.arange(-shape[0] // 2, shape[0] // 2)
        ).astype(np.int32),
    )
    # on every slice in the stack, place a circle at coordinates centers_x, centers_y with radius `radius`
    for ii in range(n_slices):
        mask = skimage.draw.disk(
            center=(centers_x[ii], centers_y[ii]), radius=radius, shape=shape[1:]
        )
        stack[ii, *mask] = (
            cylinder_value
            + np.random.randn(mask[0].shape[0]) * cylinder_value * cylinder_noise
        )

    return stack
