"""Bước 1: làm sạch GPS, gán mùa, tính tốc độ và khoảng cách tới nguồn nước.

Quy tắc nguồn nước theo paper + code elephantTempKruger:
- Hố nước: điểm CURRENT == "Open" nằm trong vùng nghiên cứu (124 điểm).
- Sông/suối OSM: mùa khô chỉ dùng dòng chảy quanh năm; mùa mưa dùng cả dòng theo mùa.
- dw = khoảng cách Euclid (UTM 36S) tới nguồn nước gần nhất trong mùa đó.
"""
import json

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import shapely
from pyproj import Transformer

import config as C
from vegetation import sample_woody, source_metadata

C.utf8_stdout()
C.OUT.mkdir(parents=True, exist_ok=True)


def load_gps():
    d = pd.read_csv(C.GPS_CSV, parse_dates=["timestamp"])
    d = d.rename(columns={
        "individual-local-identifier": "id", "timestamp": "time_utc",
        "location-long": "lon", "location-lat": "lat", "external-temperature": "temp",
    })[["id", "time_utc", "lon", "lat", "temp"]]
    d = d.dropna().drop_duplicates(["id", "time_utc"]).sort_values(["id", "time_utc"])
    d["time_local"] = d.time_utc + pd.Timedelta(hours=C.LOCAL_UTC_OFFSET_H)
    return d.reset_index(drop=True)


def add_season(d):
    md = d.time_local.dt.month * 100 + d.time_local.dt.day
    start = C.WET_START[0] * 100 + C.WET_START[1]
    end = C.WET_END[0] * 100 + C.WET_END[1]
    d["wet"] = ((md >= start) | (md < end)).astype(np.int8)
    return d


def add_steps(d):
    to_utm = Transformer.from_crs("EPSG:4326", C.UTM, always_xy=True)
    d["x"], d["y"] = to_utm.transform(d.lon.values, d.lat.values)
    g = d.groupby("id", sort=False)
    d["dt_h"] = g.time_utc.diff().dt.total_seconds() / 3600
    d["step_m"] = np.hypot(g.x.diff(), g.y.diff())
    # Tốc độ từ điểm trước; bỏ bước qua khoảng mất tín hiệu dài
    ok = d.dt_h <= 2.05
    d["speed_kmh"] = np.where(ok, d.step_m / 1000 / d.dt_h, np.nan)
    d.loc[d.speed_kmh > 10, "speed_kmh"] = np.nan   # 4 bước > 10 km/h: lỗi GPS
    d["hour"] = d.time_local.dt.hour + d.time_local.dt.minute / 60
    return d


def load_water():
    study = gpd.read_file(C.KRUGER_SHP).to_crs(C.UTM).geometry.iloc[0]
    wh = gpd.read_file(C.WATERHOLES_SHP).to_crs(C.UTM)
    wh = wh[(wh.CURRENT == "Open") & wh.within(study)].copy()
    rv = gpd.read_file(C.RIVERS_SHP).to_crs(C.UTM)
    rv["perennial_flag"] = rv.seasonal.ne("yes")
    return study, wh, rv


def nearest(px, py, geoms):
    """Khoảng cách và toạ độ điểm gần nhất trên nguồn nước gần nhất."""
    geoms = np.asarray(geoms)
    tree = shapely.STRtree(geoms)
    pts = shapely.points(px, py)
    (ip, ig), dist = tree.query_nearest(pts, return_distance=True, all_matches=False)
    order = np.argsort(ip)
    ig, dist = ig[order], dist[order]
    near = shapely.get_point(shapely.shortest_line(pts, geoms[ig]), 1)
    return dist, shapely.get_x(near), shapely.get_y(near)


def sample_raster(path, x, y):
    with rasterio.open(path) as src:
        vals = np.array([v[0] for v in src.sample(zip(x, y))], dtype="float64")
        nodata = src.nodata
    if nodata is not None:
        vals[np.isclose(vals, nodata) | (vals < -1e30)] = np.nan
    return vals


def main():
    d = add_steps(add_season(load_gps()))
    study, wh, rv = load_water()

    x, y = d.x.values, d.y.values
    dist_wh, wh_x, wh_y = nearest(x, y, wh.geometry.values)
    dist_ra, ra_x, ra_y = nearest(x, y, rv.geometry.values)
    dist_rp, rp_x, rp_y = nearest(x, y, rv[rv.perennial_flag].geometry.values)
    wet = d.wet.values == 1
    river = np.where(wet, dist_ra, dist_rp)
    rx, ry = np.where(wet, ra_x, rp_x), np.where(wet, ra_y, rp_y)
    use_wh = dist_wh <= river
    d["dw"] = np.where(use_wh, dist_wh, river)
    d["water_kind"] = np.where(use_wh, "waterhole", "river")
    # Toạ độ nguồn nước gần nhất (để web vẽ hướng đi dự đoán)
    to_wgs = Transformer.from_crs(C.UTM, "EPSG:4326", always_xy=True)
    d["water_lon"], d["water_lat"] = to_wgs.transform(np.where(use_wh, wh_x, rx), np.where(use_wh, wh_y, ry))

    d["landsat_temp"] = sample_raster(C.LANDSAT_TIF, d.x.values, d.y.values)
    vegetation, woody_sampling = sample_woody(d.lon.values, d.lat.values)
    for key, values in vegetation.items():
        d[key] = values
    print("Đã thêm woody cover và đặc trưng lân cận từ", C.WOODY_TIF.name)

    d.to_parquet(C.OUT / "points.parquet", index=False)
    # Augmented copy preserves the source columns and every original observation.
    raw = pd.read_csv(C.GPS_CSV, dtype=str)
    raw["_join_time"] = pd.to_datetime(raw["timestamp"])
    cov = d[["id", "time_utc", "woody", "woody_mean_300m", "woody_std_300m", "woody_missing"]].rename(columns={
        "woody": "woody_cover_pct", "woody_mean_300m": "woody_cover_mean_300m_pct",
        "woody_std_300m": "woody_cover_std_300m_pct"})
    augmented = raw.merge(cov, left_on=["individual-local-identifier", "_join_time"],
                          right_on=["id", "time_utc"], how="left", validate="many_to_one", sort=False)
    augmented.drop(columns=["_join_time", "id", "time_utc"]).to_csv(C.OUT / "gps_with_woody.csv", index=False)

    dry, wet = d[d.wet == 0], d[d.wet == 1]
    summary = {
        "n_points": int(len(d)), "n_individuals": int(d.id.nunique()),
        "n_dry": int(len(dry)), "n_wet": int(len(wet)),
        "n_waterholes_open": int(len(wh)), "n_river_features": int(len(rv)),
        "n_river_perennial": int(rv.perennial_flag.sum()),
        "mean_dw_km_dry": round(dry.dw.mean() / 1000, 2),
        "mean_dw_km_wet": round(wet.dw.mean() / 1000, 2),
        "pct_within_200m": round(100 * (d.dw <= C.WATER_BUFFER_M).mean(), 1),
        "pct_within_200m_dry": round(100 * (dry.dw <= C.WATER_BUFFER_M).mean(), 1),
        "pct_within_200m_wet": round(100 * (wet.dw <= C.WATER_BUFFER_M).mean(), 1),
        "mean_speed_dry": round(dry.speed_kmh.mean(), 3),
        "mean_speed_wet": round(wet.speed_kmh.mean(), 3),
        "landsat_missing_pct": round(100 * d.landsat_temp.isna().mean(), 2),
        "woody_sampling": woody_sampling,
        "woody_source": source_metadata(),
        "woody_missing_pct": round(100 * d.woody.isna().mean(), 3),
        "woody_summary_pct": {"min": float(d.woody.min()), "median": float(d.woody.median()), "max": float(d.woody.max())},
        "woody_missing_by_individual": d.groupby("id").woody.apply(lambda v: int(v.isna().sum())).to_dict(),
    }
    (C.OUT / "prepare_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), "utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print("Paper: 1,5 km (khô) / 0,9 km (mưa); 21,6% điểm ≤200 m (19,6% khô, 23,5% mưa);"
          " tốc độ 0,39 (khô) / 0,42 km/h (mưa)")


if __name__ == "__main__":
    main()
