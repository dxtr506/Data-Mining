"""Bước 2: tách chuyến đi giữa hai lần ghé nước như paper.

Dùng cho cây hướng đi: đặc trưng "thời gian từ lúc rời nước" (hours_since_water).
Phần còn lại tái lập số liệu của paper (số chuyến, Hình 6) để đối chiếu; không phải nhãn của cây.

Chuyến (segment): bắt đầu ở điểm đầu tiên ra khỏi vùng 200 m quanh nguồn nước (pt0),
kết thúc ở điểm đầu tiên quay lại vùng 200 m của một nguồn nước bất kỳ (ptn).

Trạng thái so với nguồn nước: tái hiện gần đúng thuật toán segclust2d mà paper dùng.
1. Tín hiệu là tốc độ thay đổi khoảng cách tới nước, Δdw/Δt (m/h).
2. Mỗi chuyến được chia tối ưu thành 1–5 pha (mỗi pha ≥ 5 điểm) bằng quy hoạch động,
   số pha chọn theo BIC.
3. Gán nhãn mỗi pha theo khoảng cách tới nước thay đổi bao nhiêu từ đầu đến cuối pha:
   tăng ≥ 500 m = rời xa nước, giảm ≥ 500 m = tiến về nước, còn lại = giữ khoảng cách.
"""
import json

import numpy as np
import pandas as pd

import config as C

C.utf8_stdout()


def find_segments(d):
    """Trả về danh sách (start_idx, end_idx) theo chỉ số dòng của d (end gồm điểm về tới nước)."""
    segs, dropped = [], {"gap": 0, "too_long": 0, "too_short": 0}
    at_water = (d.dw.values <= C.WATER_BUFFER_M)
    t = d.time_utc.values
    ids = d.id.values
    dt = d.dt_h.values
    starts = np.flatnonzero(np.r_[True, ids[1:] != ids[:-1]])
    ends = np.r_[starts[1:], len(d)]
    for s, e in zip(starts, ends):
        aw = at_water[s:e]
        i = 1
        n = e - s
        while i < n:
            if aw[i] or not aw[i - 1]:
                i += 1
                continue
            j = i                       # i: điểm đầu tiên rời nước
            while j < n and not aw[j]:
                j += 1
            if j >= n:                  # hết dữ liệu khi chưa quay lại nước
                break
            a, b = s + i, s + j         # b: điểm đầu tiên quay lại vùng 200 m
            npts = b - a + 1
            dur = (t[b] - t[a]) / np.timedelta64(1, "h")
            if np.nanmax(dt[a:b + 1]) > C.MAX_GAP_H:
                dropped["gap"] += 1
            elif dur >= C.MAX_SEGMENT_H:
                dropped["too_long"] += 1
            elif npts < C.MIN_SEGMENT_POINTS:
                dropped["too_short"] += 1
            else:
                segs.append((a, b))
            i = j + 1
    return segs, dropped


def segment_series(y, min_len, max_k):
    """Phân đoạn bình phương tối thiểu tối ưu, chọn số pha theo BIC. Trả về nhãn pha 0..K-1."""
    n = len(y)
    s1 = np.r_[0.0, np.cumsum(y)]
    s2 = np.r_[0.0, np.cumsum(y * y)]

    def cost(i, j):  # i có thể là mảng
        m = j - i
        return s2[j] - s2[i] - (s1[j] - s1[i]) ** 2 / m

    kmax = min(max_k, n // min_len)
    inf = np.inf
    dp = np.full((kmax + 1, n + 1), inf)
    arg = np.zeros((kmax + 1, n + 1), dtype=int)
    for j in range(min_len, n + 1):
        dp[1, j] = cost(0, j)
    for k in range(2, kmax + 1):
        for j in range(k * min_len, n + 1):
            i = np.arange((k - 1) * min_len, j - min_len + 1)
            c = dp[k - 1, i] + cost(i, j)
            b = np.argmin(c)
            dp[k, j], arg[k, j] = c[b], i[b]
    best_k, best_crit = 1, inf
    for k in range(1, kmax + 1):
        rss = max(dp[k, n], 1e-9)
        crit = n * np.log(rss / n) + 2 * k * np.log(n)
        if crit < best_crit:
            best_k, best_crit = k, crit
    bounds, j = [n], n
    for k in range(best_k, 1, -1):
        j = arg[k, j]
        bounds.append(j)
    bounds = [0] + bounds[::-1]
    lab = np.empty(n, dtype=int)
    for p in range(best_k):
        lab[bounds[p]:bounds[p + 1]] = p
    return lab


def since_water_all(d):
    """Thời gian (h) và quãng đường (km) kể từ lúc rời nước, cho mọi điểm không ở nguồn nước.

    Dùng để dự đoán cả trên những chuyến không đưa vào tập học (quá ngắn, quá dài, mất tín hiệu).
    Cách tính giống trong chuyến: mốc là điểm đầu tiên ra khỏi vùng 200 m. NaN nếu chưa ghé nước lần nào.
    """
    n = len(d)
    hrs, km = np.full(n, np.nan), np.full(n, np.nan)
    at = d.dw.values <= C.WATER_BUFFER_M
    t = (d.time_utc.values - d.time_utc.values[0]) / np.timedelta64(1, "h")
    step = np.nan_to_num(d.step_m.values)
    ids = d.id.values
    seen, prev_at, t_dep, cum = False, False, np.nan, 0.0
    for i in range(n):
        if i == 0 or ids[i] != ids[i - 1]:
            seen, prev_at = False, False
        if at[i]:
            seen, prev_at = True, True
            continue
        if not seen:
            continue
        if prev_at:
            t_dep, cum = t[i], 0.0
        else:
            cum += step[i]
        prev_at = False
        hrs[i], km[i] = t[i] - t_dep, cum / 1000
    return hrs, km


def circ_mean_sd_hours(h):
    a = np.asarray(h) * 2 * np.pi / 24
    c, s = np.cos(a).mean(), np.sin(a).mean()
    r = np.hypot(c, s)
    mean = (np.arctan2(s, c) * 24 / (2 * np.pi)) % 24
    sd = np.sqrt(-2 * np.log(r)) * 24 / (2 * np.pi)
    return round(float(mean), 1), round(float(sd), 1)


def mean_ci(v):
    v = v[~np.isnan(v)]
    if len(v) < 2:
        return [None, None, None]
    m, se = v.mean(), v.std(ddof=1) / np.sqrt(len(v))
    return [round(float(m), 3), round(float(m - 1.96 * se), 3), round(float(m + 1.96 * se), 3)]


def main():
    d = pd.read_parquet(C.OUT / "points.parquet")
    segs, dropped = find_segments(d)

    n = len(d)
    seg_id = np.full(n, -1)
    prop = np.full(n, np.nan)
    hrs = np.full(n, np.nan)
    path_km = np.full(n, np.nan)
    rate = np.full(n, np.nan)
    phase = np.full(n, -1)
    t_h = (d.time_utc.values - d.time_utc.values[0]) / np.timedelta64(1, "h")
    dw = d.dw.values
    step = np.nan_to_num(d.step_m.values)

    rows, phase_rows = [], []
    for k, (a, b) in enumerate(segs):
        sl = slice(a, b + 1)
        seg_id[sl] = k
        tt = t_h[sl] - t_h[a]
        dur = tt[-1]
        prop[sl] = tt / dur
        hrs[sl] = tt
        pk = np.r_[0.0, np.cumsum(step[a + 1:b + 1])] / 1000
        path_km[sl] = pk
        # Δdw so với điểm trước; điểm đầu so với điểm cuối cùng còn ở nguồn nước
        dts = (t_h[a:b + 1] - t_h[a - 1:b]).astype(float)
        y = (dw[a:b + 1] - dw[a - 1:b]) / dts
        rate[sl] = y
        lab = segment_series(y, C.MIN_PHASE_POINTS, C.MAX_PHASES)
        for p in np.unique(lab):
            idx = np.flatnonzero(lab == p)
            net = dw[a + idx[-1]] - dw[a + idx[0] - 1]   # so với điểm ngay trước pha
            phase_rows.append((k, p, float(y[idx].mean()), int(len(idx)), float(net)))
        phase[sl] = lab
        r0 = d.iloc[a]
        rows.append({
            "seg_id": k, "id": r0.id, "wet": int(r0.wet), "start_idx": a, "end_idx": b,
            "n_points": b - a + 1, "duration_h": dur, "path_km": pk[-1],
            "displacement_km": float(np.hypot(d.x.values[b] - d.x.values[a], d.y.values[b] - d.y.values[a]) / 1000),
            "start_hour": float(d.hour.values[a]), "end_hour": float(d.hour.values[b]),
            "max_dw_km": float(dw[sl].max() / 1000), "n_phases": int(lab.max() + 1),
        })
    segdf = pd.DataFrame(rows)
    ph = pd.DataFrame(phase_rows, columns=["seg_id", "phase", "mean_rate", "n", "net_m"])
    ph["state"] = np.where(ph.net_m >= C.PHASE_NET_M, 0, np.where(ph.net_m <= -C.PHASE_NET_M, 2, 1))
    state_map = {(s, p): st for s, p, st in zip(ph.seg_id, ph.phase, ph.state)}

    state = np.where(dw <= C.WATER_BUFFER_M, C.AT_WATER, C.OUTSIDE)
    in_seg = seg_id >= 0
    state[in_seg] = [state_map[(s, p)] for s, p in zip(seg_id[in_seg], phase[in_seg])]

    # Ngoài các chuyến dùng để học: vẫn tính đặc trưng chuyến đi để cây dự đoán được
    hrs_all, km_all = since_water_all(d)
    fill = (seg_id < 0) & (dw > C.WATER_BUFFER_M)
    hrs[fill], path_km[fill] = hrs_all[fill], km_all[fill]
    chk = in_seg & (dw > C.WATER_BUFFER_M)
    assert np.allclose(hrs[chk], hrs_all[chk]) and np.allclose(path_km[chk], km_all[chk]), "lệch cách tính"

    d["seg_id"], d["prop"], d["hours_since_water"] = seg_id, prop, hrs
    d["path_km_since_water"], d["ddw_rate"], d["state"] = path_km, rate, state
    d.to_parquet(C.OUT / "points_states.parquet", index=False)
    segdf.to_csv(C.OUT / "segments.csv", index=False)

    # "Bắt đầu tìm nước": đổi từ giữ khoảng cách (1) sang tiến về nước (2) trong cùng chuyến
    s = pd.Series(state)
    prev = s.shift(1)
    same = pd.Series(seg_id).eq(pd.Series(seg_id).shift(1)) & in_seg
    change = same & prev.eq(1) & s.eq(2)
    ch = d[change.values]

    seg_pts = d[in_seg]
    fig6 = {}
    for wet, name in [(0, "dry"), (1, "wet")]:
        sp = seg_pts[seg_pts.wet == wet]
        b = (sp.prop * 10).round() / 10
        fig6[name] = {
            "prop": [round(x, 1) for x in np.arange(0, 1.01, 0.1)],
            "dw_km": [mean_ci(sp.dw.values[np.isclose(b, x)] / 1000) for x in np.arange(0, 1.01, 0.1)],
            "speed": [mean_ci(sp.speed_kmh.values[np.isclose(b, x)]) for x in np.arange(0, 1.01, 0.1)],
            "temp": [mean_ci(sp.temp.values[np.isclose(b, x)]) for x in np.arange(0, 1.01, 0.1)],
        }

    val = {
        "segments_kept": int(len(segdf)), "segment_points": int(in_seg.sum()),
        "segments_dropped": dropped,
        "pct_points_in_segments": round(100 * in_seg.mean(), 1),
        "phase_median_rate_m_per_h": {C.STATE_NAMES[k]: round(float(ph.mean_rate[ph.state == k].median()), 1) for k in range(3)},
        "state_share_pct": {C.STATE_NAMES[k]: round(100 * float((state[in_seg] == k).mean()), 1) for k in range(3)},
        "phases_per_segment": segdf.n_phases.value_counts().sort_index().to_dict(),
        "pct_displacement_ge_500m": round(100 * (segdf.displacement_km >= 0.5).mean(), 1),
        "seek_water_changes": {"total": int(len(ch)), "dry": int((ch.wet == 0).sum()), "wet": int((ch.wet == 1).sum()),
                               "temp_dry": mean_ci(ch[ch.wet == 0].temp.values),
                               "temp_wet": mean_ci(ch[ch.wet == 1].temp.values)},
        "fig6": fig6,
    }
    for wet, name in [(0, "dry"), (1, "wet")]:
        sg = segdf[segdf.wet == wet]
        val[f"segments_{name}"] = {
            "n": int(len(sg)),
            "path_km_mean_sd": [round(sg.path_km.mean(), 1), round(sg.path_km.std(), 1)],
            "duration_h_mean_sd": [round(sg.duration_h.mean(), 1), round(sg.duration_h.std(), 1)],
            "displacement_km_mean_sd": [round(sg.displacement_km.mean(), 1), round(sg.displacement_km.std(), 1)],
            "max_dw_km_mean_sd": [round(sg.max_dw_km.mean(), 1), round(sg.max_dw_km.std(), 1)],
            "leave_water_hour_circ": circ_mean_sd_hours(sg.start_hour),
            "return_water_hour_circ": circ_mean_sd_hours(sg.end_hour),
        }
    (C.OUT / "segments_validation.json").write_text(json.dumps(val, indent=2, ensure_ascii=False), "utf-8")
    show = {k: v for k, v in val.items() if k != "fig6"}
    print(json.dumps(show, indent=2, ensure_ascii=False))
    print("Paper: 2.835 chuyến / 137.106 điểm; khô 12±8,5 km trong 31±20 h, mưa 10±7 km trong 27±7 h;"
          " rời nước ~14:00 về ~11:00 (khô); 2.111 lần bắt đầu tìm nước (26°C khô, 25°C mưa)")


if __name__ == "__main__":
    main()
