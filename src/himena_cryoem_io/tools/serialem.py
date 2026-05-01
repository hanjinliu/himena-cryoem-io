from pathlib import Path
import numpy as np
from himena import Parametric, StandardType
from himena.types import WidgetDataModel
from himena.plugins import register_function, configure_gui

from himena_cryoem_io.consts import MenuId
from himena_cryoem_io._utils import tile_montage


@register_function(
    types=[StandardType.IMAGE],
    menus=[MenuId.SERIALEM],
    title="Open Image As Montage",
    command_id="himena-cryoem-io:serialem:open-image-as-montage",
    run_async=True,
)
def open_image_as_montage(model: WidgetDataModel) -> Parametric:
    """Open the image as a montage based on the current navigator item."""
    import mdocfile

    if not isinstance(source := model.source, Path):
        raise ValueError("Model source must be a Path.")
    if not isinstance(image_stack := model.value, np.ndarray):
        raise ValueError("Model value must be a numpy array.")
    mdoc_path = source.with_name(source.name + ".mdoc")
    if not mdoc_path.exists():
        raise FileNotFoundError(f"mdoc file not found: {mdoc_path}")

    mdoc = mdocfile.read(mdoc_path)

    @configure_gui
    def run(align: bool = True) -> WidgetDataModel:
        image_montage = tile_montage(image_stack, mdoc, align=align)
        return WidgetDataModel(
            value=image_montage,
            type=StandardType.IMAGE,
            title=f"{source.stem} Montage",
        )

    return run
