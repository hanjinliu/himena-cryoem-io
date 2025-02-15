from __future__ import annotations

from himena import WidgetDataModel
from qtpy import QtWidgets as QtW
from himena.plugins import validate_protocol

from himena_cryoem_io._parse_nav import parse_nav, NavFile, NavItem


class QNavigator(QtW.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtW.QVBoxLayout(self)
        self._tree_widget = QtW.QTreeWidget()
        self._tree_widget.setHeaderLabels(
            ["Label", "Color", "X", "Y", "Z", "Type", "Reg.", "Acq.", "Note"]
        )
        self._tree_widget.header().setFixedHeight(24)
        layout.addWidget(self._tree_widget)

        self._nav_file: NavFile | None = None

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

    @validate_protocol
    def model_type(self) -> str:
        return "text.SerialEM-nav"

    @validate_protocol
    def size_hint(self) -> tuple[int, int]:
        return 360, 420

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
