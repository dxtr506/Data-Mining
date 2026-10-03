"""Xuất đường đi thật của các voi có dữ liệu 2009 và các lớp bản đồ thành web/data/tracks.js, layers.js.

Chạy sau 07_tasks_tree.py (lấy danh sách voi từ tasks_pred.parquet). Dự đoán của cây nằm ở tasks.js (08_tasks_export.py)."""
import json

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

import config as C

C.utf8_stdout()
C.WEB_DATA.mkdir(parents=True, exist_ok=True)

def write_js(name, var, obj):
    txt = json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    (C.WEB_DATA / name).write_text(f"window.{var}={txt};\n", "utf-8")
    print(f"  {name}: {len(txt) / 1e6:.1f} MB")


def round_geojson(gdf, nd=5):
    gj = json.loads(gdf.to_json(drop_id=True))

    def rnd(c):
        return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(v, nd) for v in c]
    for f in gj["features"]:
        f["geometry"]["coordinates"] = rnd(f["geometry"]["coordinates"])
    return gj


def visible_area(d, study_utm):
    """Vùng hiện ảnh vệ tinh: vùng nghiên cứu + dải 1,5 km quanh những điểm GPS nằm ngoài nó."""
    pts = shapely.points(d.x.values[::2], d.y.values[::2])
    out = pts[~shapely.contains(study_utm, pts)]
    extra = shapely.union_all(shapely.buffer(out, 1500, quad_segs=4))
    area = shapely.union_all([study_utm, extra]).simplify(150)
    # chỉ giữ đường bao ngoài: lỗ nhỏ bên trong không cần che
    polys = list(area.geoms) if area.geom_type == "MultiPolygon" else [area]
    area = shapely.MultiPolygon([shapely.Polygon(g.exterior) for g in polys])
    return area


def layers(d):
    study = gpd.read_file(C.KRUGER_SHP).to_crs(4326)
    study_utm = study.to_crs(C.UTM).geometry.iloc[0]
    area_utm = visible_area(d, study_utm)
    wh = gpd.read_file(C.WATERHOLES_SHP)
    wh = wh[(wh.CURRENT == "Open") & wh.within(study_utm)].to_crs(4326)[["NAME", "TYPE", "geometry"]]
    wh.columns = ["name", "type", "geometry"]
    rv = gpd.read_file(C.RIVERS_SHP)
    rv["perennial"] = rv.seasonal.ne("yes").astype(int)
    rv["name"] = rv["name"].fillna("")
    rv = rv[["name", "waterway", "perennial", "geometry"]].copy()
    rv["geometry"] = rv.geometry.simplify(15)
    rv = gpd.clip(rv, area_utm)
    rv = rv[~rv.geometry.is_empty].explode(index_parts=False).to_crs(4326)
    rv = rv[rv.geom_type == "LineString"]
    study["geometry"] = study.to_crs(C.UTM).geometry.simplify(50).to_crs(4326)
    area = gpd.GeoDataFrame(geometry=[area_utm], crs=C.UTM).to_crs(4326)
    out = {"boundary": round_geojson(study[["geometry"]]), "area": round_geojson(area),
           "rivers": round_geojson(rv), "waterholes": round_geojson(wh)}
    # Vùng mặt nước OSM (hồ, đập, lòng sông) để thấy rõ khi phóng to; có khi đã chạy 00_get_osm_water.py
    osm = C.ROOT / "data" / "osm_water.geojson"
    if osm.exists():
        wa = gpd.read_file(osm).set_crs(4326, allow_override=True).to_crs(C.UTM)
        wa["geometry"] = wa.geometry.simplify(4)
        wa = gpd.clip(wa, area_utm)
        wa = wa[~wa.geometry.is_empty & wa.geom_type.isin(["Polygon", "MultiPolygon"])].to_crs(4326)
        out["water"] = round_geojson(wa[["kind", "name", "geometry"]].fillna(""))
    return out


def tracks(d, ids):
    """Đường đi thật (30 phút / điểm) của các voi có dữ liệu năm 2009, bắt đầu từ 3 ngày trước ngày chia
    để vệt đi có sẵn lúc mở trang. Không chứa dự đoán hay nhãn."""
    d = d.reset_index(drop=True)
    start = pd.Timestamp(C.SPLIT_DATE) - pd.Timedelta(days=3)
    t0 = (start - pd.Timedelta(hours=C.LOCAL_UTC_OFFSET_H)).floor("D")
    els = []
    for eid in sorted(ids):
        rows = np.flatnonzero((d.id.values == eid) & (d.time_local.values >= np.datetime64(start)))
        g = d.iloc[rows]

        def ints(v, k=1, fill=-1):
            return [int(x) for x in np.where(np.isnan(v), fill, np.round(np.asarray(v, float) * k))]

        def delta(v):  # lưu độ chênh với điểm trước cho file nhỏ hơn; web cộng dồn lại
            v = np.asarray(v, dtype=np.int64)
            return [int(x) for x in np.r_[v[:1], np.diff(v)]]
        tmin = ((g.time_utc - t0).dt.total_seconds() / 60).round().astype(int).values
        els.append({
            "id": eid, "n": int(len(g)),
            "t": delta(tmin), "lon": delta(np.round(g.lon.values * 1e5)), "lat": delta(np.round(g.lat.values * 1e5)),
            "temp": ints(g.temp.values, 1, -99), "dw": ints(g.dw.values), "wet": [int(x) for x in g.wet.values],
            "hs": ints(g.hours_since_water.values, 10),     # h × 10
            "woody": ints(g.woody.values, 10, -1),          # % × 10; -1 = nodata
        })
    return {"t0": t0.strftime("%Y-%m-%dT%H:%M:%SZ"), "utc_offset_h": C.LOCAL_UTC_OFFSET_H, "delta": ["t", "lon", "lat"],
            "water_buffer_m": C.WATER_BUFFER_M, "elephants": els}


def main():
    d = pd.read_parquet(C.OUT / "points_states.parquet")
    pred = pd.read_parquet(C.OUT / "tasks_pred.parquet", columns=["id"])
    ids = pred.id.unique()
    print(f"Xuất đường đi và bản đồ: {len(ids)} voi có dữ liệu năm 2009")
    write_js("layers.js", "KNP_LAYERS", layers(d[d.id.isin(ids)]))
    write_js("tracks.js", "KNP_TRACKS", tracks(d, ids))


if __name__ == "__main__":
    main()
