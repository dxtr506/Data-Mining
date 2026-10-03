"""Cửa sổ 90 phút cho bài toán trạng thái chuyển động.

Mỗi con voi được đặt lên lưới 90 phút theo giờ địa phương (00:00, 01:30, ...). Tại mốc g:
- Điểm neo k0 = fix GPS cuối cùng tại hoặc trước g, cũ không quá 30 phút. Mọi feature lấy từ fix ≤ k0.
- Cửa sổ tương lai (chỉ dùng để tạo nhãn): các fix từ k0 tới k1, với k1 = fix cuối cùng trước g + 105 phút
  và không sớm hơn g + 75 phút.
- Cửa sổ trước (feature lịch sử): các fix từ kp tới k0, với kp = fix neo của mốc g − 90 phút.

Đại lượng của một cửa sổ:
- path_m        : tổng độ dài các bước GPS trong cửa sổ, quy về 90 phút (path × 90 / thời lượng).
- disp_m        : độ dịch chuyển thẳng từ fix đầu tới fix cuối (không quy đổi).
- straightness  : disp / path (0 = quay về chỗ cũ, 1 = đi thẳng); NaN khi path < 1 m.
- turn_deg      : trung bình |đổi hướng| giữa các bước liên tiếp dài ≥ 20 m (bỏ bước ngắn vì nhiễu GPS).
- max_gap_min   : khoảng cách lớn nhất giữa hai fix liên tiếp trong cửa sổ.
- n_fix         : số fix trong cửa sổ.
"""
import numpy as np
import pandas as pd

import config as C

STEP_MIN = 90
MAX_FIX_AGE_MIN = 30
END_LO, END_HI = 75, 105          # fix kết thúc cửa sổ tương lai phải nằm trong [g+75, g+105]
MIN_TURN_STEP_M = 20
FLAG_SPEED_MPH = 10_000           # 10 km/h: bước GPS bị gắn cờ lỗi


def _window(t, x, y, cd, flag_cum, a, b, nominal=STEP_MIN):
    """Đại lượng của các cửa sổ fix a..b (mảng chỉ số, a ≤ b)."""
    dur = t[b] - t[a]
    path = cd[b] - cd[a]
    disp = np.hypot(x[b] - x[a], y[b] - y[a])
    with np.errstate(invalid="ignore", divide="ignore"):
        path90 = np.where(dur > 0, path * nominal / dur, np.nan)
        straight = np.where(path >= 1, np.minimum(disp / path, 1.0), np.nan)
    n = b - a + 1
    gaps = np.full(len(a), np.nan)
    turns = np.full(len(a), np.nan)
    for i in range(len(a)):                       # cửa sổ ngắn (≤ ~8 fix) nên vòng lặp nhỏ
        if b[i] <= a[i]:
            continue
        sl = slice(a[i], b[i] + 1)
        tt, xx, yy = t[sl], x[sl], y[sl]
        gaps[i] = np.diff(tt).max()
        dx, dy = np.diff(xx), np.diff(yy)
        keep = np.hypot(dx, dy) >= MIN_TURN_STEP_M
        h = np.arctan2(dx[keep], dy[keep])
        if len(h) >= 2:
            dh = np.abs((np.diff(h) + np.pi) % (2 * np.pi) - np.pi)
            turns[i] = np.degrees(dh).mean()
    flagged = flag_cum[b] != flag_cum[a]
    return dict(dur_min=dur, path_m=path90, path_raw_m=path, disp_m=disp, straightness=straight,
                turn_deg=turns, max_gap_min=gaps, n_fix=n, flagged=flagged)


def build_windows(d):
    """Một hàng / mốc 90 phút có cả cửa sổ trước và cửa sổ tương lai. d: points_states (đã sort id, time)."""
    t_all = d.time_utc.values.astype("datetime64[s]").astype(np.int64) / 60
    off = C.LOCAL_UTC_OFFSET_H * 60
    out = []
    for eid, idx in d.groupby("id", sort=False).indices.items():
        t, x, y = t_all[idx], d.x.values[idx], d.y.values[idx]
        step = np.r_[0.0, np.hypot(np.diff(x), np.diff(y))]
        cd = np.cumsum(step)
        spd = np.r_[0.0, step[1:] / np.maximum(np.diff(t) / 60, 1e-9)]
        flag_cum = np.cumsum(spd > FLAG_SPEED_MPH)
        grid = np.arange(np.ceil((t[0] + off) / STEP_MIN) * STEP_MIN - off, t[-1] + 1, STEP_MIN)

        def anchor(g):
            k = np.clip(np.searchsorted(t, g, side="right") - 1, 0, len(t) - 1)
            ok = (t[k] <= g) & (g - t[k] <= MAX_FIX_AGE_MIN)
            return k, ok

        k0, ok0 = anchor(grid)
        kp, okp = anchor(grid - STEP_MIN)
        kq, okq = anchor(grid - 2 * STEP_MIN)
        k1 = np.clip(np.searchsorted(t, grid + END_HI, side="right") - 1, 0, len(t) - 1)
        ok1 = (t[k1] >= grid + END_LO) & (k1 > k0)
        r = np.flatnonzero(ok0 & okp & ok1 & (k0 > kp))
        if not len(r):
            continue
        a0, a1, ap = k0[r], k1[r], kp[r]
        fut = _window(t, x, y, cd, flag_cum, a0, a1)
        prev = _window(t, x, y, cd, flag_cum, ap, a0)
        gi = idx[a0]
        # tốc độ bước cuối cùng trước mốc (km/h), chỉ khi bước đó ≤ 60 phút
        last_dt = t[a0] - t[np.maximum(a0 - 1, 0)]
        last_speed = np.where((a0 > 0) & (last_dt > 0) & (last_dt <= 60), step[a0] / 1000 / (last_dt / 60), np.nan)
        temp = d.temp.values[idx]
        temp_prev90 = np.where(okp[r], temp[ap], np.nan)
        temp_prev180 = np.where(okq[r], temp[kq[r]], np.nan)
        dw = d.dw.values[idx]
        frame = pd.DataFrame({
            "id": eid, "t_utc_min": grid[r], "fix": gi, "fix_end": idx[a1],
            "fix_age_min": grid[r] - t[a0],
            "hour": ((grid[r] + off) % 1440) / 60, "temp": temp[a0], "wet": d.wet.values[gi],
            "dw_km": dw[a0] / 1000,
            "hours_since_water": d.hours_since_water.values[gi],
            "woody": d.woody.values[gi], "woody_mean_300m": d.woody_mean_300m.values[gi],
            "woody_missing": d.woody_missing.values[gi].astype(int),
            "temp_change_90": temp[a0] - temp_prev90, "temp_change_180": temp[a0] - temp_prev180,
            "last_speed_kmh": last_speed,
            "x": x[a0], "y": y[a0], "lon": d.lon.values[gi], "lat": d.lat.values[gi],
            "ddw_next_m": dw[a1] - dw[a0],
        })
        for k, v in fut.items():
            frame[f"next_{k}"] = v
        for k, v in prev.items():
            frame[f"prev_{k}"] = v
        out.append(frame)
    w = pd.concat(out, ignore_index=True)
    w["prev_speed_kmh"] = w.prev_path_m / 1000 / (STEP_MIN / 60)      # tốc độ trung bình cửa sổ trước
    assert (w.t_utc_min - w.fix_age_min <= w.t_utc_min).all()
    return w


def split_masks(w, val_start="2008-07-01", test_start=None):
    """Chia theo thời gian (giờ địa phương): fit < val_start ≤ validation < test_start ≤ 2009 (đối chiếu).
    Hàng có cửa sổ tương lai chạm sang tập sau bị bỏ khỏi tập trước."""
    test_start = test_start or C.SPLIT_DATE
    off = C.LOCAL_UTC_OFFSET_H * 60
    to_min = lambda s: pd.Timestamp(s).value // 60_000_000_000 - off
    v0, t0 = to_min(val_start), to_min(test_start)
    end = w.t_utc_min + END_HI
    fit = end < v0
    val = (w.t_utc_min >= v0) & (end < t0)
    test = w.t_utc_min >= t0
    return fit.to_numpy(), val.to_numpy(), test.to_numpy()


WATER_HORIZON_MIN = 180
MAX_FUTURE_GAP_MIN = 60


def add_water_return(w, d):
    """Nhãn "quay lại vùng nước trong 3 giờ tới" cho các cửa sổ đang ở xa nước (> 200 m).

    1 = có ít nhất một điểm GPS trong vùng 200 m quanh nguồn nước trong (g, g + 3 h], không có khoảng trống GPS
        > 60 phút trước khi tới đó. 0 = không có điểm nào trong vùng nước và GPS phủ tới ít nhất g + 2h15 không
        trống > 60 phút. NaN = không đủ GPS để biết. Chỉ dùng tương lai để tạo nhãn.
    """
    t_all = d.time_utc.values.astype("datetime64[s]").astype(np.int64) / 60
    lab = np.full(len(w), np.nan)
    tta = np.full(len(w), np.nan)
    for eid, idx in d.groupby("id", sort=False).indices.items():
        t, dw = t_all[idx], d.dw.values[idx]
        m = np.flatnonzero(w.id.values == eid)
        t0 = w.t_utc_min.values[m]
        a = np.searchsorted(t, t0, side="right")                 # fix đầu tiên sau mốc
        b = np.searchsorted(t, t0 + WATER_HORIZON_MIN, side="right")
        for i, (ai, bi) in enumerate(zip(a, b)):
            if bi - ai < 2 or ai == 0:
                continue
            hit = np.flatnonzero(dw[ai:bi] <= C.WATER_BUFFER_M)
            if len(hit):
                j = ai + hit[0]
                if np.diff(t[ai - 1:j + 1]).max() <= MAX_FUTURE_GAP_MIN:
                    lab[m[i]], tta[m[i]] = 1, t[j] - t0[i]
            elif t[bi - 1] >= t0[i] + WATER_HORIZON_MIN - 45 and np.diff(t[ai - 1:bi]).max() <= MAX_FUTURE_GAP_MIN:
                lab[m[i]] = 0
    w = w.copy()
    away = (w.dw_km.values * 1000 > C.WATER_BUFFER_M) & w.hours_since_water.notna().values
    w["water_return"] = np.where(away, lab, np.nan)
    w["minutes_to_water"] = np.where(away, tta, np.nan)
    return w
