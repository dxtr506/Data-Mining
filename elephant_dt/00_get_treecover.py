"""Download a pinned woody-density surface from the study authors' repository.

woodland_clip.tif is written from trees_interpolate.tif in the authors' code.
It is NOT the original Bucini raster. A supplied elemove/data/treecover.tif
takes precedence; there is no silent Hansen (>5m trees) fallback.
"""
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
import rasterio
import numpy as np
import config as C

REVISION = "49938f5eede63b38060f2adb4ae744526aa98dcb"
REPO = "https://github.com/pratikunterwegs/elephantTempKruger"
URL = f"https://raw.githubusercontent.com/pratikunterwegs/elephantTempKruger/{REVISION}/ele_code/spatial/woodland_clip.tif"
EXPECTED_SHA256 = "58980f9d4536723baa82cfe60c43fa1856983adb6cdcf47c2fc879d52872edef"


def main():
    C.utf8_stdout()
    C.WOODY_METADATA.parent.mkdir(parents=True, exist_ok=True)
    original = C.WOODY_BUCINI.exists()
    path = C.WOODY_BUCINI if original else C.WOODY_AUTHOR
    if not path.exists():
        request = urllib.request.Request(URL, headers={"User-Agent": "Kruger-elephant-research-demo/1.0"})
        with urllib.request.urlopen(request, timeout=60) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != EXPECTED_SHA256:
            raise ValueError("Raster checksum mismatch.")
        path.write_bytes(data)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    if not original and sha != EXPECTED_SHA256:
        raise ValueError("Cached author raster checksum mismatch.")
    with rasterio.open(path) as r:
        if not r.crs or r.count != 1:
            raise ValueError("Expected a georeferenced single-band raster.")
        valid = r.read(1, masked=True).compressed()
        if not len(valid) or not np.isfinite(valid).all() or valid.min() < 0 or valid.max() > 100:
            raise ValueError("Expected percent cover values in [0,100].")
        info = {"path": str(path), "sha256": sha, "crs": str(r.crs), "width": r.width,
                "height": r.height, "resolution_crs_units": list(r.res), "bounds": list(r.bounds),
                "nodata": r.nodata, "value_min": float(valid.min()), "value_max": float(valid.max()),
                "unit": "percent", "feature": "woody", "stem_density": False,
                "source_kind": "user_supplied_original_unverified" if original else "author_interpolated_woody_surface",
                "source_url": None if original else URL, "repository": REPO,
                "repository_revision": None if original else REVISION,
                "reference_doi": "10.1201/b10275-15", "study_doi": "10.3389/fevo.2019.00004",
                "original_bucini_raster_verified": False,
                "temporal_status": "static surface; observation year not independently verified",
                "limitations": ["Author surface is derived from trees_interpolate.tif, not the raw Bucini map.",
                                "Interpolation reconstruction and original Bucini map are not supplied in this repository.",
                                "Canopy percentage is not a count of trees per unit area."],
                "lineage_code_url": f"{REPO}/blob/{REVISION}/ele_code/elecode012woodlandmaps2.rmd",
                "metadata_written_utc": datetime.now(timezone.utc).isoformat()}
    C.WOODY_METADATA.write_text(json.dumps(info, indent=2, ensure_ascii=False, allow_nan=False), "utf-8")
    print(f"Woody surface: {path.name}, {info['width']}×{info['height']}, {info['value_min']:.2f}–{info['value_max']:.2f}%")
    print("Source:", info["source_kind"], "· metadata:", C.WOODY_METADATA)


if __name__ == "__main__":
    main()
