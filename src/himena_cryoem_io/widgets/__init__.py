from himena_cryoem_io.consts import Type
from himena_cryoem_io.widgets.navigator import QNavigator
from himena.plugins import register_widget_class


def _register():
    register_widget_class(Type.NAV, QNavigator)


_register()
