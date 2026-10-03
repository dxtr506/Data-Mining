"""CRS-aware sampling of percent woody cover. Nodata stays NaN, never zero."""
import json
import numpy as np
import rasterio
from rasterio.transform import rowcol
from pyproj import Transformer
from scipy.ndimage import uniform_filter
import config as C


def sample_woody(lon, lat):
    if not C.WOODY_TIF.exists():
        raise FileNotFoundError("Missing woody raster. Run 00_get_treecover.py first.")
    with rasterio.open(C.WOODY_TIF) as src:
        if src.crs is None:
            raise ValueError("Woody raster has no CRS.")
        x, y = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True).transform(lon, lat)
        rr, cc = rowcol(src.transform, x, y)
        rr, cc = np.asarray(rr), np.asarray(cc)
        inside = (rr >= 0) & (cc >= 0) & (rr < src.height) & (cc < src.width)
        a = src.read(1, masked=True).astype(float).filled(np.nan)
        a[(a < 0) | (a > 100) | ~np.isfinite(a)] = np.nan
        if not src.crs.is_projected or src.crs.linear_units not in ["metre", "meter"]:
            raise ValueError("Neighborhood metrics require a projected raster in metres.")
        size = tuple(max(1, 2 * int(np.floor(C.WOODY_SMOOTH_M / v)) + 1) for v in src.res[::-1])
        mask = np.isfinite(a)
        weights = uniform_filter(mask.astype(float), size=size, mode="constant", cval=0)
        sums = uniform_filter(np.where(mask, a, 0), size=size, mode="constant", cval=0)
        squares = uniform_filter(np.where(mask, a*a, 0), size=size, mode="constant", cval=0)
        m = np.divide(sums, weights, out=np.full_like(a, np.nan), where=weights > 0)
        var = np.maximum(np.divide(squares, weights, out=np.full_like(a, np.nan), where=weights > 0) - m*m, 0)
        results = {}
        valid_center = np.full(len(rr), False)
        valid_center[inside] = mask[rr[inside], cc[inside]]
        for name, arr in [("woody", a), ("woody_mean_300m", m), ("woody_std_300m", np.sqrt(var))]:
            vals = np.full(len(rr), np.nan)
            vals[inside] = arr[rr[inside], cc[inside]]
            vals[~valid_center] = np.nan
            results[name] = vals
        results["woody_missing"] = (~valid_center).astype(np.int8)
        meta = {"window_pixels": list(size), "window_width_m": [size[1]*src.res[0], size[0]*src.res[1]],
                "n_sampled": len(rr), "n_outside_bounds": int((~inside).sum()),
                "n_missing_native": int((~valid_center).sum()), "n_valid": int(valid_center.sum())}
    return results, meta


def source_metadata():
    return json.loads(C.WOODY_METADATA.read_text("utf-8")) if C.WOODY_METADATA.exists() else {}
