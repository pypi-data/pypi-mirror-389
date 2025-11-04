"""
Utility functions for batch processing.

These functions replace the deprecated pixtreme batch processing functions
that were removed in version 0.8.4.
"""

import cupy as cp
import pixtreme as px


def images_to_batch(
    images: cp.ndarray | list[cp.ndarray],
    mean: float = 0.0,
    std: float = 1.0,
    size: int | tuple[int, int] | None = None,
    swap_rb: bool = False,
    layout: str = "NCHW",
) -> cp.ndarray:
    """
    Convert images to a batch tensor with normalization and layout conversion.

    Args:
        images: Single image or list of images (CuPy arrays)
        mean: Mean value for normalization
        std: Standard deviation for normalization
        size: Target size for resizing. Can be int (for square) or (width, height) tuple. None to keep original size.
        swap_rb: Whether to swap R and B channels
        layout: Target layout ("HWC", "CHW", "NHWC", or "NCHW")

    Returns:
        Batch tensor as CuPy array with shape determined by layout:
        - "NCHW": (N, C, H, W)
        - "NHWC": (N, H, W, C)
        - "CHW": (C, H, W) for single image
        - "HWC": (H, W, C) for single image
    """
    # Convert single image to list
    if isinstance(images, cp.ndarray):
        if images.ndim == 3:
            images = [images]
        elif images.ndim == 4:
            # Already batched
            images = [images[i] for i in range(images.shape[0])]

    # Ensure all images are float32
    images = [px.to_float32(img) if img.dtype != cp.float32 else img for img in images]

    # Resize if needed
    if size is not None:
        # Convert int to tuple (size, size) for square resize
        if isinstance(size, int):
            size = (size, size)
        images = [px.resize(img, size, interpolation=px.INTER_AUTO) for img in images]

    # Swap R and B channels if needed
    if swap_rb:
        images = [img[:, :, ::-1] for img in images]

    # Normalize
    if isinstance(mean, (tuple, list)):
        mean = cp.array(mean, dtype=cp.float32)
    if isinstance(std, (tuple, list)):
        std = cp.array(std, dtype=cp.float32)
    images = [(img - mean) / std for img in images]

    # Convert layout
    if layout.upper() in ["NCHW", "CHW"]:
        # HWC -> CHW: (H, W, C) -> (C, H, W)
        images = [cp.transpose(img, (2, 0, 1)) for img in images]

    # Stack into batch (always include batch dimension for consistency with ONNX/TensorRT)
    return cp.stack(images, axis=0)


def image_to_batch(
    image: cp.ndarray,
    mean: float = 0.0,
    std: float = 1.0,
    size: int | tuple[int, int] | None = None,
    swap_rb: bool = False,
    layout: str = "NCHW",
) -> cp.ndarray:
    """
    Convert a single image to a batch tensor.

    This is a convenience wrapper around images_to_batch for single images.

    Args:
        image: Image as CuPy array
        mean: Mean value for normalization
        std: Standard deviation for normalization
        size: Target size for resizing. Can be int (for square) or (width, height) tuple. None to keep original size.
        swap_rb: Whether to swap R and B channels
        layout: Target layout ("HWC", "CHW", "NHWC", or "NCHW")

    Returns:
        Batch tensor with batch dimension
    """
    batch = images_to_batch([image], mean=mean, std=std, size=size, swap_rb=swap_rb, layout=layout)

    # Ensure batch dimension exists
    if batch.ndim == 3:
        batch = batch[cp.newaxis, ...]

    return batch


def batch_to_images(
    batch: cp.ndarray,
    mean: float = 0.0,
    std: float = 1.0,
    swap_rb: bool = False,
    layout: str = "NCHW",
) -> list[cp.ndarray]:
    """
    Convert a batch tensor to a list of images.

    Args:
        batch: Batch tensor as CuPy array
        mean: Mean value used in normalization (will be reversed)
        std: Standard deviation used in normalization (will be reversed)
        swap_rb: Whether to swap R and B channels
        layout: Input layout ("HWC", "CHW", "NHWC", or "NCHW")

    Returns:
        List of images as CuPy arrays in HWC format (H, W, C)
    """
    # Handle single image (3D tensor)
    if batch.ndim == 3:
        batch = batch[cp.newaxis, ...]

    # Convert layout to NHWC
    if layout.upper() in ["NCHW", "CHW"]:
        # CHW -> HWC: (N, C, H, W) -> (N, H, W, C)
        batch = cp.transpose(batch, (0, 2, 3, 1))

    # Denormalize
    if isinstance(mean, (tuple, list)):
        mean = cp.array(mean, dtype=cp.float32)
    if isinstance(std, (tuple, list)):
        std = cp.array(std, dtype=cp.float32)
    batch = batch * std + mean

    # Clip to valid range
    batch = cp.clip(batch, 0.0, 1.0)

    # Swap R and B channels if needed
    if swap_rb:
        batch = batch[:, :, :, ::-1]

    # Split batch into list of images
    images = [batch[i] for i in range(batch.shape[0])]

    return images
