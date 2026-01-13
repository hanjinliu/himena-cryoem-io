from __future__ import annotations

from pathlib import Path
import numpy as np
from himena import StandardType, WidgetDataModel
from himena.standards.model_meta import TextMeta
from himena.plugins import register_reader_plugin, register_writer_plugin
from himena.data_wrappers import wrap_dataframe
from himena_cryoem_io.consts import Type
from himena_cryoem_io import widgets

del widgets  # reading nav always needs the widget.


@register_reader_plugin
def read_star(path: Path):
    """Read a star file as a dictionary of dataframes."""
    return WidgetDataModel(
        value=path.read_text(),
        type=Type.STAR,
    )


@read_star.define_matcher
def _(path: Path):
    if path.suffix == ".star":
        return Type.STAR
    return None


@register_writer_plugin
def write_star(path: Path, model: WidgetDataModel):
    return path.write_text(model.value)


@write_star.define_matcher
def _(model: WidgetDataModel, path: Path):
    type_ok = model.type in {
        StandardType.EXCEL,
        StandardType.DATAFRAMES,
        StandardType.TABLE,
        StandardType.DATAFRAME,
    }
    ext_ok = path.suffix == ".star"
    return type_ok and ext_ok


@register_reader_plugin
def read_mod(path: Path):
    import imodmodel

    imod = imodmodel.ImodModel.from_file(path)
    return WidgetDataModel(value=imod, type=Type.IMOD_MODEL)


@read_mod.define_matcher
def _(path: Path):
    if path.suffix == ".mod":
        return Type.IMOD_MODEL
    return None


@register_writer_plugin
def write_mod(path: Path, data: WidgetDataModel):
    import imodmodel

    if isinstance(imod := data.value, imodmodel.ImodModel):
        imod.to_file(path)
    else:
        raise TypeError(f"Expected imodmodel.ImodModel, got {type(imod)}")


@write_mod.define_matcher
def _(model: WidgetDataModel, path: Path):
    return model.is_subtype_of(Type.IMOD_MODEL) and path.suffix == ".mod"


@register_reader_plugin
def read_cs(path: Path):
    """Read the cryosparc cs file."""
    arr = np.load(path)
    return WidgetDataModel(value=arr, type=StandardType.ARRAY)


@read_cs.define_matcher
def _(path: Path):
    if path.suffix == ".cs":
        return StandardType.ARRAY
    return None


@register_writer_plugin
def write_cs(path: Path, model: WidgetDataModel):
    """Write a structured array to a cryosparc cs file."""
    return np.save(path, model.value)


@write_cs.define_matcher
def _(model: WidgetDataModel, path: Path):
    return model.type == StandardType.ARRAY and path.suffix == ".cs"


@register_reader_plugin
def read_csg(path: Path):
    """Read the cryosparc csg file."""
    # csg is just a yaml file.
    # TODO: read other files in the same directory.
    return WidgetDataModel(
        value=path.read_text(), type="text.csg", metadata=TextMeta(language="YAML")
    )


@read_csg.define_matcher
def _(path: Path):
    if path.suffix == ".csg":
        return "text.csg"
    return None


@register_writer_plugin(priority=10)
def write_csg(path: Path, model: WidgetDataModel):
    """Write a JSON string to a cryosparc csg file."""
    return path.write_text(model.value)


@write_csg.define_matcher
def _(model: WidgetDataModel, path: Path):
    return path.suffix == ".csg"


@register_reader_plugin
def read_mdoc(path: Path):
    """Read a SerialEM mdoc file as a dataframe."""
    import mdocfile

    df = mdocfile.read(path)
    return WidgetDataModel(value=df, type=StandardType.DATAFRAME)


@read_mdoc.define_matcher
def _(path: Path):
    if path.suffix == ".mdoc":
        return StandardType.DATAFRAME
    return None


@register_reader_plugin
def read_nav(path: Path):
    """Read a SerialEM nav file."""
    # For the file format, see:
    # https://bio3d.colorado.edu/SerialEM/hlp/html/about_formats.htm
    text = path.read_text()
    return WidgetDataModel(value=text, type=Type.NAV)


@read_nav.define_matcher
def _(path: Path):
    if path.suffix == ".nav":
        return Type.NAV
    return None


@register_reader_plugin
def read_ctf(path: Path):
    """Read a CTFFind CTF file as an image."""
    import mrcfile

    with mrcfile.open(path) as f:
        arr = f.data
    return WidgetDataModel(value=arr[0], type=StandardType.IMAGE)


@read_ctf.define_matcher
def _(path: Path):
    if path.suffix == ".ctf":
        return StandardType.IMAGE
    return None


@register_reader_plugin
def read_xf(path: Path):
    """Read an IMOD xf file as a dataframe."""
    # https://warpem.github.io/warp/reference/warptools/custom_tilt_series_alignments
    arr = [a.split() for a in path.read_text(encoding="utf-8").splitlines()]
    arr = np.array(arr, dtype=np.float32)
    # A11 A12 A21 A22 DX DY
    columns = ["A11", "A12", "A21", "A22", "DX", "DY"]
    df = {col: arr[:, i] for i, col in enumerate(columns)}
    return WidgetDataModel(value=df, type=StandardType.DATAFRAME)


@read_xf.define_matcher
def _(path: Path):
    if path.suffix in [".xf", ".prexf"]:
        return StandardType.DATAFRAME
    return None


@register_writer_plugin
def write_xf(model: WidgetDataModel, path: Path):
    """Write a dataframe to an IMOD xf file."""
    df = wrap_dataframe(model.value)
    if df.column_names() != ["A11", "A12", "A21", "A22", "DX", "DY"]:
        raise ValueError(
            f"Expected columns ['A11', 'A12', 'A21', 'A22', 'DX', 'DY'], got {df.column_names()}"
        )
    csv = df.to_csv_string(separator="\t", header=False)
    path.write_text(csv)


@write_xf.define_matcher
def _(model: WidgetDataModel, path: Path):
    type_ok = model.type == StandardType.DATAFRAME
    ext_ok = path.suffix in [".xf", ".prexf"]
    return type_ok and ext_ok
