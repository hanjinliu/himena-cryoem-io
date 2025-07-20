from __future__ import annotations

from pathlib import Path
import tempfile
from typing import Literal
from himena import Parametric, StandardType, WidgetDataModel
from himena.consts import MenuId
from himena.widgets import set_status_tip
from himena.standards.model_meta import ImageMeta, DimAxis
from himena.plugins import register_function, configure_gui
import numpy as np


@register_function(
    menus=MenuId.FILE_NEW,
    title="Fetch EMDB",
    command_id="himena-cryoem-io:fetch:emdb",
)
def fetch_emdb() -> Parametric:
    """Fetch the EMDB entry."""
    import requests
    import mrcfile

    @configure_gui(run_async=True)
    def fetch_emdb_entry(
        emdb_id: str,
        mirror: Literal["Europe", "US", "China", "Japan"] = "Europe",
    ) -> WidgetDataModel:
        url = _map_url(emdb_id, mirror)
        response = requests.get(url, stream=True)
        total_mb = int(response.headers.get("content-length", 0)) / 2**20
        chunk_size = 2**20
        if response.status_code == 200:
            with tempfile.TemporaryDirectory() as tmpdir:
                map_path = Path(tmpdir) / f"emd_{emdb_id}.map.gz"
                with open(map_path, "wb") as file:
                    for i, chunk in enumerate(
                        response.iter_content(chunk_size=chunk_size)
                    ):
                        file.write(chunk)
                        downloaded_mb = i * chunk_size / 2**20
                        set_status_tip(
                            f"Downloading EMD-{emdb_id} ({downloaded_mb:.2f} / {total_mb:.2f} MB)"
                        )
                with mrcfile.open(map_path) as mrc:
                    img = np.array(mrc.data)
                    axes = [
                        DimAxis(name=axis, scale=float(mrc.voxel_size[axis]))
                        for axis in "zyx"
                    ]
        else:
            raise ValueError(f"Failed to download: {url}")
        set_status_tip(f"Downloaded EMD-{emdb_id}")
        return WidgetDataModel(
            value=img,
            type=StandardType.IMAGE,
            title=f"EMDB-{emdb_id}",
            metadata=ImageMeta(axes=axes),
        )

    return fetch_emdb_entry


def _map_url(emdb_id: str, mirror: Literal["Europe", "US", "China", "Japan"]) -> str:
    if mirror == "Europe":
        return f"https://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-{emdb_id}/map/emd_{emdb_id}.map.gz"
    elif mirror == "US":
        return f"https://ftp.wwpdb.org/pub/emdb/structures/EMD-{emdb_id}/map/emd_{emdb_id}.map.gz"
    elif mirror == "China":
        return f"https://ftp.emdb-china.org/structures/EMD-{emdb_id}/map/emd_{emdb_id}.map.gz"
    elif mirror == "Japan":
        return f"https://ftp.pdbj.org/pub/emdb/structures/EMD-{emdb_id}/map/emd_{emdb_id}.map.gz"
    else:  # pragma: no cover
        raise ValueError(f"Unknown mirror: {mirror}")
