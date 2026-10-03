"""Bước 0 (tuỳ chọn): tải vùng mặt nước (hồ, đập, lòng sông) từ OpenStreetMap qua Overpass API.

Chỉ dùng làm nền bản đồ cho web (thấy rõ sông, hồ khi phóng to), không dùng để tính khoảng cách
tới nước (bước 1 vẫn dùng đúng dữ liệu của paper). Dữ liệu OSM là hiện tại, không phải 2007–2009.
Kết quả lưu ở data/osm_water.geojson; nếu file đã có thì không tải lại.
"""
import json
import urllib.parse
import urllib.request

import shapely
from shapely.geometry import LineString, mapping
from shapely.ops import polygonize

import config as C

C.utf8_stdout()
OUT = C.ROOT / "data" / "osm_water.geojson"
BBOX = (-25.6, 31.0, -23.8, 32.15)        # nam, tây, bắc, đông
URL = "https://overpass-api.de/api/interpreter"
QUERY = """
[out:json][timeout:180];
(
  way["natural"="water"]({s},{w},{n},{e});
  relation["natural"="water"]({s},{w},{n},{e});
  way["waterway"="riverbank"]({s},{w},{n},{e});
  relation["waterway"="riverbank"]({s},{w},{n},{e});
  way["landuse"="reservoir"]({s},{w},{n},{e});
);
out geom;
"""


def way_line(geom):
    return LineString([(p["lon"], p["lat"]) for p in geom])


def to_polygons(el):
    if el["type"] == "way":
        g = el.get("geometry") or []
        if len(g) >= 4 and g[0] == g[-1]:
            return [shapely.Polygon([(p["lon"], p["lat"]) for p in g])]
        return []
    outer = [way_line(m["geometry"]) for m in el.get("members", []) if m.get("role") == "outer" and m.get("geometry")]
    inner = [way_line(m["geometry"]) for m in el.get("members", []) if m.get("role") == "inner" and m.get("geometry")]
    polys = list(polygonize(outer))
    holes = shapely.union_all(list(polygonize(inner))) if inner else None
    return [p.difference(holes) if holes is not None else p for p in polys]


def main():
    if OUT.exists():
        print("Đã có", OUT)
        return
    s, w, n, e = BBOX
    data = urllib.parse.urlencode({"data": QUERY.format(s=s, w=w, n=n, e=e)}).encode()
    req = urllib.request.Request(URL, data=data, headers={"User-Agent": "elephant-dt-student-project"})
    with urllib.request.urlopen(req, timeout=240) as r:
        els = json.load(r)["elements"]
    feats = []
    for el in els:
        kind = el.get("tags", {}).get("water") or el.get("tags", {}).get("waterway") or el.get("tags", {}).get("natural", "")
        for p in to_polygons(el):
            if p.is_valid and not p.is_empty:
                feats.append({"type": "Feature", "properties": {"kind": kind, "name": el.get("tags", {}).get("name", "")},
                              "geometry": mapping(p)})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": feats}), "utf-8")
    print(f"Đã lưu {len(feats)} vùng mặt nước vào {OUT}")


if __name__ == "__main__":
    main()
