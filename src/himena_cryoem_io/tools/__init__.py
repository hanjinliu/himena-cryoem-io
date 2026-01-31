from himena.plugins import configure_submenu
from himena_cryoem_io.consts import MenuId
from himena_cryoem_io.tools import star

configure_submenu(MenuId.CRYOEM, "Cryo-EM")

del star, configure_submenu, MenuId
