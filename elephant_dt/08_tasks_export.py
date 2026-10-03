"""Bước 8: bảng đối chiếu, báo cáo (outputs/tasks_report.md) và dữ liệu web (web/data/tasks.js)."""
import json

import numpy as np
import pandas as pd

import config as C

C.utf8_stdout()


def ints(v, k=1, fill=-1):
    v = np.asarray(v, float)
    return [int(x) for x in np.where(np.isfinite(v), np.round(v * k), fill)]


def share(df, col, k=1):
    n = len(df)
    return [round(float((df[col] == c).mean()), 4) for c in range(2)] if n else [None, None]


def table(df, grp, col, order=None):
    out = []
    for g, sub in df.groupby(grp, observed=True):
        out.append({"group": str(g), "n": int(len(sub)), "share": share(sub, col)})
    return out


def eda(w, d):
    """Bảng mô tả trên 2007–2008 (fit + validation). 2009 không dùng."""
    g = w[w.period.isin(["fit", "val"])].copy()
    res = {}
    # --- nghỉ / di chuyển ---
    r = g[g.good].copy()
    r["rest"] = (r.y_rest == 0).astype(int)
    r["y_rest"] = r.y_rest.astype(int)
    slot = (np.round(r.hour * 60 / 90).astype(int) % 16)
    res["rest_by_hour"] = [round(float(r.rest[slot == s].mean()), 4) for s in range(16)]
    r["place"] = np.where(r.dw_km * 1000 <= C.WATER_BUFFER_M, "Ở nguồn nước (≤ 200 m)", "Xa nước (> 200 m)")
    r["when"] = pd.cut(r.hour, [-0.01, 4.5, 6, 18, 24], labels=["00:00–04:30", "04:30–06:00", "06:00–18:00", "18:00–24:00"], right=False)
    res["rest_place"] = [{"place": p, "when": str(wn), "n": int(len(s)), "rest": round(float(s.rest.mean()), 4)}
                         for (p, wn), s in r.groupby(["place", "when"], observed=True)]
    night = r[r.hour < 4.5]
    kn = night[night.woody_missing == 0]
    wb = pd.cut(kn.woody, [0, 15, 30, 45, 60, 101], labels=["0–15", "15–30", "30–45", "45–60", "> 60"], include_lowest=True)
    res["rest_woody_night"] = [{"group": str(k), "n": int(len(s)), "rest": round(float(s.rest.mean()), 4)} for k, s in kn.groupby(wb, observed=True)]
    core = r[(r.hour >= 0.7) & (r.hour < 3.8)]
    res["rest_by_id_core"] = sorted([{"group": str(k), "n": int(len(x)), "rest": round(float(x.rest.mean()), 4)} for k, x in core.groupby("id")],
                                    key=lambda q: -q["rest"])
    day = r[r.hour.between(9, 15)]
    tb = pd.cut(day.temp, [-np.inf, 25, 30, 35, 40, np.inf], labels=["< 25", "25–30", "30–35", "35–40", "≥ 40"])
    res["rest_temp_day"] = [{"group": str(k), "n": int(len(s)), "rest": round(float(s.rest.mean()), 4)} for k, s in day.groupby(tb, observed=True)]
    # --- quay lại nước ---
    a = g[g.y_water.notna() & g.hours_since_water.notna()].copy()
    a["y"] = a.y_water.astype(int)
    a["slot"] = (np.round(a.hour * 60 / 90).astype(int) % 16)
    near = a[a.dw_km.between(0.3, 1.5)]
    res["water_by_hour"] = [{"n": int((near.slot == s).sum()), "p": round(float(near.y[near.slot == s].mean()), 4)} for s in range(16)]
    res["water_by_hour_all"] = [round(float(a.y[a.slot == s].mean()), 4) for s in range(16)]
    ctl = near[near.hour.between(6, 16)]
    res["water_control"] = {"n": int(len(ctl)), "p": round(float(ctl.y.mean()), 4)}

    def grp(df, col, bins=None, labels=None):
        key = pd.cut(df[col], bins, labels=labels, include_lowest=True) if bins else df[col]
        return [{"group": str(k), "n": int(len(s)), "p": round(float(s.y.mean()), 4)} for k, s in df.groupby(key, observed=True)]
    res["water_temp"] = grp(ctl, "temp", [0, 25, 30, 35, 40, 99], ["≤ 25", "25–30", "30–35", "35–40", "> 40"])
    kc = ctl[ctl.woody_missing == 0]
    res["water_woody"] = grp(kc, "woody", [0, 25, 35, 45, 101], ["0–25", "25–35", "35–45", "> 45"])
    ctl2 = ctl.assign(season=np.where(ctl.wet == 1, "Mùa mưa", "Mùa khô"))
    res["water_season"] = grp(ctl2, "season")
    h6 = a[a.hour.between(6, 16)]
    res["water_dist"] = grp(h6, "dw_km", [0, 0.3, 0.6, 1, 2, 4, 99], ["< 0,3 km", "0,3–0,6", "0,6–1", "1–2", "2–4", "> 4 km"])
    res["water_hsw"] = grp(ctl, "hours_since_water", [0, 3, 6, 12, 24, 48, 9999], ["< 3 h", "3–6", "6–12", "12–24", "24–48", "> 48 h"])
    # --- đi nhanh / chậm ban ngày (khi voi đi) ---
    sp = g[g.y_speed.notna()].copy()
    sp["fast"] = sp.y_speed.astype(int)
    sp["thr"] = float(sp[sp.period == "fit"].next_path_m.median())
    def spd(df, col, bins=None, labels=None):
        key = pd.cut(df[col], bins, labels=labels, include_lowest=True) if bins else df[col]
        return [{"group": str(k), "n": int(len(x)), "fast": round(float(x.fast.mean()), 4), "path": int(x.next_path_m.median())}
                for k, x in df.groupby(key, observed=True)]
    ks = sp[sp.woody_missing == 0]
    res["speed"] = {"threshold": int(sp.thr.iloc[0]), "n": int(len(sp)), "fast": round(float(sp.fast.mean()), 4),
                    "woody": spd(ks, "woody_mean_300m", [0, 25, 35, 45, 101], ["0–25", "25–35", "35–45", "> 45"]),
                    "temp": spd(sp, "temp", [0, 25, 30, 35, 40, 99], ["≤ 25", "25–30", "30–35", "35–40", "> 40"]),
                    "season": spd(sp.assign(season=np.where(sp.wet == 1, "Mùa mưa", "Mùa khô")), "season"),
                    "hour": spd(sp, "hour", [6, 9, 12, 15, 18], ["06–09", "09–12", "12–15", "15–18"])}
    # --- ở lại / rời vùng nước ---
    st = g[g.y_stay.notna()].copy()
    st["stay"] = st.y_stay.astype(int)
    st["slot"] = (np.round(st.hour / 3) * 3).astype(int) % 24
    kw = st[st.woody_missing == 0]
    wb2 = pd.cut(kw.woody_mean_300m, [0, 30, 40, 101], labels=["0–30", "30–40", "> 40"], include_lowest=True)
    res["stay"] = {"n": int(len(st)), "share": round(float(st.stay.mean()), 4),
                   "hour": [{"group": f"{h:02d}h", "n": int((st.slot == h).sum()), "stay": round(float(st.stay[st.slot == h].mean()), 4)} for h in range(0, 24, 3)],
                   "woody_night": [{"group": str(k), "n": int(len(x)), "stay": round(float(x.stay.mean()), 4)}
                                   for k, x in kw[kw.hour < 4.5].groupby(wb2[kw.hour < 4.5], observed=True)]}
    # --- chuyến đi (Hình 2 của paper) từ segments.csv ---
    seg = pd.read_csv(C.OUT / "segments.csv")
    seg["year"] = d.time_local.dt.year.values[seg.start_idx.values]
    seg["tstart"] = d.time_local.values[seg.start_idx.values]
    s = seg[seg.year < 2009]
    hist = lambda col: [int(((s[col].values // 1).astype(int) % 24 == h).sum()) for h in range(24)]
    res["trips"] = {"n": int(len(s)), "leave_hour": hist("start_hour"), "return_hour": hist("end_hour"),
                    "duration_h": {"dry": round(float(s.duration_h[s.wet == 0].median()), 1), "wet": round(float(s.duration_h[s.wet == 1].median()), 1)},
                    "path_km": {"dry": round(float(s.path_km[s.wet == 0].median()), 1), "wet": round(float(s.path_km[s.wet == 1].median()), 1)},
                    "max_dw_km": {"dry": round(float(s.max_dw_km[s.wet == 0].median()), 1), "wet": round(float(s.max_dw_km[s.wet == 1].median()), 1)},
                    "n_season": {"dry": int((s.wet == 0).sum()), "wet": int((s.wet == 1).sum())}}
    return res


def web_data(trees, metrics, e, pred):
    start = pd.Timestamp(C.SPLIT_DATE) - pd.Timedelta(days=3)
    t0 = (start - pd.Timedelta(hours=C.LOCAL_UTC_OFFSET_H)).floor("D")
    t0_min = t0.value // 60_000_000_000
    els = {}
    for eid, p in pred.groupby("id"):
        p = p.sort_values("t_utc_min")
        k = 1e5
        els[eid] = {"t": [int(round(v - t0_min)) for v in p.t_utc_min], "lon": ints(p.lon, k), "lat": ints(p.lat, k),
                    "wx": ints(np.round(p.wlon * k) - np.round(p.lon * k)), "wy": ints(np.round(p.wlat * k) - np.round(p.lat * k)),
                    "dw": ints(p.dw_m), "temp": ints(p.temp), "woody": ints(p.woody, 10), "hsw": ints(p.hours_since_water, 10),
                    "apath": ints(p.apath), "mtw": ints(p.minutes_to_water),
                    **{f"{c}_{kk}": [int(v) for v in p[f"{c}_{kk}"]] for kk in trees["trees"] for c in ["actual", "pred", "leaf"]},
                    **{f"conf_{kk}": ints(p[f"conf_{kk}"], 100) for kk in trees["trees"]}}
    tasks = {}
    for key, tr in trees["trees"].items():
        m = metrics["tasks"][key]
        tasks[key] = {**tr, "metrics": {x: m[x] for x in ["val", "2009", "ablation", "permutation_val", "leaves", "rules_stable", "rules_total",
                                                          "baselines", "share", "n", "confusion_2009"]}}
    return {"feature_labels": trees["feature_labels"], "tasks": tasks, "eda": e, "elephants": els,
            "speed_threshold_m": metrics["speed_threshold_m"], "stay_m": metrics["stay_m"]}


def report(trees, metrics, e):
    pct = lambda v: "—" if v is None else f"{100 * v:.1f}%".replace(".", ",")
    f2 = lambda v: "—" if v is None else f"{v:.2f}".replace(".", ",")
    lab = trees["feature_labels"]

    def cond(steps):
        b = {}
        for f, op, v in steps:
            lo, hi = b.get(f, (None, None))
            lo, hi = (lo, v if hi is None else min(hi, v)) if op == "<=" else (v if lo is None else max(lo, v), hi)
            b[f] = (lo, hi)
        out = []
        for f, (lo, hi) in b.items():
            fv = (lambda x: f"{int(x):02d}:{int(round((x % 1) * 60)):02d}") if f == "hour" else (lambda x: f"{x:.2f}".replace(".", ","))
            if f == "wet":
                out.append("mùa mưa" if lo is not None else "mùa khô")
            elif f == "woody_missing":
                out.append("thiếu dữ liệu cây gỗ" if lo is not None else "có dữ liệu cây gỗ")
            elif lo is not None and hi is not None:
                out.append(f"{fv(lo)} < {lab[f]} ≤ {fv(hi)}")
            elif hi is not None:
                out.append(f"{lab[f]} ≤ {fv(hi)}")
            else:
                out.append(f"{lab[f]} > {fv(lo)}")
        return " · ".join(out)

    def rules(key):
        t = trees["trees"][key]
        rows = ["| Dự đoán | Điều kiện | Mẫu (voi) | Lift fit / val / 2009 | Voi lift > 1 (2007–08 · 2009) | Ổn định |", "|---|---|---:|---|---|---|"]
        for r in sorted(t["rules"], key=lambda r: (not r["stable"], r["pred"], -r["lift"])):
            rows.append(f"| {t['classes'][r['pred']]} | {cond(r['steps'])} | {r['n']:,} ({r['n_ids']}) | {f2(r['lift_fit'])} / {f2(r['lift_val'])} / {f2(r['lift_2009'])} | "
                        f"{r['ids_lift_gt1']}/{r['ids_eval']} · {r['ids_lift_gt1_2009']}/{r['ids_eval_2009']} | {'có' if r['stable'] else 'chưa'} |")
        return "\n".join(rows)

    def model_rows(key, _=None):
        m = metrics["tasks"][key]
        b = m["baselines"]
        rows = [f"| Cây ({m['leaves']} luật) | {f2(m['val']['macro_f1'])} | {f2(m['2009']['macro_f1'])} | {pct(m['2009']['acc'])} |",
                f"| Luôn đoán lớp đông nhất | {f2(b['val']['majority']['macro_f1'])} | {f2(b['2009']['majority']['macro_f1'])} | {pct(b['2009']['majority']['acc'])} |"]
        abl = ["| Bỏ nhóm feature | macro-F1 validation | macro-F1 2009 |", "|---|---:|---:|", f"| Không bỏ | {f2(m['val']['macro_f1'])} | {f2(m['2009']['macro_f1'])} |"]
        abl += [f"| {a['dropped']} | {f2(a['val']['macro_f1'])} | {f2(a['2009']['macro_f1'])} |" for a in m["ablation"]]
        return "\n".join(rows), "\n".join(abl)

    def tab(rows, head, col="p", label="Xác suất về nước trong 3 giờ"):
        return f"| {head} | Số mẫu | {label} |\n|---|---:|---:|\n" + "\n".join(f"| {r['group']} | {r['n']:,} | {pct(r[col])} |" for r in rows)

    tr = e["trips"]
    rest_tab = "\n".join(f"| {r['place']} | {r['when']} | {r['n']:,} | {pct(r['rest'])} |" for r in e["rest_place"])
    rr, ra = model_rows("rest")
    wr, wa = model_rows("water")
    mr, mw = metrics["tasks"]["rest"], metrics["tasks"]["water"]
    md = f"""# Bốn câu hỏi cho Decision Tree về hành vi di chuyển của voi

Dữ liệu GPS 14 voi, 08/2007–08/2009, cửa sổ 90 phút. Chia theo thời gian: fit 08/2007–06/2008, validation 07–12/2008,
2009 chỉ để đối chiếu (đã được xem ở các phiên bản trước nên không dùng để chọn cấu hình). Feature chỉ lấy từ GPS tại hoặc
trước mốc dự báo; cây không biết voi vừa làm gì để không chỉ học quán tính.

## Câu hỏi 1. Voi nghỉ hay di chuyển trong 90 phút tới?

**Nghỉ** = tổng đường đi < 75 m trong 90 phút (dưới mức này độ thẳng quỹ đạo gần như nhiễu GPS). Chưa khẳng định ngủ.
Tỉ lệ nghỉ: {pct(mr['share']['fit'][0])} (fit), {pct(mr['share']['2009'][0])} (2009).

| Mô hình | macro-F1 validation | macro-F1 2009 (đối chiếu) | Accuracy 2009 |
|---|---:|---:|---:|
{rr}

{ra}

### Luật
{rules("rest")}

### Nghỉ xảy ra khi nào, ở gần hay xa nước? (2007–2008)
| Vị trí | Giờ | Số cửa sổ | Tỉ lệ nghỉ |
|---|---|---:|---:|
{rest_tab}

Nghỉ tập trung từ nửa đêm tới khoảng 4 giờ sáng và xảy ra gần như nhau ở gần lẫn xa nguồn nước: nghỉ không gắn với việc ở cạnh nước.

Ban đêm (00:00–04:30), cây gỗ càng rậm càng nghỉ nhiều:
{tab(e['rest_woody_night'], 'Cây gỗ %', 'rest', 'Tỉ lệ nghỉ')}

Ban ngày (09:00–15:00), nhiệt độ không đổi nhiều tỉ lệ nghỉ:
{tab(e['rest_temp_day'], '°C', 'rest', 'Tỉ lệ nghỉ')}

## Câu hỏi 2. Voi đang ở xa nước (> 200 m) có quay lại vùng nước trong 3 giờ tới không?

**Về nước** = có điểm GPS trong vùng 200 m quanh nguồn nước trong 3 giờ tới (GPS không trống > 60 phút). Đây là xu hướng
quay lại nước, chưa quan sát được voi có uống hay không. Tỉ lệ về nước: {pct(mw['share']['fit'][1])} (fit), {pct(mw['share']['2009'][1])} (2009).

| Mô hình | macro-F1 validation | macro-F1 2009 (đối chiếu) | Accuracy 2009 |
|---|---:|---:|---:|
{wr}

{wa}

Khoảng cách tới nước là yếu tố mạnh nhất nhưng hiển nhiên (càng gần càng dễ về). Vì vậy các bảng dưới cố định giờ (06:00–16:00)
và khoảng cách (0,3–1,5 km): n = {e['water_control']['n']:,}, tỉ lệ chung {pct(e['water_control']['p'])}.

{tab(e['water_temp'], 'Nhiệt độ vòng cổ °C')}

Nhiệt độ cao đi kèm xu hướng quay lại nước nhiều hơn dù đã cố định giờ và khoảng cách.

{tab(e['water_woody'], 'Cây gỗ %')}
{tab(e['water_season'], 'Mùa (lịch quy ước)')}
{tab(e['water_hsw'], 'Thời gian đã rời nước')}

Theo khoảng cách (06:00–16:00):
{tab(e['water_dist'], 'Khoảng cách tới nước')}

### Luật
{rules("water")}

## Câu hỏi 3. Ban ngày, khi voi đi, đi nhanh hay chậm?

Chỉ xét cửa sổ 06:00–18:00 mà voi đi (đường đi ≥ 75 m). **Nhanh** = đường đi 90 phút trên {e['speed']['threshold']} m (trung vị của dữ liệu học).
Ví dụ: voi cho cây dự đoán tốc độ *nếu* nó đi; cây không biết trước voi có đi hay không.

| Mô hình | macro-F1 validation | macro-F1 2009 (đối chiếu) | Accuracy 2009 |
|---|---:|---:|---:|
{model_rows("speed")[0]}

{model_rows("speed")[1]}

Tỉ lệ đi nhanh theo cây gỗ ~300 m (2007–2008):
{tab(e['speed']['woody'], 'Cây gỗ %', 'fast', 'Đi nhanh')}
Theo mùa:
{tab(e['speed']['season'], 'Mùa', 'fast', 'Đi nhanh')}
Theo nhiệt độ vòng cổ:
{tab(e['speed']['temp'], '°C', 'fast', 'Đi nhanh')}

### Luật
{rules("speed")}

## Câu hỏi 4. Voi đang ở trong vùng nước (≤ 200 m) ở lại hay rời đi?

**Ở lại** = đi dưới {metrics['stay_m']} m trong 90 phút tới. Chưa phân biệt được uống nước, tắm hay nghỉ.

| Mô hình | macro-F1 validation | macro-F1 2009 (đối chiếu) | Accuracy 2009 |
|---|---:|---:|---:|
{model_rows("stay")[0]}

{model_rows("stay")[1]}

Tỉ lệ ở lại theo giờ (2007–2008):
{tab(e['stay']['hour'], 'Giờ', 'stay', 'Ở lại')}

### Luật
{rules("stay")}

## Chuyến đi giữa hai lần ghé nước (Hình 2 của paper), 2007–2008
{tr['n']:,} chuyến (mùa khô {tr['n_season']['dry']:,}, mùa mưa {tr['n_season']['wet']:,}). Trung vị thời lượng {tr['duration_h']['dry']} giờ (khô) và
{tr['duration_h']['wet']} giờ (mưa); đường đi {tr['path_km']['dry']} / {tr['path_km']['wet']} km; xa nước nhất {tr['max_dw_km']['dry']} / {tr['max_dw_km']['wet']} km.

## Giới hạn
- Nhãn là hình học quỹ đạo và khoảng cách tới lớp nước của dự án; không quan sát được ngủ, ăn hay uống.
- Cửa sổ 90 phút có ~4 điểm GPS; GPS thiếu làm đường đi ngắn đi (đã loại cửa sổ trống > 60 phút).
- "Ổn định" = lift > 1,1 ở validation và 2009, và > 1 ở ít nhất 2/3 số voi đủ mẫu. Lift fit/validation là trong mẫu.
- Mùa theo lịch quy ước; cây gỗ là bề mặt nội suy của tác giả; liên hệ không đồng nghĩa nhân quả.
"""
    (C.OUT / "tasks_report.md").write_text(md, "utf-8")


def main():
    w = pd.read_parquet(C.OUT / "tasks_windows.parquet")
    d = pd.read_parquet(C.OUT / "points_states.parquet", columns=["time_local"])
    trees = json.loads((C.OUT / "tasks_trees.json").read_text("utf-8"))
    metrics = json.loads((C.OUT / "tasks_metrics.json").read_text("utf-8"))
    pred = pd.read_parquet(C.OUT / "tasks_pred.parquet")
    e = eda(w, d)
    report(trees, metrics, e)
    data = web_data(trees, metrics, e, pred)
    txt = json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    (C.WEB_DATA / "tasks.js").write_text(f"window.KNP_TASKS={txt};\n", "utf-8")
    print(f"tasks.js: {len(txt) / 1e6:.1f} MB · {len(data['elephants'])} voi · báo cáo: {C.OUT / 'tasks_report.md'}")


if __name__ == "__main__":
    main()
