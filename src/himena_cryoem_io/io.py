from __future__ import annotations

from pathlib import Path
import numpy as np
from himena import StandardType, WidgetDataModel
from himena.standards.model_meta import TextMeta
from himena.plugins import register_reader_plugin, register_writer_plugin
from himena_cryoem_io.consts import Type
from himena_cryoem_io import widgets

del widgets  # reading nav always needs the widget.


@register_reader_plugin
def read_star(path: Path):
    import starfile

    dict_of_blocks = starfile.read(path, always_dict=True)
    assert isinstance(dict_of_blocks, dict)
    return WidgetDataModel(value=dict_of_blocks, type=StandardType.DATAFRAMES)


@read_star.define_matcher
def _(path: Path):
    if path.suffix == ".star":
        return StandardType.DATAFRAMES
    return None


@register_writer_plugin
def write_star(path: Path, model: WidgetDataModel):
    import starfile

    return starfile.write(model.value, path)


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


def read_mod(path: Path):
    import imodmodel

    imod = imodmodel.ImodModel.from_file(path)
    return WidgetDataModel(value=imod, type=Type.IMOD_MODEL)


def write_mod(path: Path, data: WidgetDataModel):
    import imodmodel

    if isinstance(imod := data.value, imodmodel.ImodModel):
        imod.to_file(path)
    else:
        raise TypeError(f"Expected imodmodel.ImodModel, got {type(imod)}")


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
