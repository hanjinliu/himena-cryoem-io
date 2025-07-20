from __future__ import annotations

from pathlib import Path
import mdocfile
import numpy as np
import pandas as pd
from qtpy import QtWidgets as QtW, QtCore
from superqt import QToggleSwitch

from himena import StandardType, WidgetDataModel
from himena.plugins import validate_protocol
from himena.io_utils import read
from himena_builtins.qt.widgets.image import QImageGraphicsView
from himena_cryoem_io._parse_nav import parse_nav, NavFile, NavItem, MapItem
from himena_cryoem_io.consts import Type


class QNavigator(QtW.QSplitter):
    def __init__(self):
        super().__init__()
        self._tree_widget = QtW.QTreeWidget()
        self._tree_widget.setHeaderLabels(
            ["Label", "Color", "X", "Y", "Z", "Type", "Reg.", "Acq.", "Note"]
        )
        self._tree_widget.header().setFixedHeight(24)
        self._tree_widget.itemDoubleClicked.connect(self._on_tree_item_double_clicked)
        self.addWidget(self._tree_widget)

        self._img_view = QImageGraphicsView()
        self.addWidget(self._img_view)
        self._nav_file: NavFile | None = None
        self._nav_source: Path | None = None
        self._control_widget = QNavigatorControl(self)
        self.setSizes([300, 500])

    @validate_protocol
    def update_model(self, model: WidgetDataModel):
        text = model.value
        if not isinstance(text, str):
            raise ValueError("The model value must be a string.")
        nav = parse_nav(text)
        for item in nav.items:
            self._add_nav_item(item)
        for i in range(9):
            self._tree_widget.resizeColumnToContents(i)
        self._nav_file = nav
        self._nav_source = model.source

    @validate_protocol
    def model_type(self) -> str:
        return Type.NAV

    @validate_protocol
    def size_hint(self) -> tuple[int, int]:
        return 800, 420

    @validate_protocol
    def control_widget(self) -> QNavigatorControl:
        return self._control_widget

    def _add_nav_item(self, item: NavItem):
        tree_item = QtW.QTreeWidgetItem(self._tree_widget)
        tree_item.setText(0, item.label)
        tree_item.setText(1, str(item.color))
        tree_item.setText(2, format(item.x, ".1f"))
        tree_item.setText(3, format(item.y, ".1f"))
        tree_item.setText(4, format(item.z, ".1f"))
        tree_item.setText(5, item.type.name)
        tree_item.setText(6, str(item.regis))
        tree_item.setText(7, item.acquire)
        tree_item.setText(8, item.note)
        self._tree_widget.addTopLevelItem(tree_item)

    def _nav_item_for_item(self, item: QtW.QTreeWidgetItem) -> NavItem | None:
        row = self._tree_widget.indexOfTopLevelItem(item)
        if row == -1:
            return
        return self._nav_file.items[row]

    def _on_tree_item_double_clicked(self, item):
        if self._nav_file is None:
            return
        if nav_item := self._nav_item_for_item(item):
            self._set_nav_item(nav_item)

    def _set_nav_item(self, nav_item: NavItem):
        if isinstance(nav_item, MapItem):
            path = _solve_path(nav_item.params.map_file, self._nav_source)
            model = read(path)
            if not model.is_subtype_of(StandardType.IMAGE):
                raise ValueError(f"Expected an image, got type {model.type!r}")
            img = np.asarray(model.value)
            if img.ndim > 3:
                raise ValueError(f"Expected a 2D or 3D image, got shape {img.shape}")
            elif img.ndim == 3:
                if nav_item.params.map_montage:
                    mdoc_path = path.with_suffix(f"{path.suffix}.mdoc")
                    if not mdoc_path.exists():
                        raise FileNotFoundError(f"mdoc file not found: {mdoc_path}")
                    mdoc = mdocfile.read(mdoc_path)
                    align = self._control_widget._align_switch.isChecked()
                    img_slice = _tile_montage(img, mdoc, align=align)
                else:
                    img_slice = img[nav_item.params.map_section]
            else:
                img_slice = img
            self._img_view.set_n_images(1)
            self._img_view.set_array(0, _as_uint8(img_slice))
            self._img_view.auto_range()


class QNavigatorControl(QtW.QWidget):
    def __init__(self, navigator: QNavigator):
        super().__init__()
        self._navigator = navigator
        layout = QtW.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        # align the montage if this switch is checked
        self._align_switch = QToggleSwitch("Align")
        self._align_switch.setChecked(True)
        layout.addWidget(self._align_switch)

        self._align_switch.toggled.connect(self._on_align_toggled)

    def _on_align_toggled(self, checked: bool):
        if item := self._navigator._tree_widget.currentItem():
            if nav_item := self._navigator._nav_item_for_item(item):
                if isinstance(nav_item, MapItem):
                    self._navigator._set_nav_item(nav_item)


def _tile_montage(img: np.ndarray, mdoc: pd.DataFrame, align: bool) -> np.ndarray:
    mont_xmin, mont_ymin = 0, 0
    mont_xmax, mont_ymax = 0, 0
    image_size_y, image_size_x = img.shape[1:]
    colname = "AlignedPieceCoords" if align else "PieceCoordinates"
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
        img_slice = img[int(zvalue)]
        img_u8 = ((img_slice - i_min) / (i_max - i_min) * 255).astype(np.uint8)
        img_montage[y : y + image_size_y, x : x + image_size_x] = img_u8
    return img_montage


def _solve_path(path: Path, nav_path: Path | None = None) -> Path:
    path = path.resolve()
    if path.exists():
        return path
    if nav_path is not None and (fp := nav_path.parent.joinpath(path.name)).exists():
        return fp
    raise FileNotFoundError(f"File not found: {path}")


def _as_uint8(img: np.ndarray) -> np.ndarray:
    """Convert an image to uint8."""
    if img.dtype == np.uint8:
        return img
    _min, _max = img.min(), img.max()
    return ((img - _min) / (_max - _min) * 255).astype(np.uint8)


def _quick_clim(img: np.ndarray) -> tuple[int, int]:
    img_sub = img[..., ::4]
    return tuple(np.quantile(img_sub, [0.001, 0.999]))
