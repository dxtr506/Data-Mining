"""Bước 7: hai Decision Tree, mỗi cây trả lời một câu hỏi.

Bốn cây, mỗi cây một câu hỏi và một nhãn tổng quát lấy từ GPS:
  "rest"  : trong 90 phút tới voi NGHỈ (đường đi < ngưỡng ở 06_movement_eda) hay DI CHUYỂN?
  "water" : voi đang ở xa nước (> 200 m) có QUAY LẠI vùng nước (≤ 200 m) trong 3 giờ tới không?
            Đây là xu hướng quay lại nước; chưa quan sát được voi có uống hay không.
  "speed" : ban ngày (06–18h), khi voi đi, đi NHANH hay CHẬM (đường đi 90 phút trên / dưới trung vị của dữ liệu học)?
  "stay"  : voi đang ở trong vùng nước (≤ 200 m) sẽ Ở LẠI (đi < 150 m) hay RỜI ĐI trong 90 phút tới?
Mỗi cây đi qua cùng một quy trình kiểm chứng; cây nào không hơn mức đoán bừa thì không được giữ.

Feature chỉ lấy từ GPS tại hoặc trước mốc dự báo. Không dùng "voi vừa làm gì" để cây khỏi chỉ học quán tính.
Chia theo thời gian: fit 08/2007–06/2008, validation 07–12/2008 (chọn độ sâu, số mẫu ở lá, cắt tỉa, ablation),
2009 chỉ để đối chiếu (đã được xem ở các phiên bản trước nên không dùng để chọn gì). Mô hình cuối học lại trên
2007–2008. Mỗi luật báo số mẫu, số cá thể, lift ở fit / validation / 2009 và số voi có lift > 1.
"""
import json

import numpy as np
import pandas as pd
from pyproj import Transformer
from sklearn.inspection import permutation_importance
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score
from sklearn.tree import DecisionTreeClassifier

import config as C
from movement import add_water_return

C.utf8_stdout()

FEATURE_LABELS = {
    "hour": "Giờ địa phương", "temp": "Nhiệt độ vòng cổ (°C)", "wet": "Mùa (lịch quy ước)",
    "dw_km": "Khoảng cách tới nguồn nước gần nhất (km)", "hours_since_water": "Thời gian ngoài vùng gần nước (giờ)",
    "woody": "Độ che phủ cây gỗ tại GPS (%)", "woody_mean_300m": "Độ che phủ cây gỗ trung bình ~300 m (%)",
    "temp_change_90": "Nhiệt độ so với 90 phút trước (°C)", "temp_change_180": "Nhiệt độ so với 3 giờ trước (°C)",
    "woody_missing": "Thiếu dữ liệu cây gỗ", "fix_age_min": "Tuổi điểm GPS tại mốc (phút)",
}
BASE = ["hour", "temp", "wet", "dw_km", "woody", "woody_mean_300m", "temp_change_90", "temp_change_180", "woody_missing", "fix_age_min"]
STAY_M = 150               # ở trong vùng nước và đi < 150 m trong 90 phút = ở lại
TASKS = {
    "rest": {"title": "Nghỉ hay di chuyển?", "classes": ["Nghỉ (ít di chuyển)", "Di chuyển"], "features": BASE},
    "water": {"title": "Có quay lại nước không?", "classes": ["Chưa về nước", "Về nước trong 3 giờ"],
              "features": BASE + ["hours_since_water"]},
    "speed": {"title": "Đi nhanh hay chậm?", "classes": ["Đi chậm", "Đi nhanh"], "features": BASE + ["hours_since_water"]},
    "stay": {"title": "Ở lại hay rời vùng nước?", "classes": ["Rời đi", "Ở lại vùng nước"], "features": BASE},
}
GRID = [dict(max_depth=d, min_samples_leaf=m, ccp_alpha=a)
        for d in [3, 4, 5, 6] for m in [250, 500, 1000] for a in [0.0, 0.0002, 0.0005, 0.001]]
TIE = 0.01              # chọn cây ít lá nhất trong 0,01 macro-F1 so với tốt nhất: bỏ các nhánh chỉ thêm nhiễu
MIN_ID_ROWS = 30
MIN_PERIOD_ROWS = 30


def scores(y, p):
    return {"acc": round(accuracy_score(y, p), 4), "bal_acc": round(balanced_accuracy_score(y, p), 4),
            "macro_f1": round(f1_score(y, p, average="macro", labels=[0, 1]), 4)}


class Imputer:
    def fit(self, df, feats):
        self.med = {f: float(df[f].median()) for f in feats if df[f].isna().any() or f.startswith("woody")}
        return self

    def transform(self, df, feats):
        X = df[feats].copy()
        for f, m in self.med.items():
            if f in X:
                X[f] = X[f].fillna(m)
        return X.to_numpy(float)


def tree(p):
    return DecisionTreeClassifier(class_weight="balanced", random_state=0, **p)


def select(fit, val, feats, tgt):
    imp = Imputer().fit(fit, feats)
    Xf, Xv = imp.transform(fit, feats), imp.transform(val, feats)
    rows = []
    for p in GRID:
        m = tree(p).fit(Xf, fit[tgt])
        rows.append({**p, "leaves": int(m.get_n_leaves()), **{f"val_{k}": v for k, v in scores(val[tgt], m.predict(Xv)).items()}})
    best = max(r["val_macro_f1"] for r in rows)
    choice = min([r for r in rows if r["val_macro_f1"] >= best - TIE], key=lambda r: (r["leaves"], -r["val_macro_f1"]))
    return {k: choice[k] for k in ["max_depth", "min_samples_leaf", "ccp_alpha"]}, rows


def lift_of(y, mask, k, base):
    n = int(mask.sum())
    return (round(float((y[mask] == k).mean() / base[k]), 2) if n >= MIN_PERIOD_ROWS else None), n


def per_id_lift(ids, y, mask, pc):
    ok = pos = 0
    for e in np.unique(ids[mask]):
        me, ae = mask & (ids == e), ids == e
        if me.sum() < MIN_ID_ROWS:
            continue
        be = (y[ae] == pc).mean()
        ok += 1
        pos += int(be > 0 and (y[me] == pc).mean() / be > 1)
    return ok, pos


def export(model, feats, tr, sets, tgt, classes):
    K = len(classes)
    t = model.tree_
    Xtr, ytr, ids = tr["X"], tr["df"][tgt].to_numpy(int), tr["df"].id.to_numpy()
    counts = np.asarray(model.decision_path(Xtr).T @ np.eye(K)[ytr])
    base = np.bincount(ytr, minlength=K) / len(ytr)
    leaf_tr = model.apply(Xtr)
    leaf_of = {n: model.apply(s["X"]) for n, s in sets.items()}
    base_of = {n: np.bincount(s["df"][tgt].astype(int), minlength=K) / len(s["df"]) for n, s in sets.items()}
    nodes = []
    for i in range(t.node_count):
        leaf = t.children_left[i] == -1
        c = counts[i]
        pc = int(np.argmax(t.value[i][0]))
        node = {"id": i, "leaf": bool(leaf), "feature": None if leaf else feats[t.feature[i]],
                "threshold": None if leaf else round(float(t.threshold[i]), 6),
                "left": None if leaf else int(t.children_left[i]), "right": None if leaf else int(t.children_right[i]),
                "n": int(c.sum()), "counts": [int(v) for v in c], "pred": pc,
                "conf": round(float(c[pc] / c.sum()), 4), "lift": round(float(c[pc] / c.sum() / base[pc]), 2)}
        if leaf:
            m = leaf_tr == i
            node["n_ids"] = int(len(np.unique(ids[m])))
            node["ids_eval"], node["ids_lift_gt1"] = per_id_lift(ids, ytr, m, pc)
            for name, s in sets.items():
                y = s["df"][tgt].to_numpy(int)
                node[f"lift_{name}"], node[f"n_{name}"] = lift_of(y, leaf_of[name] == i, pc, base_of[name])
            te = sets["2009"]["df"]
            node["ids_eval_2009"], node["ids_lift_gt1_2009"] = per_id_lift(te.id.to_numpy(), te[tgt].to_numpy(int), leaf_of["2009"] == i, pc)
        nodes.append(node)
    rules = []

    def walk(i, steps):
        n = nodes[i]
        if n["leaf"]:
            rules.append({"leaf": i, "steps": steps, "pred": n["pred"], "support": round(n["n"] / len(ytr), 4),
                          **{k: v for k, v in n.items() if k not in ("left", "right", "feature", "threshold", "leaf", "id")}})
            return
        walk(n["left"], steps + [[n["feature"], "<=", n["threshold"]]])
        walk(n["right"], steps + [[n["feature"], ">", n["threshold"]]])

    walk(0, [])
    for r in rules:
        lv, l9 = r.get("lift_val"), r.get("lift_2009")
        r["stable"] = bool(lv and l9 and lv > 1.1 and l9 > 1.1 and r["ids_eval"] and r["ids_lift_gt1"] / r["ids_eval"] >= 2 / 3)
    rules.sort(key=lambda r: -r["lift"] * np.sqrt(r["support"]))
    return nodes, rules


def fit_task(key, cfg, data):
    tgt, feats, classes = f"y_{key}", cfg["features"], cfg["classes"]
    fit, val, te = data["fit"], data["val"], data["2009"]
    train = pd.concat([fit, val])
    params, grid = select(fit, val, feats, tgt)
    imp_f = Imputer().fit(fit, feats)
    m_fit = tree(params).fit(imp_f.transform(fit, feats), fit[tgt])
    Xv = imp_f.transform(val, feats)
    pv = m_fit.predict(Xv)
    perm = permutation_importance(m_fit, Xv, val[tgt], scoring="f1_macro", n_repeats=5, random_state=0).importances_mean
    imp = Imputer().fit(train, feats)
    Xtr, X9 = imp.transform(train, feats), imp.transform(te, feats)
    model = tree(params).fit(Xtr, train[tgt])
    p9 = model.predict(X9)
    sets = {"fit": {"df": fit, "X": imp.transform(fit, feats)}, "val": {"df": val, "X": imp.transform(val, feats)}, "2009": {"df": te, "X": X9}}
    nodes, rules = export(model, feats, {"df": train, "X": Xtr}, sets, tgt, classes)
    groups = {"Giờ": ["hour"], "Nhiệt độ": ["temp", "temp_change_90", "temp_change_180"], "Mùa": ["wet"],
              "Khoảng cách tới nước": ["dw_km"], "Cây gỗ": ["woody", "woody_mean_300m", "woody_missing"],
              "Chất lượng GPS": ["fix_age_min"], "Thời gian rời nước": ["hours_since_water"]}
    abl = []
    for g, fs in groups.items():
        keep = [f for f in feats if f not in fs]
        if len(keep) == len(feats):
            continue
        ik = Imputer().fit(fit, keep)
        mk = tree(params).fit(ik.transform(fit, keep), fit[tgt])
        it = Imputer().fit(train, keep)
        mk9 = tree(params).fit(it.transform(train, keep), train[tgt])
        abl.append({"dropped": g, "val": scores(val[tgt], mk.predict(ik.transform(val, keep))),
                    "2009": scores(te[tgt], mk9.predict(it.transform(te, keep)))})
    maj = int(np.bincount(fit[tgt].astype(int)).argmax())
    base = {p: {"majority": scores(d[tgt], np.full(len(d), maj))} for p, d in [("val", val), ("2009", te)]}
    metrics = {"title": cfg["title"], "classes": classes, "params": params, "leaves": int(model.get_n_leaves()), "grid": grid,
               "n": {"fit": len(fit), "val": len(val), "2009": len(te)},
               "share": {p: [round(float((d[tgt] == k).mean()), 4) for k in range(2)] for p, d in [("fit", fit), ("val", val), ("2009", te)]},
               "val": scores(val[tgt], pv), "2009": scores(te[tgt], p9), "baselines": base,
               "confusion_2009": confusion_matrix(te[tgt], p9, labels=[0, 1]).tolist(), "ablation": abl,
               "permutation_val": {f: round(float(v), 4) for f, v in zip(feats, perm)}, "imputation_medians": imp.med,
               "rules_stable": int(sum(r["stable"] for r in rules)), "rules_total": len(rules)}
    print(f"\n=== {cfg['title']}: {params}, {model.get_n_leaves()} lá | n fit {len(fit):,} val {len(val):,} 2009 {len(te):,}")
    print("  validation", metrics["val"], "| 2009", metrics["2009"], "| lớp đông nhất val", base["val"]["majority"]["macro_f1"])
    for a in abl:
        print(f"  bỏ {a['dropped']}: val {a['val']['macro_f1']}, 2009 {a['2009']['macro_f1']}")
    for r in rules:
        c = " VÀ ".join(f"{f} {op} {round(v, 2)}" for f, op, v in r["steps"])
        print(f"  [{'ổn định' if r['stable'] else 'chưa'}] {classes[r['pred']]}: lift {r['lift_fit']}/{r['lift_val']}/{r['lift_2009']}, "
              f"{r['n']:,} mẫu, {r['ids_lift_gt1']}/{r['ids_eval']} voi | {c}")
    tree_out = {"key": key, "title": cfg["title"], "classes": classes, "feature_keys": feats, "params": params, "nodes": nodes, "rules": rules}
    return tree_out, metrics, train, imp


def main():
    w = pd.read_parquet(C.OUT / "movement_windows.parquet")
    d = pd.read_parquet(C.OUT / "points_states.parquet")
    w = add_water_return(w, d)
    w["y_rest"] = np.where(w.good, (w.state != 0).astype(float), np.nan)        # 0 = nghỉ, 1 = di chuyển
    w["y_water"] = w.water_return
    day = w.hour.ge(6) & w.hour.lt(18)
    moving = w.good & (w.state != 0) & day
    speed_thr = float(w[moving & (w.period == "fit")].next_path_m.median())          # chỉ học từ fit
    w["y_speed"] = np.where(moving, (w.next_path_m > speed_thr).astype(float), np.nan)   # 0 = chậm, 1 = nhanh
    at_water = w.good & (w.dw_km * 1000 <= C.WATER_BUFFER_M)
    w["y_stay"] = np.where(at_water, (w.next_path_m < STAY_M).astype(float), np.nan)     # 1 = ở lại
    w["wlon"] = d.water_lon.values[w.fix.values]
    w["wlat"] = d.water_lat.values[w.fix.values]
    w.to_parquet(C.OUT / "tasks_windows.parquet", index=False)
    n9 = w[w.period == "2009"].id.value_counts()
    keep9 = w.id.map(n9).fillna(0) >= 16               # bỏ voi có < 1 ngày dữ liệu 2009
    out_trees, metrics, fitted = {}, {"tasks": {}}, {}
    for key, cfg in TASKS.items():
        tgt = f"y_{key}"
        ok = w[tgt].notna() & (w.period != "gap")
        if key in ("water", "speed"):
            ok &= w.hours_since_water.notna() if key == "water" else True
        data = {}
        for p in ["fit", "val", "2009"]:
            df = w[ok & (w.period == p) & (keep9 if p == "2009" else True)].copy()
            df[tgt] = df[tgt].astype(int)
            data[p] = df
        out_trees[key], metrics["tasks"][key], tr_df, imp = fit_task(key, cfg, data)
        fitted[key] = (tr_df, imp)
    metrics["speed_threshold_m"], metrics["stay_m"] = speed_thr, STAY_M

    # Dự đoán cho mọi cửa sổ 2009 để web hiển thị (feature đủ; nhãn có thể thiếu)
    t9 = w[(w.period == "2009") & keep9 & w.good].copy()
    to_wgs = Transformer.from_crs(C.UTM, "EPSG:4326", always_xy=True)
    lon, lat = to_wgs.transform(t9.x.values, t9.y.values)
    pred = pd.DataFrame({"id": t9.id.values, "t_utc_min": t9.t_utc_min.values, "lon": lon, "lat": lat, "fix": t9.fix.values,
                         "dw_m": t9.dw_km.values * 1000, "temp": t9.temp.values, "woody": t9.woody.values,
                         "hours_since_water": t9.hours_since_water.values, "wlon": t9.wlon.values, "wlat": t9.wlat.values,
                         "apath": t9.next_path_m.values, "minutes_to_water": t9.minutes_to_water.values}, index=t9.index)
    pred["actual_rest"] = t9.y_rest.fillna(-1).astype(int)
    pred["actual_water"] = t9.y_water.fillna(-1).astype(int)
    pred["actual_speed"] = t9.y_speed.fillna(-1).astype(int)
    pred["actual_stay"] = t9.y_stay.fillna(-1).astype(int)
    for key, cfg in TASKS.items():
        tr_df, imp = fitted[key]
        feats = cfg["features"]
        mdl = tree(out_trees[key]["params"]).fit(imp.transform(tr_df, feats), tr_df[f"y_{key}"])
        rows = t9
        if key == "water":
            rows = t9[t9.hours_since_water.notna() & (t9.dw_km * 1000 > C.WATER_BUFFER_M)]
        elif key == "speed":
            rows = t9[t9.hour.ge(6) & t9.hour.lt(18)]               # dự đoán tốc độ nếu voi đi
        elif key == "stay":
            rows = t9[t9.dw_km * 1000 <= C.WATER_BUFFER_M]
        X = imp.transform(rows, feats)
        leaves = mdl.apply(X)
        pred[f"pred_{key}"], pred[f"leaf_{key}"], pred[f"conf_{key}"] = -1, -1, 0.0
        pred.loc[rows.index, f"pred_{key}"] = mdl.predict(X)
        pred.loc[rows.index, f"leaf_{key}"] = leaves
        pred.loc[rows.index, f"conf_{key}"] = [out_trees[key]["nodes"][l]["conf"] for l in leaves]
    pred.to_parquet(C.OUT / "tasks_pred.parquet", index=False)
    (C.OUT / "tasks_trees.json").write_text(json.dumps({"feature_labels": FEATURE_LABELS, "trees": out_trees}, ensure_ascii=False, indent=1), "utf-8")
    (C.OUT / "tasks_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, default=float), "utf-8")


if __name__ == "__main__":
    main()
