from __future__ import annotations
from qtpy import QtCore, QtWidgets as QtW, QtGui
from himena import MainWindow, StandardType, WidgetDataModel
from himena.plugins import validate_protocol
from himena.standards.model_meta import DataFrameMeta
from himena_builtins.qt.widgets.dataframe import QDataFrameView, QDataFrameViewControl
from himena_cryoem_io.consts import Type
from himena_cryoem_io.star_meta import StarMeta
from starfile_rs import read_star_text, LoopDataBlock, SingleDataBlock, DataBlock
import polars as pl


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
        self._dataframe_title = QtW.QLabel("")
        self._dataframe_title.setFixedHeight(24)
        self._dataframe_view = QDataFrameView(ui)
        self._dataframe_view._hor_header._drag_enabled = False
        self.addWidget(self._block_name_list)
        _right = QtW.QWidget()
        _right_layout = QtW.QVBoxLayout(_right)
        _right_layout.setSpacing(0)
        _right_layout.setContentsMargins(0, 0, 0, 0)
        _right_layout.addWidget(self._dataframe_title)
        _right_layout.addWidget(self._dataframe_view)
        self.addWidget(_right)
        self._star: dict[str, DataBlockWrapper] = {}
        self._orig_text = ""
        self.setSizes([160, 320])
        self.setStretchFactor(0, 0)  # left panel doesn't stretch
        self.setStretchFactor(1, 1)  # right panel stretches
        self._control_widget: QStarControl | None = None

        self._block_name_list.right_clicked.connect(self._on_block_name_right_clicked)

    @validate_protocol
    def update_model(self, model: WidgetDataModel):
        self._orig_text = model.value
        self._star = {
            name: DataBlockWrapper(block)
            for name, block in read_star_text(model.value).items()
        }
        block_names = list(self._star.keys())
        self._block_name_list.set_block_names(block_names)
        self._block_name_list.setVisible(len(block_names) > 1)

        # refer to metadata
        if isinstance(meta := model.metadata, StarMeta):
            current_block = meta.current_block
            if current_block in self._star:
                idx = list(self._star.keys()).index(current_block)
                self._block_name_list.setCurrentIndex(
                    self._block_name_list.model().index(idx, 0)
                )
            df_view = self._dataframe_view
            df_view._selection_model.clear()
            if (pos := meta.current_position) is not None:
                index = df_view.model().index(*pos)
                df_view.setCurrentIndex(index)
                df_view._selection_model.current_index = pos
            for (r0, r1), (c0, c1) in meta.selections:
                df_view._selection_model.append((slice(r0, r1), slice(c0, c1)))

    @validate_protocol
    def to_model(self) -> WidgetDataModel:
        df_meta = self._dataframe_view._prep_table_meta()
        idx = self._block_name_list.currentIndex()
        block_names = list(self._star.keys())
        return WidgetDataModel(
            value=self._orig_text,
            type=Type.STAR,
            metadata=StarMeta(
                current_position=df_meta.current_position,
                selections=df_meta.selections,
                current_block=block_names[idx.row()] if idx.isValid() else None,
            ),
        )

    @validate_protocol
    def control_widget(self) -> QDataFrameViewControl:
        if self._control_widget is None:
            self._control_widget = QStarControl(self._dataframe_view)
            self._control_widget.update_for_table(self._dataframe_view)
        return self._control_widget

    @validate_protocol
    def model_type(self) -> str:
        return Type.STAR

    @validate_protocol
    def theme_changed_callback(self, theme):
        if control := self._control_widget:
            control.update_theme(theme)

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
        if control := self._control_widget:
            control.update_for_table(self._dataframe_view)
        self._dataframe_title.setText(f"<b>data_{block_name}</b>")
        font_metric = self._dataframe_view.fontMetrics()
        for i, colname in enumerate(df.columns):
            width = font_metric.horizontalAdvance(str(colname)) + 20
            self._dataframe_view.setColumnWidth(i, width)

    def _make_menu(self, block: str) -> QtW.QMenu:
        menu = QtW.QMenu(self)
        action = menu.addAction("Duplicate Block As DataFrame")
        action.triggered.connect(lambda: self._duplicate_block_as_df(block))
        action = menu.addAction("Duplicate Block As Text")
        action.triggered.connect(lambda: self._duplicate_block_as_text(block))
        return menu

    def _on_block_name_right_clicked(self, block_name: str):
        menu = self._make_menu(block_name)
        return menu.exec(QtGui.QCursor.pos())

    def _duplicate_block_as_df(self, block_name: str):
        return self._ui.exec_action(
            "himena-cryoem-io:star:duplicate-block-as-dataframe",
            model_context=self.to_model(),
            with_params={"name": block_name},
        )

    def _duplicate_block_as_text(self, block_name: str) -> str:
        return self._ui.exec_action(
            "himena-cryoem-io:star:duplicate-block-as-text",
            model_context=self.to_model(),
            with_params={"name": block_name},
        )


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
    right_clicked = QtCore.Signal(str)

    def __init__(self, parent: QtW.QWidget | None = None):
        super().__init__(parent)
        self.setSelectionMode(QtW.QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QtW.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setUniformItemSizes(True)
        self.setModel(QStarBlockListModel())
        self.selectionModel().currentChanged.connect(self._on_current_changed)

    def _on_current_changed(
        self, current: QtCore.QModelIndex, previous: QtCore.QModelIndex
    ):
        block_name = current.data(QtCore.Qt.ItemDataRole.DisplayRole)
        self.current_changed.emit(block_name)

    def set_block_names(self, names: list[str]):
        model = self.model()
        assert isinstance(model, QStarBlockListModel)
        model.setStringList(names)
        if names:
            self.setCurrentIndex(model.index(0, 0))

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        if e.button() == QtCore.Qt.MouseButton.RightButton:
            current_index = self.indexAt(e.position().toPoint())
            if current_index.isValid():
                self.right_clicked.emit(current_index.data())


class QStarBlockListModel(QtCore.QStringListModel):
    def data(self, index: QtCore.QModelIndex, role: int = 0) -> QtCore.QVariant:
        if role == QtCore.Qt.ItemDataRole.SizeHintRole:
            return QtCore.QSize(100, 22)
        return super().data(index, role)


class QStarControl(QDataFrameViewControl):
    pass
