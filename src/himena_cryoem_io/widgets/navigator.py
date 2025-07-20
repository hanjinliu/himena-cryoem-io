from __future__ import annotations

from pathlib import Path
import mdocfile
import numpy as np
from qtpy import QtWidgets as QtW

from himena import StandardType, WidgetDataModel
from himena.plugins import validate_protocol
from himena.io_utils import read
from himena_builtins.qt.widgets.image import QImageGraphicsView
from himena_cryoem_io._parse_nav import parse_nav, NavFile, NavItem, MapItem


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
        return "text.SerialEM-nav"

    @validate_protocol
    def size_hint(self) -> tuple[int, int]:
        return 600, 420

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

    def _on_tree_item_double_clicked(self, item):
        if self._nav_file is None:
            return
        row = self._tree_widget.indexOfTopLevelItem(item)
        if row == -1:
            return
        nav_item = self._nav_file.items[row]
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
                    # TODO: read mdoc and montage the images
                    mdoc_path = path.with_suffix(f"{path.suffix}.mdoc")
                    if not mdoc_path.exists():
                        raise FileNotFoundError(f"mdoc file not found: {mdoc_path}")
                    # TODO: bug in mdocfile; cannot read mdoc file
                    mdoc = mdocfile.read(mdoc_path)
                    mdoc
                else:
                    img_slice = img[nav_item.params.map_section]
            else:
                img_slice = img
            self._img_view.set_n_images(1)
            self._img_view.set_array(0, img_slice)


def _solve_path(path: Path, nav_path: Path | None = None) -> Path:
    path = path.resolve()
    if path.exists():
        return path
    if nav_path is not None and (fp := nav_path.parent.joinpath(path.name)).exists():
        return fp
    raise FileNotFoundError(f"File not found: {path}")
