from __future__ import annotations
from qtpy import QtCore, QtWidgets as QtW
from himena import MainWindow, StandardType, WidgetDataModel
from himena.plugins import validate_protocol
from himena.standards.model_meta import DataFrameMeta
from himena_builtins.qt.widgets.dataframe import QDataFrameView
from himena_cryoem_io.consts import Type
from starfile_rs import read_star_text, LoopDataBlock, SingleDataBlock, DataBlock
import polars as pl

# TODO: block drag/drop


class QStarView(QtW.QSplitter):
    """Star file viewer."""

    __himena_widget_id__ = "himena-cryoem-io:QStarView"
    __himena_display_name__ = "Star File Viewer"

    def __init__(self, ui: MainWindow):
        super().__init__(QtCore.Qt.Orientation.Horizontal)
        self._ui = ui
        left = QtW.QWidget()
        self._block_name_list = QStarBlockNameView(self)
        self._block_name_list.current_changed.connect(self._on_block_name_changed)
        left.setFixedWidth(160)
        self._dataframe_view = QDataFrameView(ui)
        self._dataframe_view._hor_header._drag_enabled = False
        self.addWidget(self._block_name_list)
        self.addWidget(self._dataframe_view)
        self._star: dict[str, DataBlockWrapper] = {}
        self._orig_text = ""
        self.setSizes([160, 320])

    @validate_protocol
    def update_model(self, model: WidgetDataModel):
        self._orig_text = model.value
        self._star = {
            name: DataBlockWrapper(block)
            for name, block in read_star_text(model.value).items()
        }
        block_names = list(self._star.keys())
        self._block_name_list.set_block_names(block_names)
        hide = len(block_names) == 0 or len(block_names) == 1 and block_names[0] == ""
        self._block_name_list.setVisible(not hide)

    @validate_protocol
    def to_model(self) -> WidgetDataModel:
        return WidgetDataModel(value=self._orig_text, type=Type.STAR)

    @validate_protocol
    def model_type(self) -> str:
        return Type.STAR

    @validate_protocol
    def size_hint(self) -> tuple[int, int]:
        return (480, 320)

    def _on_block_name_changed(self, block_name: str):
        block = self._star[block_name]
        df = block.dataframe
        df_model = WidgetDataModel(
            value=df,
            type=StandardType.DATAFRAME,
            metadata=DataFrameMeta(transpose=not block._is_loop),
        )
        self._dataframe_view.update_model(df_model)
        font_metric = self._dataframe_view.fontMetrics()
        for i, colname in enumerate(df.columns):
            width = font_metric.horizontalAdvance(str(colname)) + 20
            self._dataframe_view.setColumnWidth(i, width)


class DataBlockWrapper:
    """A cached data block wrapper"""

    def __init__(self, block: DataBlock):
        self._block = block
        self._cached_df: pl.DataFrame | None = None
        self._is_loop = isinstance(block, LoopDataBlock)

    @property
    def dataframe(self) -> pl.DataFrame:
        if self._cached_df is None:
            if isinstance(self._block, LoopDataBlock):
                self._cached_df = self._block.to_polars()
            elif isinstance(self._block, SingleDataBlock):
                self._cached_df = pl.DataFrame(self._block.to_dict())
            else:
                self._cached_df = pl.DataFrame()
            self._block = None  # free memory
        return self._cached_df


class QStarBlockNameView(QtW.QListView):
    current_changed = QtCore.Signal(str)

    def __init__(self, parent: QtW.QWidget | None = None):
        super().__init__(parent)
        self.setSelectionMode(QtW.QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setUniformItemSizes(True)
        self.setModel(QtCore.QStringListModel())
        self.selectionModel().currentChanged.connect(self._on_current_changed)

    def _on_current_changed(
        self, current: QtCore.QModelIndex, previous: QtCore.QModelIndex
    ):
        block_name = current.data(QtCore.Qt.ItemDataRole.DisplayRole)
        self.current_changed.emit(block_name)

    def set_block_names(self, names: list[str]):
        model = self.model()
        assert isinstance(model, QtCore.QStringListModel)
        model.setStringList(names)
        if names:
            self.setCurrentIndex(model.index(0, 0))
