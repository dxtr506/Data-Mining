"""Số liệu mô tả sâu cho từng cây (không huấn luyện gì thêm): nghỉ, về nước, tốc độ, ở nước.

Đọc outputs/tasks_windows.parquet (cửa sổ 90 phút, nhãn của 4 cây) và outputs/segments.csv,
ghi outputs/behavior_stats.md. Mọi bảng tách "học" (2007-2008) và "2009" để thấy pattern có giữ nguyên không.
"""
import numpy as np
import pandas as pd

import config as C

C.utf8_stdout()
d = pd.read_parquet(C.OUT / "tasks_windows.parquet")
d = d[d.good & d.period.isin(["fit", "val", "2009"])].copy()
d["grp"] = np.where(d.period == "2009", "2009", "học")
d["day"] = ((d.t_utc_min + C.LOCAL_UTC_OFFSET_H * 60) // 1440).astype(int)
d["season"] = np.where(d.wet == 1, "mùa mưa", "mùa khô")
d["at_water"] = d.dw_km * 1000 <= C.WATER_BUFFER_M
d["hh"] = d.hour.map(lambda h: f"{int(h):02d}:{int(round((h % 1) * 60)):02d}")
HOURS = sorted(d.hour.unique())
out = []


def pct(x, nd=1):
    return "—" if pd.isna(x) else f"{100 * x:.{nd}f}%".replace(".", ",")


def table(df, title, fmt=None):
    out.append(f"\n**{title}**\n")
    cols = list(df.columns)
    out.append("| " + " | ".join(map(str, [df.index.name or ""] + cols)) + " |")
    out.append("|" + "---|" * (len(cols) + 1))
    for idx, row in df.iterrows():
        cells = [f"{int(v):,}".replace(",", ".") if isinstance(v, (int, np.integer)) or str(c).startswith("số") else (fmt(v) if fmt and not isinstance(v, str) else str(v))
                 for c, v in row.items()]
        out.append("| " + " | ".join([str(idx)] + cells) + " |")


def by(df, key, ycol, bins=None, labels=None):
    g = df[key] if bins is None else pd.cut(df[key], bins, labels=labels)
    r = df.groupby([g, "grp"], observed=True)[ycol].agg(["mean", "size"]).unstack("grp")
    return r


def share_table(df, key, ycol, bins=None, labels=None, name=None):
    r = by(df, key, ycol, bins, labels)
    t = pd.DataFrame({"học": r["mean"]["học"], "n học": r["size"]["học"], "2009": r["mean"]["2009"], "n 2009": r["size"]["2009"]})
    t.index.name = name or key
    return t


def fmt_cell(v):
    if isinstance(v, (int, np.integer)) or (isinstance(v, float) and v.is_integer() and v > 1):
        return f"{int(v):,}".replace(",", ".")
    return pct(v)


# ---------------- Cây 1: nghỉ ----------------
out.append("# Số liệu mô tả cho từng cây\n")
out.append("Nguồn: `tasks_windows.parquet`, cửa sổ 90 phút đủ chất lượng. \"học\" = 08/2007–12/2008, \"2009\" = đối chiếu. Giờ địa phương (UTC+2).")
out.append("\n## Cây 1. Nghỉ\n")
r = d[d.y_rest.notna()].copy()
r["rest"] = (r.y_rest == 0).astype(int)      # y_rest: 0 = nghỉ, 1 = di chuyển
t = share_table(r, "hh", "rest", name="Giờ")
table(t, "1.1 Tỉ lệ cửa sổ nghỉ theo giờ (mốc bắt đầu cửa sổ 90 phút)", fmt_cell)

core = r[r.hour.isin([1.5, 3.0])]
t = core.groupby(["season", "grp"]).rest.mean().unstack()
t.index.name = "Mùa"
table(t, "1.2 Nghỉ trong khung 00:45–03:45 theo mùa", fmt_cell)

# Mỗi voi: ngày đủ 16 cửa sổ -> số giờ nghỉ / ngày
full = r.groupby(["id", "day"]).filter(lambda g: len(g) == 16)
dd = full.groupby(["id", "day", "grp"]).rest.sum().mul(1.5).reset_index(name="rest_h")
q = dd.groupby("grp").rest_h.describe(percentiles=[.25, .5, .75])
t = pd.DataFrame({"số ngày": q["count"].astype(int), "25%": q["25%"], "trung vị": q["50%"], "75%": q["75%"], "trung bình": q["mean"]})
t.index.name = "Nhóm"
table(t, "1.3 Số giờ nghỉ mỗi ngày (chỉ ngày có đủ 16 cửa sổ; ước lượng = số cửa sổ nghỉ × 1,5 giờ)", lambda v: f"{v:.1f}".replace(".", ","))

# Nghỉ nối liền: một "đợt nghỉ" = các cửa sổ nghỉ liên tiếp (cách nhau 90 phút)
r = r.sort_values(["id", "t_utc_min"])
r["new"] = (r.rest.eq(1) & ~(r.rest.shift().eq(1) & (r.t_utc_min.diff() == 90) & (r.id == r.id.shift()))).astype(int)
r["bout"] = r.new.cumsum()
bouts = r[r.rest == 1].groupby("bout").agg(grp=("grp", "first"), n=("rest", "size"), start=("hour", "first"), id=("id", "first"))
bouts["start_h"] = bouts.start
q = bouts.groupby("grp").n.agg(["size", "median", "mean", "max"])
t = pd.DataFrame({"số đợt": q["size"].astype(int), "trung vị (cửa sổ)": q["median"].astype(int), "trung bình": q["mean"], "dài nhất": q["max"].astype(int)})
t.index.name = "Nhóm"
table(t, "1.4 Đợt nghỉ liên tiếp (một cửa sổ = 90 phút, nên 2 cửa sổ liên tiếp ≈ 3 giờ nghỉ)", lambda v: f"{v:.2f}".replace(".", ","))
dist = bouts.groupby(["grp", pd.cut(bouts.n, [0, 1, 2, 3, 99], labels=["1", "2", "3", "≥4"])], observed=True).size().unstack(0)
dist = dist.div(dist.sum())
dist.index.name = "Số cửa sổ liên tiếp"
table(dist, "Tỉ lệ đợt nghỉ theo độ dài", fmt_cell)

t = r[r.hour.isin([1.5, 3.0])].groupby(["id", "grp"]).rest.mean().unstack()
t.index.name = "Voi"
table(t, "1.5 Từng voi: tỉ lệ nghỉ trong khung 00:45–03:45", fmt_cell)
t = share_table(r[r.hour.isin([0, 1.5, 3.0, 4.5])], "woody", "rest", bins=[-1, 15, 30, 45, 60, 101], labels=["0–15", "15–30", "30–45", "45–60", ">60"], name="Cây gỗ tại GPS (%), 00:00–06:00")
table(t, "1.6 Nghỉ ban đêm theo cây gỗ", fmt_cell)
t = share_table(r[r.hour.isin([0, 1.5, 3.0, 4.5])], "dw_km", "rest", bins=[-1, 0.2, 0.5, 1, 2, 99], labels=["≤0,2", "0,2–0,5", "0,5–1", "1–2", ">2"], name="Cách nước (km), 00:00–06:00")
table(t, "1.7 Nghỉ ban đêm theo khoảng cách tới nước", fmt_cell)
nt = r[r.hour.isin([0, 1.5, 3.0, 4.5])].groupby(["id", "day", "grp"]).rest.agg(["size", "sum"]).reset_index()
nt = nt[nt["size"] == 4]
for g in ["học", "2009"]:
    x = nt[nt.grp == g]
    out.append(f"\nĐêm đủ 4 cửa sổ 00:00–06:00 ({g}, {len(x)} đêm-voi): có ít nhất 1 cửa sổ nghỉ {pct((x['sum'] >= 1).mean())}; ít nhất 2 cửa sổ nghỉ {pct((x['sum'] >= 2).mean())}; không nghỉ lần nào {pct((x['sum'] == 0).mean())}.")
for g in ["học", "2009"]:
    x = r[(r.grp == g) & (r.rest == 1)]
    out.append(f"Trong các cửa sổ nghỉ ({g}), {pct(x.hour.isin([0, 1.5, 3.0, 4.5]).mean())} nằm ở 4 mốc 00:00–04:30; {pct(x.hour.isin([22.5, 0, 1.5, 3.0, 4.5]).mean())} nếu tính cả 22:30.")
out.append("\nBan ngày, tỉ lệ nghỉ trung bình 06:00–18:00 (học / 2009): "
           + " / ".join(pct(r[(r.hour >= 6) & (r.hour < 18) & (r.grp == g)].rest.mean()) for g in ["học", "2009"])
           + f". Nghỉ lúc 10:30–12:00: " + " / ".join(pct(r[r.hour.isin([10.5, 12.0]) & (r.grp == g)].rest.mean()) for g in ["học", "2009"]) + ".")

# ---------------- Cây 2: về nước ----------------
out.append("\n## Cây 2. Về nước\n")
w = d[d.y_water.notna() & ~d.at_water].copy()
w["near"] = w.dw_km.between(0.3, 1.5)
sub = w[w.near]
t = share_table(sub, "hh", "y_water", name="Giờ")
table(t, "2.1 Xác suất về nước trong 3 giờ theo giờ, chỉ voi cách nước 0,3–1,5 km", fmt_cell)
t = share_table(w, "dw_km", "y_water", bins=[0.2, 0.3, 0.6, 1, 2, 4, 99], labels=["0,2–0,3", "0,3–0,6", "0,6–1", "1–2", "2–4", ">4"], name="Cách nước (km)")
table(t, "2.2 Theo khoảng cách (mọi giờ)", fmt_cell)
dn = w.assign(period_of_day=np.where((w.hour >= 6) & (w.hour < 18), "ban ngày 06–18", "ban đêm 18–06"))
t = (dn[dn.near].groupby(["period_of_day", "grp"]).y_water.mean().unstack())
t.index.name = "Thời điểm"
table(t, "2.3 Ban ngày và ban đêm (cùng khoảng cách 0,3–1,5 km)", fmt_cell)
t = dn[dn.near].groupby(["season", "grp"]).y_water.mean().unstack()
t.index.name = "Mùa"
table(t, "2.4 Theo mùa (0,3–1,5 km)", fmt_cell)
day_near = dn[dn.near & (dn.period_of_day == "ban ngày 06–18")]
t = share_table(day_near, "temp", "y_water", bins=[-50, 25, 30, 35, 99], labels=["≤25", "25–30", "30–35", ">35"], name="Nhiệt độ (°C), 06–18h, 0,3–1,5 km")
table(t, "2.5 Theo nhiệt độ vòng cổ", fmt_cell)
seg = pd.read_csv(C.OUT / "segments.csv")
out.append("\n**2.6 Chuyến giữa hai lần ghé nước** (cả 2007–2009, nguồn `segments.csv`)\n")
out.append(f"- Số chuyến: {len(seg):,} của {seg.id.nunique()} voi.".replace(",", "."))
for wet, name in [(0, "mùa khô"), (1, "mùa mưa")]:
    sg = seg[seg.wet == wet]
    out.append(f"- {name} ({len(sg):,} chuyến): thời lượng trung vị {sg.duration_h.median():.1f} giờ; đường đi {sg.path_km.median():.1f} km; xa nước nhất {sg.max_dw_km.median():.1f} km.".replace(",", "."))
for col, name in [("start_hour", "Giờ rời nước"), ("end_hour", "Giờ về nước")]:
    h = (seg[col] // 3 * 3).astype(int).value_counts(normalize=True).sort_index()
    out.append(f"- {name} theo khung 3 giờ: " + ", ".join(f"{k:02d}–{k + 3:02d}h {pct(v, 0)}" for k, v in h.items()))
t = share_table(sub, "hours_since_water", "y_water", bins=[-1, 3, 6, 12, 24, 48, 999], labels=["<3 h", "3–6", "6–12", "12–24", "24–48", ">48"], name="Đã rời nước")
table(t, "2.7 Tỉ lệ về nước trong 3 giờ theo thời gian đã rời nước", fmt_cell)

# ---------------- Cây 3: tốc độ ----------------
out.append("\n## Cây 3. Tốc độ ban ngày khi voi đi\n")
s = d[d.y_speed.notna()].copy()
thr = float(np.median(s[s.period == "fit"].next_path_m))
out.append(f"Ngưỡng nhanh/chậm (trung vị tập fit 08/2007–06/2008, đúng ngưỡng cây dùng): {thr:.0f} m / 90 phút ≈ {thr / 1.5 / 1000:.2f} km/giờ trung bình.")
out.append("Trung vị đường đi (m / 90 phút) khi voi đi ban ngày: " + " / ".join(f"{g} {s[s.grp == g].next_path_m.median():.0f}" for g in ["học", "2009"]) + ".")
dayall = d[(d.hour >= 6) & (d.hour < 18) & d.y_rest.notna()]
out.append("Tỉ lệ cửa sổ ban ngày voi có đi (≥ 75 m), học / 2009: " + " / ".join(pct((dayall[dayall.grp == g].y_rest == 1).mean()) for g in ["học", "2009"]) + ".")
t = share_table(s, "hh", "y_speed", name="Giờ")
table(t, "3.1 Tỉ lệ đi nhanh theo giờ", fmt_cell)
t = s.groupby(["season", "grp"]).y_speed.mean().unstack(); t.index.name = "Mùa"
table(t, "3.2 Theo mùa", fmt_cell)
t = share_table(s, "woody_mean_300m", "y_speed", bins=[-1, 25, 35, 45, 101], labels=["0–25", "25–35", "35–45", ">45"], name="Cây gỗ ~300 m (%)")
table(t, "3.3 Theo cây gỗ", fmt_cell)
t = s.groupby([pd.cut(s.woody_mean_300m, [-1, 35, 45, 101], labels=["≤35%", "35–45%", ">45%"]), "season", "grp"], observed=True).y_speed.mean().unstack(["season", "grp"])
t.index.name = "Cây gỗ ~300 m"
t.columns = [f"{a} · {b}" for a, b in t.columns]
table(t, "3.4 Cây gỗ × mùa", fmt_cell)
t = s.groupby([pd.cut(s.hours_since_water, [-1, 3, 6, 15, 999], labels=["<3 h", "3–6", "6–15", ">15"]), "season", "grp"], observed=True).y_speed.mean().unstack(["season", "grp"])
t.index.name = "Đã rời nước"
t.columns = [f"{a} · {b}" for a, b in t.columns]
table(t, "3.5 Thời gian đã rời nước × mùa", fmt_cell)
t = share_table(s, "temp", "y_speed", bins=[-50, 25, 30, 35, 99], labels=["≤25", "25–30", "30–35", ">35"], name="Nhiệt độ (°C)")
table(t, "3.6 Theo nhiệt độ vòng cổ", fmt_cell)

# ---------------- Cây 4: ở nước ----------------
out.append("\n## Cây 4. Ở nước\n")
z = d[d.y_stay.notna()].copy()
t = share_table(z, "hh", "y_stay", name="Giờ")
table(t, "4.1 Tỉ lệ ở lại vùng nước theo giờ (chỉ cửa sổ đang ở trong vùng 200 m)", fmt_cell)
allw = d.copy()
t = allw.groupby(["hh", "grp"]).at_water.mean().unstack(); t.index.name = "Giờ"
table(t, "4.2 Tỉ lệ cửa sổ voi đang ở trong vùng nước theo giờ (mọi cửa sổ)", fmt_cell)
night_all = allw[allw.hour.isin([0, 1.5, 3.0, 4.5])]
out.append("\nBan đêm (00:00–06:00), tỉ lệ cửa sổ ở trong vùng nước: " + " / ".join(pct(night_all[night_all.grp == g].at_water.mean()) for g in ["học", "2009"])
           + "; ban ngày 06:00–18:00: " + " / ".join(pct(allw[(allw.hour >= 6) & (allw.hour < 18) & (allw.grp == g)].at_water.mean()) for g in ["học", "2009"]) + ".")
t = z[z.hour.isin([0, 1.5, 3.0])].groupby(["season", "grp"]).y_stay.mean().unstack(); t.index.name = "Mùa (00:00–04:30)"
table(t, "4.3 Ở lại ban đêm theo mùa", fmt_cell)
t = share_table(z[z.hour.isin([0, 1.5, 3.0])], "woody", "y_stay", bins=[-1, 25, 37, 50, 101], labels=["0–25", "25–37", "37–50", ">50"], name="Cây gỗ tại GPS (%), 00–04:30")
table(t, "4.4 Ở lại ban đêm theo cây gỗ", fmt_cell)

(C.OUT / "behavior_stats.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
