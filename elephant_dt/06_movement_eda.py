"""Bước 6 (EDA trạng thái chuyển động): phân tích cửa sổ 90 phút trước khi đặt nhãn.

1. Tạo cửa sổ 90 phút (movement.build_windows): đường đi, dịch chuyển, độ thẳng, đổi hướng.
2. Chọn ngưỡng nhãn CHỈ từ dữ liệu học (fit: 08/2007–06/2008):
   - Di chuyển ít: đường đi < L, với L là nơi độ thẳng trung vị đi được nửa đường từ mức nhiễu GPS
     (đường đi < 50 m) lên mức ổn định (đường đi 400–1200 m).
   - Đi ngoằn ngoèo / Đi thẳng: cắt độ thẳng tại phân vị Q của các cửa sổ có di chuyển (mặc định Q = 25%).
3. Đối chiếu theo giờ, nhiệt độ, mùa, woody cover, nguồn nước, từng cá thể; kiểm tra điểm GPS thiếu.
4. Độ nhạy: tỉ lệ nhãn khi đổi L ±25% và Q = 20% / 33%.
Kết quả: outputs/movement_windows.parquet, outputs/movement_thresholds.json, outputs/movement_eda.md, hình.
"""
import json
import os

import numpy as np
import pandas as pd

import config as C
from movement import build_windows, split_masks

C.utf8_stdout()
os.environ.setdefault("MPLCONFIGDIR", str(C.OUT / "matplotlib_cache"))
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

FIG = C.OUT / "figures"
STATES = ["Di chuyển ít", "Đi ngoằn ngoèo", "Đi thẳng"]
LOW, LOCAL, DIRECTED = 0, 1, 2
STATE_COLORS = ["#1baf7a", "#eb6834", "#2a78d6"]     # 3 slot đầu bảng màu phân loại (đã kiểm định mọi cặp)
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e1e0d9"
DEFAULT_Q = 0.25


def quality_mask(w):
    """Cửa sổ tương lai đủ tin cậy để tạo nhãn: ≥ 3 fix, không trống > 60 phút, không bước GPS lỗi."""
    return ((~w.next_flagged) & (w.next_max_gap_min <= 60) & (w.next_n_fix >= 3)).to_numpy()


def choose_thresholds(w, fit, q=DEFAULT_Q):
    f = w[fit]
    s_low = float(f.next_straightness[f.next_path_m < 50].median())
    s_hi = float(f.next_straightness[f.next_path_m.between(400, 1200)].median())
    target = (s_low + s_hi) / 2
    grid = np.arange(40, 200, 5)
    med = np.array([f.next_straightness[f.next_path_m.between(g - 10, g + 10)].median() for g in grid])
    path_low = float(np.interp(target, med, grid))               # med tăng dần theo đường đi
    moving = f.next_straightness[f.next_path_m >= path_low]
    return {"path_low_m": round(path_low, 1), "straight_cut": round(float(moving.quantile(q)), 3),
            "straight_quantile": q, "noise_straightness": round(s_low, 3), "plateau_straightness": round(s_hi, 3)}


def label(w, path_low, straight_cut, which="next"):
    """which="next": nhãn của 90 phút tới; "prev": trạng thái của 90 phút vừa qua (feature lịch sử)."""
    path, straight = w[f"{which}_path_m"], w[f"{which}_straightness"]
    return np.select([path < path_low, straight < straight_cut], [LOW, LOCAL], DIRECTED)


def share_table(group, y):
    t = pd.crosstab(group, y, normalize="index").reindex(columns=[0, 1, 2], fill_value=0)
    t["n"] = pd.Series(group).value_counts()
    return t


def style(ax, title):
    ax.set_title(title, fontsize=10, loc="left", color=INK)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#c3c2b7")
    ax.tick_params(colors=INK2, labelsize=8)


def stacked(ax, cats, shares, labels):
    bottom = np.zeros(len(cats))
    for k in range(3):
        ax.bar(range(len(cats)), shares[:, k], bottom=bottom, color=STATE_COLORS[k], width=0.8,
               edgecolor="white", linewidth=1, label=STATES[k])
        bottom += shares[:, k]
    ax.set_xticks(range(len(cats)), labels, fontsize=7)
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1))


def main():
    d = pd.read_parquet(C.OUT / "points_states.parquet")
    w = build_windows(d)
    fit, val, test = split_masks(w)
    good = quality_mask(w)
    th = choose_thresholds(w, fit & good)
    w["state"] = label(w, th["path_low_m"], th["straight_cut"])
    w["prev_state"] = label(w, th["path_low_m"], th["straight_cut"], which="prev")
    w["good"] = good
    w["period"] = np.select([fit, val, test], ["fit", "val", "2009"], "gap")
    w.to_parquet(C.OUT / "movement_windows.parquet", index=False)
    g = w[good & (fit | val)]                 # EDA trên 2007–2008; 2009 để dành đối chiếu

    # ---- độ nhạy ngưỡng ----
    sens = []
    for f_l in [0.75, 1.0, 1.25]:
        for q in [0.20, 0.25, 0.33]:
            L = th["path_low_m"] * f_l
            cut = float(w[fit & good & (w.next_path_m >= L)].next_straightness.quantile(q))
            y = label(g, L, cut)
            base = g.state.to_numpy()
            sens.append({"path_low_m": round(L, 1), "quantile": q, "straight_cut": round(cut, 3),
                         "share": [round(float((y == k).mean()), 4) for k in range(3)],
                         "agree_with_default": round(float((y == base).mean()), 4)})

    # ---- đối chiếu ----
    hour_slot = (np.round(g.hour * 60 / 90).astype(int) % 16)
    by_hour = share_table(hour_slot, g.state)
    path_hour = g.groupby(hour_slot).next_path_m.median()
    tbins = pd.cut(g.temp, [-np.inf, 20, 25, 30, 35, np.inf], labels=["<20", "20–25", "25–30", "30–35", "≥35"])
    by_temp = share_table(tbins, g.state)
    day = g[g.hour.between(9, 15)]
    by_temp_day = share_table(pd.cut(day.temp, [-np.inf, 25, 30, 35, 40, np.inf], labels=["<25", "25–30", "30–35", "35–40", "≥40"]), day.state)
    known = g[g.woody_missing == 0]
    wbins = pd.cut(known.woody, [0, 15, 30, 45, 60, 101], labels=["0–15", "15–30", "30–45", "45–60", ">60"], include_lowest=True)
    by_woody = share_table(wbins, known.state)
    by_woody_night = share_table(pd.cut(known.woody[known.hour < 4.5], [0, 15, 30, 45, 60, 101],
                                        labels=["0–15", "15–30", "30–45", "45–60", ">60"], include_lowest=True), known.state[known.hour < 4.5])
    by_season = share_table(np.where(g.wet == 1, "Mùa mưa", "Mùa khô"), g.state)
    by_id = share_table(g.id, g.state)
    path_id = g.groupby("id").next_path_m.median()
    water = pd.crosstab(g.state, np.select([g.next_disp_m < 100, g.ddw_next_m <= -100, g.ddw_next_m >= 100],
                                           ["Dịch chuyển < 100 m", "Về gần nước", "Ra xa nước"], "Khoảng cách ít đổi"),
                        normalize="index")
    dw_state = g.groupby("state").dw_km.median()
    persist = float((g.state == g.prev_state).mean())

    # ---- chất lượng dữ liệu ----
    allw = w[fit | val]
    q_info = {
        "windows_total": int(len(w)), "fit": int(fit.sum()), "val": int(val.sum()), "test_2009": int(test.sum()),
        "excluded_quality_pct": round(100 * float(1 - quality_mask(allw).mean()), 2),
        "n_fix_counts": {int(k): int(v) for k, v in allw.next_n_fix.value_counts().sort_index().items()},
        "median_path_maxgap30": float(allw.next_path_m[allw.next_max_gap_min <= 31].median()),
        "median_path_maxgap60": float(allw.next_path_m[allw.next_max_gap_min.between(55, 61)].median()),
        "fix_age_counts": {int(k): int(v) for k, v in allw.fix_age_min.round().value_counts().sort_index().head(6).items()},
        "woody_missing_pct": round(100 * float(g.woody_missing.mean()), 2),
    }
    summary = {"thresholds": th, "sensitivity": sens, "quality": q_info,
               "state_share_2007_08": [round(float((g.state == k).mean()), 4) for k in range(3)],
               "persistence_same_state": round(persist, 4), "states": STATES}
    (C.OUT / "movement_thresholds.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), "utf-8")

    # ---- hình ----
    FIG.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.4))
    f = w[fit & good]
    bins = np.logspace(0.5, 3.9, 50)
    ax[0].hist(f.next_path_m, bins=bins, color="#86b6ef", edgecolor="white", linewidth=0.5)
    ax[0].set_xscale("log"); ax[0].axvline(th["path_low_m"], color=INK, lw=1.2, ls="--")
    ax[0].text(th["path_low_m"] * 1.08, ax[0].get_ylim()[1] * 0.9, f"{th['path_low_m']:.0f} m", fontsize=8, color=INK)
    style(ax[0], "Đường đi trong 90 phút (dữ liệu học, log)"); ax[0].set_xlabel("m", fontsize=8, color=INK2)
    gx = np.arange(20, 1500, 10)
    mm = [f.next_straightness[f.next_path_m.between(v * 0.85, v * 1.15)].median() for v in gx]
    ax[1].plot(gx, mm, color="#2a78d6", lw=2); ax[1].set_xscale("log")
    ax[1].axhline(th["noise_straightness"], color=INK2, lw=1, ls=":"); ax[1].axhline(th["plateau_straightness"], color=INK2, lw=1, ls=":")
    ax[1].axvline(th["path_low_m"], color=INK, lw=1.2, ls="--")
    style(ax[1], "Độ thẳng trung vị theo đường đi"); ax[1].set_xlabel("đường đi (m, log)", fontsize=8, color=INK2)
    fig.tight_layout(); fig.savefig(FIG / "movement_thresholds.png", dpi=150); plt.close(fig)

    fig, ax = plt.subplots(2, 2, figsize=(10, 6.2))
    stacked(ax[0, 0], by_hour.index, by_hour[[0, 1, 2]].to_numpy(), [f"{int(s*1.5):02d}:{'30' if s % 2 else '00'}" if s % 2 == 0 else "" for s in by_hour.index])
    style(ax[0, 0], "Trạng thái theo giờ (2007–2008)")
    stacked(ax[0, 1], by_temp_day.index, by_temp_day[[0, 1, 2]].to_numpy(), list(by_temp_day.index.astype(str)))
    style(ax[0, 1], "Theo nhiệt độ vòng cổ, chỉ 09:00–15:00 (°C)")
    stacked(ax[1, 0], by_woody.index, by_woody[[0, 1, 2]].to_numpy(), list(by_woody.index.astype(str)))
    style(ax[1, 0], "Theo độ che phủ cây gỗ tại GPS (%)")
    stacked(ax[1, 1], by_id.index, by_id[[0, 1, 2]].to_numpy(), list(by_id.index))
    ax[1, 1].tick_params(axis="x", rotation=60)
    style(ax[1, 1], "Theo cá thể")
    handles = [matplotlib.patches.Patch(color=STATE_COLORS[k], label=STATES[k]) for k in range(3)]
    fig.legend(handles=handles, loc="upper center", ncol=3, frameon=False, fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.95)); fig.savefig(FIG / "movement_states_eda.png", dpi=150); plt.close(fig)

    # ---- báo cáo ----
    pct = lambda v: f"{100 * v:.1f}%"
    def table(t, first):
        rows = [f"| {first} | " + " | ".join(STATES) + " | Số cửa sổ |", "|---|" + "---:|" * 4]
        for k, r in t.iterrows():
            rows.append(f"| {k} | " + " | ".join(pct(r[c]) for c in [0, 1, 2]) + f" | {int(r['n']):,} |")
        return "\n".join(rows)
    sh = summary["state_share_2007_08"]
    md = f"""# EDA trạng thái chuyển động (cửa sổ 90 phút)

Dữ liệu: {q_info['windows_total']:,} cửa sổ 90 phút của 14 voi. Chia theo thời gian: **fit** 08/2007–06/2008
({q_info['fit']:,}), **validation** 07–12/2008 ({q_info['val']:,}), **2009** ({q_info['test_2009']:,}, chỉ để đối chiếu,
không dùng cho EDA hay chọn ngưỡng). Số liệu dưới đây là 2007–2008, chỉ cửa sổ đủ chất lượng.

## 1. Đại lượng đo được

| Đại lượng | Cách tính |
|---|---|
| Đường đi | Tổng độ dài các bước GPS trong 90 phút tới, quy về 90 phút |
| Dịch chuyển | Khoảng cách thẳng từ điểm đầu tới điểm cuối cửa sổ |
| Độ thẳng | Dịch chuyển ÷ đường đi (1 = đi thẳng, gần 0 = quay về chỗ cũ) |
| Đổi hướng | Trung bình góc rẽ giữa các bước dài ≥ 20 m |

Trung vị đường đi {g.next_path_m.median():.0f} m / 90 phút; độ thẳng trung vị {g.next_straightness.median():.2f}.
Phân bố đường đi (log) **chỉ có một đỉnh**: không có ranh giới tự nhiên giữa "nghỉ" và "đi".

## 2. Ngưỡng nhãn (học từ fit)

![Ngưỡng](figures/movement_thresholds.png)

- **Di chuyển ít: đường đi < {th['path_low_m']:.0f} m.** Ở đường đi < 50 m, độ thẳng trung vị chỉ {th['noise_straightness']:.2f}
  (gần nhiễu GPS: mô phỏng voi đứng yên với sai số 10 m cho đường đi ~50 m, độ thẳng ~0,33). Từ ~200 m trở lên độ thẳng ổn
  định quanh {th['plateau_straightness']:.2f}. Ngưỡng là nơi độ thẳng đi được nửa đường giữa hai mức.
- **Đi ngoằn ngoèo: có di chuyển và độ thẳng < {th['straight_cut']:.2f}** (25% cửa sổ có di chuyển kém thẳng nhất). Độ thẳng
  của các cửa sổ có di chuyển lệch mạnh về 1 và không tách hai nhóm (GMM chỉ tách "rất thẳng" và "khá thẳng"), nên dùng
  phân vị và kiểm tra độ nhạy.
- **Đi thẳng: còn lại.**

Tỉ lệ 2007–2008: {STATES[0]} {pct(sh[0])}, {STATES[1]} {pct(sh[1])}, {STATES[2]} {pct(sh[2])}.
Cửa sổ có cùng trạng thái với 90 phút trước: {pct(persist)}.

**Độ nhạy** (đổi ngưỡng, so với nhãn mặc định):

| Ngưỡng đường đi | Phân vị độ thẳng | Ngưỡng độ thẳng | {' | '.join(STATES)} | Trùng nhãn mặc định |
|---:|---:|---:|---:|---:|---:|---:|
""" + "\n".join(f"| {s['path_low_m']:.0f} m | {int(s['quantile']*100)}% | {s['straight_cut']:.2f} | "
                 + " | ".join(pct(v) for v in s["share"]) + f" | {pct(s['agree_with_default'])} |" for s in sens) + f"""

## 3. Đối chiếu

![Trạng thái theo bối cảnh](figures/movement_states_eda.png)

### Giờ trong ngày
{table(by_hour.set_axis([f"{int(s*1.5):02d}:{'30' if (s*1.5) % 1 else '00'}" for s in by_hour.index]), "Giờ")}

### Nhiệt độ vòng cổ (mọi giờ)
{table(by_temp, "°C")}

Nhiệt độ và giờ đi cùng nhau. **Chỉ xét 09:00–15:00** để giảm ảnh hưởng của giờ:
{table(by_temp_day, "°C")}

### Độ che phủ cây gỗ (chỉ GPS có giá trị thật; thiếu {q_info['woody_missing_pct']:.1f}%)
{table(by_woody, "%")}

Chỉ ban đêm (00:00–04:30):
{table(by_woody_night, "%")}

### Mùa (lịch quy ước)
{table(by_season, "Mùa")}

### Cá thể
{table(by_id, "Voi")}

Trung vị đường đi theo cá thể: {', '.join(f"{k} {v:.0f} m" for k, v in path_id.items())}.

### Quan hệ với nguồn nước trong từng trạng thái
| Trạng thái | """ + " | ".join(water.columns) + " | Khoảng cách tới nước (trung vị) |\n|---|" + "---:|" * (len(water.columns) + 1) + "\n" + "\n".join(
        f"| {STATES[k]} | " + " | ".join(pct(v) for v in water.loc[k]) + f" | {dw_state[k]*1000:.0f} m |" for k in water.index) + f"""

## 4. Chất lượng dữ liệu

- Cửa sổ bị loại vì < 3 fix, khoảng trống > 60 phút hoặc bước GPS lỗi: {q_info['excluded_quality_pct']:.1f}%.
- Số fix trong cửa sổ tương lai: {q_info['n_fix_counts']}.
- Điểm GPS thiếu làm đường đi ngắn đi: trung vị {q_info['median_path_maxgap30']:.0f} m khi đủ fix 30 phút,
  {q_info['median_path_maxgap60']:.0f} m khi có khoảng trống 60 phút. Vì vậy tuổi điểm GPS và khoảng trống được đưa vào làm
  feature kiểm soát chất lượng.
- Tuổi điểm GPS tại mốc (phút): {q_info['fix_age_counts']}.

## Giới hạn
Nhãn là trạng thái hình học của quỹ đạo GPS (đi ít / đi ngoằn ngoèo / đi thẳng), **không** phải ăn, ngủ hay uống.
Cửa sổ 90 phút chỉ có ~4 fix nên độ thẳng thô; ngưỡng là quy ước có cơ sở dữ liệu, không phải ngưỡng sinh học.
"""
    (C.OUT / "movement_eda.md").write_text(md, "utf-8")
    print(json.dumps({"thresholds": th, "share": sh, "persistence": round(persist, 3), "quality": q_info}, ensure_ascii=False, indent=1))
    print("Báo cáo:", C.OUT / "movement_eda.md")


if __name__ == "__main__":
    main()
