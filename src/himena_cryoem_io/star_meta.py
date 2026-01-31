from himena_cryoem_io.consts import Type
from himena.standards.model_meta import TableMeta


class StarMeta(TableMeta):
    """Metadata for STAR widget."""

    current_block: str | None = None

    def expected_type(self):
        return Type.STAR
