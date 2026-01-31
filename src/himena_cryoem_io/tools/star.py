from typing import Any, TYPE_CHECKING
from starfile_rs import read_star_text
from himena import Parametric, StandardType
from himena.types import WidgetDataModel
from himena.standards.model_meta import TableMeta
from himena.widgets import SubWindow
from himena.plugins import register_function, configure_gui
from himena_builtins.tools.plot import PlotFactory

from himena_cryoem_io.consts import Type, MenuId
from himena_cryoem_io.star_meta import StarMeta

SelectionType = tuple[tuple[int, int], tuple[int, int]]

if TYPE_CHECKING:
    from himena_cryoem_io.widgets.star import QStarView


class StarPlotFactory(PlotFactory):
    @classmethod
    def model_types(cls) -> list[str]:
        return [Type.STAR]

    def table_data_model(self, current_block: str) -> WidgetDataModel:
        model = self.to_model()
        title = f"{model.title} - {current_block}"
        if qstarview := _maybe_qstarview(self.subwindow.widget):
            out = qstarview._dataframe_view.to_model()
            out.title = title
            return out
        meta = model.metadata
        if not isinstance(meta, StarMeta):
            meta = TableMeta()
        data = read_star_text(model.value)[current_block].to_polars()
        return WidgetDataModel(
            value=data,
            type=StandardType.DATAFRAME,
            title=title,
            metadata=meta,
        )

    def prep_kwargs(self) -> dict[str, Any]:
        model = self.to_model()
        if not isinstance(meta := model.metadata, StarMeta):
            raise ValueError("Metadata is not StarMeta")
        name = meta.current_block
        if name is None:
            raise ValueError("No block selected")
        return {"current_block": name}


@register_function(
    types=[Type.STAR],
    menus=[MenuId.STAR],
    title="Duplicate Current Block As DataFrame",
    command_id="himena-cryoem-io:star:duplicate-block-as-dataframe",
)
def duplicate_block_as_dataframe(win: SubWindow) -> Parametric:
    """Duplicate the selected block as a DataFrame model."""
    model = win.to_model()
    star = model.value
    title = model.title

    def _get_block_name(*_):
        if not isinstance(meta := win.to_model().metadata, StarMeta):
            raise ValueError("Metadata is not StarMeta")
        name = meta.current_block
        if name is None:
            raise ValueError("No block selected")
        return name

    @configure_gui(name={"bind": _get_block_name})
    def _duplicate_block(name: str) -> WidgetDataModel:
        star_dict = read_star_text(star)
        block = star_dict[name]
        df = block.to_polars()
        return WidgetDataModel(
            value=df,
            type=StandardType.DATAFRAME,
            title=f"{title} - {name}",
            metadata=TableMeta(),
        )

    return _duplicate_block


@register_function(
    types=[Type.STAR],
    menus=[MenuId.STAR],
    title="Duplicate Current Block As Text",
    command_id="himena-cryoem-io:star:duplicate-block-as-text",
)
def duplicate_block_as_text(win: SubWindow) -> Parametric:
    """Duplicate the selected block as a text model."""
    model = win.to_model()
    star = model.value
    title = model.title

    def _get_block_name(*_):
        if not isinstance(meta := win.to_model().metadata, StarMeta):
            raise ValueError("Metadata is not StarMeta")
        name = meta.current_block
        if name is None:
            raise ValueError("No block selected")
        return name

    @configure_gui(name={"bind": _get_block_name})
    def _duplicate_block(name: str) -> WidgetDataModel:
        star_dict = read_star_text(star)
        block = star_dict[name]
        text = block.to_string()
        return WidgetDataModel(
            value=text,
            type=StandardType.TEXT,
            title=f"{title} - {name}",
        )

    return _duplicate_block


def _maybe_qstarview(widget: object) -> "QStarView | None":
    if getattr(widget, "__himena_widget_id__", "") == "himena-cryoem-io:QStarView":
        return widget
