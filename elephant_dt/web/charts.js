// charts.js: biểu đồ SVG nhỏ gọn (không cần thư viện) và hàm vẽ cây quyết định.
(function () {
  const NS = "http://www.w3.org/2000/svg";

  function svgEl(tag, attrs = {}, parent) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) if (attrs[k] != null) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const fmt = (v, d = 1) =>
    v == null || Number.isNaN(v) ? "—" : Number(v).toLocaleString("vi-VN", { minimumFractionDigits: d, maximumFractionDigits: d });
  const fmtInt = (v) => Number(v).toLocaleString("vi-VN");
  const fmtPct = (v, d = 0) => fmt(v * 100, d) + "%";
  function fmtHour(h) {
    // làm tròn xuống theo phút, giống phía Python
    const tot = Math.floor((((h % 24) + 24) % 24) * 60 + 1e-6);
    return String(Math.floor(tot / 60)).padStart(2, "0") + ":" + String(tot % 60).padStart(2, "0");
  }

  const FEAT_SHORT = {
    prev_bearing: "Hướng dịch chuyển trước đó", prev_dist: "Độ dịch chuyển trước đó", hour: "Giờ địa phương tại Kruger", temp: "Nhiệt độ đo tại vòng cổ", wet: "Mùa theo lịch quy ước",
    dw_km: "Khoảng cách tới nguồn nước gần nhất", water_bearing: "Hướng tới nguồn nước gần nhất", hours_since_water: "Thời gian ngoài vùng gần nước",
    woody: "Độ che phủ cây gỗ tại vị trí GPS", woody_missing: "Thiếu dữ liệu độ che phủ cây gỗ",
  };

  function fmtValue(f, v) {
    switch (f) {
      case "hour": return fmtHour(v);
      case "temp": return fmt(v, 1) + "°C";
      case "dw_km": return v < 1 ? fmtInt(Math.round(v * 1000)) + " m" : fmt(v, 2) + " km";
      case "hours_since_water": return fmt(v, 1) + " giờ";
      case "woody": return fmt(v, 1) + "%";
      case "woody_missing": return v > 0.5 ? "thiếu dữ liệu cây gỗ" : "có dữ liệu cây gỗ";
      case "prev_dist": return fmtInt(Math.round(v)) + " m";
      case "prev_bearing": case "water_bearing": return Math.round(v) + "° " + compass(v);
      case "wet": return v > 0.5 ? "mùa mưa" : "mùa khô";
      default: return fmt(v, 2);
    }
  }
  function splitText(f, thr, dir) {
    if (f === "wet") return dir === "left" ? "mùa khô" : "mùa mưa";
    if (f === "woody_missing") return dir === "left" ? "có dữ liệu" : "thiếu dữ liệu";
    return (dir === "left" ? "≤ " : "> ") + fmtValue(f, thr);
  }

  // ---------- Tooltip dùng chung ----------
  const tip = document.getElementById("tooltip");
  function showTip(html, x, y) {
    tip.innerHTML = html;
    tip.hidden = false;
    const r = tip.getBoundingClientRect();
    let left = x + 14, top = y + 14;
    if (left + r.width > innerWidth - 8) left = x - r.width - 14;
    if (top + r.height > innerHeight - 8) top = y - r.height - 14;
    tip.style.left = Math.max(8, left) + "px";
    tip.style.top = Math.max(8, top) + "px";
  }
  function hideTip() { tip.hidden = true; }
  const keyHtml = (color, dot) => `<i class="key${dot ? " dot" : ""}" style="background:${color}"></i>`;

  function niceTicks(min, max, n = 4) {
    if (min === max) { min -= 1; max += 1; }
    const step0 = (max - min) / n;
    const mag = Math.pow(10, Math.floor(Math.log10(step0)));
    const err = step0 / mag;
    const step = (err >= 7.5 ? 10 : err >= 3.5 ? 5 : err >= 1.5 ? 2 : 1) * mag;
    const lo = Math.floor(min / step) * step, hi = Math.ceil(max / step) * step;
    const ticks = [];
    for (let v = lo; v <= hi + step * 1e-9; v += step) ticks.push(+v.toFixed(10));
    return { ticks, lo, hi };
  }

  function frame(container, { title, legend, height = 150, margin }) {
    const m = Object.assign({ t: 8, r: 12, b: 24, l: 36 }, margin || {});
    container.innerHTML = "";
    const wrap = document.createElement("div");
    wrap.className = "chart";
    container.appendChild(wrap);
    if (title) {
      const t = document.createElement("div");
      t.className = "title";
      t.textContent = title;
      wrap.appendChild(t);
    }
    if (legend && legend.length > 1) {
      const lg = document.createElement("div");
      lg.className = "legend-inline";
      lg.innerHTML = legend.map((l) => `<span>${keyHtml(l.color, l.dot)}${l.name}</span>`).join("");
      wrap.appendChild(lg);
    }
    const width = Math.max(240, wrap.clientWidth || 360);
    const svg = svgEl("svg", { width, height, viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": title || "" }, wrap);
    return { wrap, svg, width, height, m, iw: width - m.l - m.r, ih: height - m.t - m.b };
  }

  // ---------- Biểu đồ đường có dải tin cậy ----------
  function lineChart(container, opt) {
    const f = frame(container, { title: opt.title, legend: opt.series, height: opt.height || 150 });
    const { svg, m, iw, ih } = f;
    const surface = css("--surface");
    const xs = opt.series.flatMap((s) => s.pts.map((p) => p.x));
    const ys = opt.series.flatMap((s) => s.pts.flatMap((p) => [p.lo ?? p.y, p.hi ?? p.y])).filter((v) => v != null);
    const xMin = Math.min(...xs), xMax = Math.max(...xs);
    const yt = niceTicks(opt.yMin ?? Math.min(...ys), Math.max(...ys), 4);
    const X = (v) => m.l + ((v - xMin) / (xMax - xMin)) * iw;
    const Y = (v) => m.t + ih - ((v - yt.lo) / (yt.hi - yt.lo)) * ih;
    const g = svgEl("g", { class: "axis" }, svg);
    yt.ticks.forEach((v) => {
      svgEl("line", { x1: m.l, x2: m.l + iw, y1: Y(v), y2: Y(v), class: "gridline" }, g);
      svgEl("text", { x: m.l - 6, y: Y(v) + 3, "text-anchor": "end" }, g).textContent = opt.yFormat ? opt.yFormat(v) : fmt(v, 1);
    });
    (opt.xTicks || []).forEach((v) => {
      svgEl("text", { x: X(v), y: m.t + ih + 15, "text-anchor": "middle" }, g).textContent = opt.xFormat ? opt.xFormat(v) : v;
    });
    svgEl("line", { x1: m.l, x2: m.l + iw, y1: m.t + ih, y2: m.t + ih }, g);
    for (const s of opt.series) {
      const pts = s.pts.filter((p) => p.y != null);
      if (pts.length && pts[0].lo != null) {
        const d = "M" + pts.map((p) => `${X(p.x)},${Y(p.hi)}`).join("L") + "L" + pts.slice().reverse().map((p) => `${X(p.x)},${Y(p.lo)}`).join("L") + "Z";
        svgEl("path", { d, fill: s.color, "fill-opacity": 0.12, stroke: "none" }, svg);
      }
      svgEl("path", {
        d: "M" + pts.map((p) => `${X(p.x)},${Y(p.y)}`).join("L"),
        fill: "none", stroke: s.color, "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round",
        "stroke-dasharray": s.dash || null,
      }, svg);
      if (s.dots !== false) pts.forEach((p) => svgEl("circle", { cx: X(p.x), cy: Y(p.y), r: 4, fill: s.color, stroke: surface, "stroke-width": 2 }, svg));
    }
    const allX = [...new Set(xs)].sort((a, b) => a - b);
    const cross = svgEl("line", { y1: m.t, y2: m.t + ih, stroke: css("--axis"), visibility: "hidden" }, svg);
    const overlay = svgEl("rect", { x: m.l - 6, y: m.t, width: iw + 12, height: ih, fill: "transparent" }, svg);
    overlay.addEventListener("mousemove", (ev) => {
      const r = svg.getBoundingClientRect();
      const px = ev.clientX - r.left;
      let best = allX[0];
      for (const v of allX) if (Math.abs(X(v) - px) < Math.abs(X(best) - px)) best = v;
      cross.setAttribute("x1", X(best));
      cross.setAttribute("x2", X(best));
      cross.setAttribute("visibility", "visible");
      const rows = opt.series.map((s) => {
        const p = s.pts.find((q) => q.x === best);
        return p && p.y != null ? `<div class="t-row">${keyHtml(s.color)}${s.name}: <b>${opt.valueFormat ? opt.valueFormat(p) : fmt(p.y, 2)}</b></div>` : "";
      }).join("");
      showTip(`<div class="t-head">${opt.xFormat ? opt.xFormat(best) : best}</div>${rows}`, ev.clientX, ev.clientY);
    });
    overlay.addEventListener("mouseleave", () => { cross.setAttribute("visibility", "hidden"); hideTip(); });
  }


  // ---------- Cột chồng 100% (tỉ lệ trạng thái theo giờ) ----------

  // ---------- Cây quyết định (bố cục ngang: gốc bên trái, lá bên phải) ----------
  function renderTree(container, model, opts) {
    const nodes = model.nodes;
    const pos = {};
    let row = 0, maxDepth = 0;
    (function walk(id, depth) {
      const n = nodes[id];
      maxDepth = Math.max(maxDepth, depth);
      if (n.leaf) { pos[id] = { d: depth, y: row++ }; return pos[id].y; }
      const a = walk(n.left, depth + 1), b = walk(n.right, depth + 1);
      pos[id] = { d: depth, y: (a + b) / 2 };
      return pos[id].y;
    })(0, 0);

    const L = opts.large;
    const leafCount = nodes.filter((q) => q.leaf).length;
    const rowH = L ? (leafCount > 10 ? 64 : 76) : 68, colW = L ? (leafCount > 10 ? 250 : 304) : 270, boxW = L ? 180 : 160, leafW = L ? 260 : 230, boxH = 48, pad = 8;
    const leafX = maxDepth * colW;
    const W = pad * 2 + leafX + leafW + (opts.pattern ? 78 : 0), H = pad * 2 + row * rowH;
    const X = (id) => pad + (nodes[id].leaf ? leafX : pos[id].d * colW);
    const Yc = (id) => pad + pos[id].y * rowH + rowH / 2;

    container.innerHTML = "";
    const svg = svgEl("svg", { width: W, height: H, viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": "Cây quyết định" }, container);
    const hl = opts.highlight || new Set();
    const pat = opts.pattern || null, patColor = css("--pattern") || "#f5b301";   // đường root → lá tạo nên pattern
    const accent = css("--accent"), axis = css("--axis"), surface = css("--surface"), surface2 = css("--surface-2"), border = css("--border");
    const fontSize = L ? 12 : 11;
    function wrapText(text, maxChars) {
      const lines = [];
      for (const word of text.split(/\s+/)) {
        const i = lines.length - 1;
        if (i >= 0 && (lines[i] + " " + word).length <= maxChars) lines[i] += " " + word;
        else lines.push(word);
      }
      return lines;
    }
    function textLines(parent, lines, x, firstY, attrs = {}) {
      const text = svgEl("text", Object.assign({ x, y: firstY, "font-size": fontSize, "font-weight": 600 }, attrs), parent);
      lines.forEach((line, i) => { svgEl("tspan", { x, dy: i ? 15 : 0 }, text).textContent = line; });
      return text;
    }

    // Cạnh
    for (const n of nodes) {
      if (n.leaf) continue;
      for (const [cid, dir] of [[n.left, "left"], [n.right, "right"]]) {
        const x1 = X(n.id) + boxW, y1 = Yc(n.id), x2 = X(cid), y2 = Yc(cid);
        const on = hl.has(n.id) && hl.has(cid), pon = !!pat && pat.has(n.id) && pat.has(cid);
        const mx = x1 + Math.min(28, (x2 - x1) / 2);
        const eg = svgEl("g", { opacity: 1 }, svg);
        svgEl("path", {
          d: `M${x1},${y1}C${mx},${y1} ${mx},${y2} ${x2 - (L ? 50 : 30)},${y2}L${x2},${y2}`,
          fill: "none", stroke: pon ? patColor : on ? accent : axis, "stroke-width": pon ? 3 : on ? 2.5 : 1.25,
          "stroke-linecap": "round",
        }, eg);
        const t = svgEl("text", {
          x: x2 - 4, y: y2 - 5, "text-anchor": "end", "font-size": fontSize - 1,
          style: `paint-order:stroke;stroke:${surface};stroke-width:3px`,
          "font-weight": on || pon ? 700 : 400,
        }, eg);
        t.textContent = (opts.splitText || splitText)(n.feature, n.threshold, dir);
      }
    }

    // Nút
    for (const n of nodes) {
      const x = X(n.id), yc = Yc(n.id);
      const pon = !!pat && pat.has(n.id);
      const g = svgEl("g", { style: n.leaf ? "cursor:pointer" : "", opacity: 1 }, svg);
      const on = hl.has(n.id);
      if (!n.leaf) {
        svgEl("rect", { x, y: yc - boxH / 2, width: boxW, height: boxH, rx: 6, fill: surface2, stroke: pon ? patColor : on ? accent : border, "stroke-width": pon ? 2 : on ? 2 : 1 }, g);
        const lines = opts.featureLines?.[n.feature] || wrapText(FEAT_SHORT[n.feature] || n.feature, 24);
        textLines(g, lines, x + boxW / 2, yc + 4 - (lines.length - 1) * 7.5, { "text-anchor": "middle" });
        svgEl("title", {}, g).textContent = opts.featureDescriptions?.[n.feature] || FEAT_SHORT[n.feature] || n.feature;
      } else {
        const sel = opts.selectedLeaf === n.id;
        const h = rowH - 6;
        const [line1, line2] = opts.leafText(n);
        svgEl("rect", { x, y: yc - h / 2, width: leafW, height: h, rx: 6, fill: surface2, stroke: pon ? patColor : sel || on ? accent : border, "stroke-width": pon ? 2.5 : sel || on ? 2 : 1 }, g);
        if (pon) {
          const tag = svgEl("g", {}, g);
          svgEl("rect", { x: x + leafW + 8, y: yc - 10, width: 62, height: 20, rx: 10, fill: patColor }, tag);
          svgEl("text", { x: x + leafW + 39, y: yc + 4, "text-anchor": "middle", "font-size": 12, "font-weight": 700, fill: "#2b2100" }, tag).textContent = "Pattern";
        }
        svgEl("rect", { x: x + 4, y: yc - h / 2 + 4, width: 4, height: h - 8, rx: 2, fill: opts.leafColor(n) }, g);
        const lines = wrapText(line1, L ? 32 : 30);
        const firstY = yc - (lines.length > 1 ? 14 : 6);
        textLines(g, lines, x + 14, firstY);
        svgEl("text", { x: x + 14, y: firstY + lines.length * 15 + 2, "font-size": fontSize - 1, style: `fill:${css("--ink-2")}` }, g).textContent = line2;
        g.addEventListener("click", () => opts.onLeafClick && opts.onLeafClick(n.id));
      }
      g.addEventListener("mousemove", (ev) => showTip(opts.nodeTip(n), ev.clientX, ev.clientY));
      g.addEventListener("mouseleave", hideTip);
    }
  }

  window.Viz = {
    svgEl, css, fmt, fmtInt, fmtPct, fmtHour, fmtValue, splitText, showTip, hideTip, keyHtml,
    lineChart, renderTree, FEAT_SHORT,
  };
})();
