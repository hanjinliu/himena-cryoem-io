from __future__ import annotations

from typing import TYPE_CHECKING
import warnings
import numpy as np

if TYPE_CHECKING:
    import pandas as pd


def tile_montage(img: np.ndarray, mdoc: pd.DataFrame, align: bool) -> np.ndarray:
    """Tile the image stack as a montage based on the mdoc file."""
    mont_xmin, mont_ymin = 0, 0
    mont_xmax, mont_ymax = 0, 0
    image_size_y, image_size_x = img.shape[1:]
    if align:
        if "AlignedPieceCoordsVS" in mdoc.columns:
            colname = "AlignedPieceCoordsVS"
        elif "AlignedPieceCoords" in mdoc.columns:
            colname = "AlignedPieceCoords"
        else:
            warnings.warn(
                "No aligned coordinates found in mdoc file. Falling back to unaligned "
                "coordinates.",
                UserWarning,
                stacklevel=2,
            )
            colname = "PieceCoordinates"
    else:
        colname = "PieceCoordinates"
    # first, determine the montage shape
    for coords in mdoc[colname]:
        if coords is None:
            continue
        mont_xmax = int(max(mont_xmax, coords[0] + image_size_x))
        mont_ymax = int(max(mont_ymax, coords[1] + image_size_y))
        mont_xmin = int(min(mont_xmin, coords[0]))
        mont_ymin = int(min(mont_ymin, coords[1]))
    img_montage = np.zeros(
        (mont_ymax - mont_ymin, mont_xmax - mont_xmin), dtype=np.uint8
    )
    i_min, i_max = _quick_clim(img)
    for zvalue, coords in zip(mdoc["ZValue"], mdoc[colname]):
        if coords is None:
            continue
        y = int(coords[1]) - mont_ymin
        x = int(coords[0]) - mont_xmin
        img_slice = np.clip(img[int(zvalue)], i_min, i_max)
        img_u8 = ((img_slice - i_min) / (i_max - i_min) * 255).astype(np.uint8)
        img_montage[y : y + image_size_y, x : x + image_size_x] = img_u8
    return img_montage


def _quick_clim(img: np.ndarray) -> tuple[int, int]:
    img_sub = img[..., ::8]
    return tuple(np.quantile(img_sub, [0.01, 0.999]))
