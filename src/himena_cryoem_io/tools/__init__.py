from himena.plugins import configure_submenu
from himena_cryoem_io.consts import MenuId
from himena_cryoem_io.tools import star, serialem

configure_submenu(MenuId.CRYOEM, "CryoEM")
configure_submenu(MenuId.SERIALEM, "SerialEM")

del star, serialem, configure_submenu, MenuId
