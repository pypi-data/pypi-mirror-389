import os

import numpy as np
import xarray as xr

def render(
        video: xr.DataArray,
        path: str | os.PathLike,
        images: list[dict],
) -> None:
    """
    Create a visualization of the supplied video and store it in a file.
    """
    import napari
    pass
