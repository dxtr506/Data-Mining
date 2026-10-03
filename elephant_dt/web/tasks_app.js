// tasks_app.js: phát lại GPS năm 2009. Hai câu hỏi cho Decision Tree: (1) voi nghỉ hay di chuyển trong 90 phút tới,
// (2) voi đang ở xa nước có quay lại vùng nước trong 3 giờ tới không. Một cách thể hiện duy nhất: vệt trắng = đường đi
// thật; huy hiệu cạnh voi = dự đoán của cây đang chọn; bấm vào voi để so với thực tế.
(function () {
  const { css, fmt, fmtInt, fmtPct, fmtHour } = Viz;
  const LAY = window.KNP_LAYERS, TRK = window.KNP_TRACKS, TK = window.KNP_TASKS;
  const LABEL = TK.feature_labels, EDA = TK.eda;
  const STEP = 90, GAP_MIN = 180, LINK_MAX = 2 * 1440, TRAIL = 3 * 1440;
  const SPEEDS = [30, 60, 120, 240];
  const T0 = Date.parse(TRK.t0), OFF = TRK.utc_offset_h, BUF = TRK.water_buffer_m;
  const $ = (id) => document.getElementById(id);

  // ---------- Icon ----------
  const S = (d) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${d}</svg>`;
  const ICO = {
    play: '<svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z" fill="currentColor"/></svg>',
    pause: '<svg viewBox="0 0 24 24"><path d="M7 5h4v14H7zM13 5h4v14h-4z" fill="currentColor"/></svg>',
    clock: S('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>'),
    thermo: S('<path d="M14 14.8V5a2 2 0 0 0-4 0v9.8a4 4 0 1 0 4 0z"/>'),
    drop: S('<path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z"/>'),
    sun: S('<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>'),
    moon: S('<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>'),
    hourglass: S('<path d="M6 3h12M6 21h12M7 3c0 4 5 6 5 9s-5 5-5 9M17 3c0 4-5 6-5 9s5 5 5 9"/>'),
    leaf: S('<path d="M5 19c9 0 14-5 14-14-9 0-14 5-14 14z"/><path d="M5 19l7-7"/>'),
    signal: S('<path d="M2 8.5a15 15 0 0 1 20 0M5 12a10 10 0 0 1 14 0M8.5 15.5a5 5 0 0 1 7 0"/><path d="M3 3l18 18"/>'),
    rules: S('<path d="M9 6h11M9 12h11M9 18h11"/><circle cx="4.5" cy="6" r="1"/><circle cx="4.5" cy="12" r="1"/><circle cx="4.5" cy="18" r="1"/>'),
    tree: S('<circle cx="5" cy="12" r="2"/><circle cx="19" cy="5" r="2"/><circle cx="19" cy="19" r="2"/><path d="M7 12h4M11 5v14M11 5h6M11 19h6"/>'),
    chart: S('<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>'),
    close: S('<path d="M6 6l12 12M18 6L6 18"/>'),
    target: S('<circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>'),
    next: S('<path d="M5 12h14M13 6l6 6-6 6"/>'),
    walk: S('<path d="M5 12h14M13 6l6 6-6 6"/>'),
    rest: S('<path d="M9.5 8v8M14.5 8v8"/><circle cx="12" cy="12" r="9"/>'),
    toward: S('<path d="M4 12h11M10 6l6 6-6 6"/><path d="M20 8s2 2.2 2 4a2 2 0 0 1-4 0c0-1.8 2-4 2-4z" fill="currentColor" stroke="none"/>'),
    notyet: S('<path d="M6 12h12"/><circle cx="12" cy="12" r="9"/>'),
    slow: S('<path d="M5 15h14"/><path d="M9 11h6"/>'),
    fast: S('<path d="M4 12h8M8 7l5 5-5 5M12 12h8"/>'),
    leave: S('<path d="M5 12h14M13 6l6 6-6 6"/>'),
    stay: S('<circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2" fill="currentColor"/>'),
    present: S('<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>'),
    full: S('<path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/>'),
    spark: S('<path d="M12 3l2.2 6.3L21 12l-6.8 2.7L12 21l-2.2-6.3L3 12l6.8-2.7z"/>'),
  };
  const ico = (name) => `<i data-ico="${name}">${ICO[name]}</i>`;
  function fillIcons(root = document) { root.querySelectorAll("i[data-ico]").forEach((el) => { if (!el.innerHTML.trim()) el.innerHTML = ICO[el.dataset.ico] || ""; }); }
  function elephantSvg(ring, flip) {
    const g = flip ? ' transform="translate(64 0) scale(-1 1)"' : "";
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
<circle cx="32" cy="32" r="28.5" fill="#1a1a19" fill-opacity="0.92" stroke="${ring}" stroke-width="4"/>
<g${g}><g fill="#ffffff"><ellipse cx="27" cy="33" rx="13" ry="9.5"/><circle cx="40" cy="28.5" r="8"/>
<rect x="16.5" y="35" width="5.5" height="12" rx="2"/><rect x="24" y="37" width="5.5" height="10" rx="2"/>
<rect x="31" y="37" width="5.5" height="10" rx="2"/><rect x="37.5" y="33" width="5.5" height="14" rx="2"/></g>
<path d="M45.5 30.5c3.5 2.5 4 8 2.5 13.5" fill="none" stroke="#ffffff" stroke-width="4.2" stroke-linecap="round"/>
<path d="M14.8 30.5c-2.2 1.6-2.6 4.4-2 7" fill="none" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round"/>
<path d="M35.5 21.5c-5 0-6.5 9.5-1.5 13 2.5-1.5 4-8 1.5-13z" fill="#1a1a19" fill-opacity="0.35"/>
<circle cx="42.5" cy="26.5" r="1.3" fill="#1a1a19"/></g></svg>`;
  }
  const svgUrl = (svg) => "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);

  // ---------- Hai câu hỏi ----------
  // Màu: câu 1 dùng xanh lá (nghỉ) / cam (di chuyển); câu 2 dùng xanh dương (về nước) / xám (chưa). Luôn kèm ký hiệu.
  const TASKS = {
    rest: { key: "rest", name: "Nghỉ hay di chuyển?", short: "Nghỉ", horizon: "90 phút tới", hotkey: "1",
            question: "Trong 90 phút tới voi nghỉ hay di chuyển?", classes: TK.tasks.rest.classes,
            colors: [css("--m-low"), css("--m-local")], glyph: ["rest", "walk"],
            paths: ['<path d="M9.5 7v10M14.5 7v10"/>', '<path d="M5 12h14M13 6l6 6-6 6"/>'] },
    water: { key: "water", name: "Có quay lại nước không?", short: "Về nước", horizon: "3 giờ tới", hotkey: "2",
             question: "Voi đang ở xa nước có quay lại vùng nước trong 3 giờ tới không?", classes: TK.tasks.water.classes,
             colors: [css("--c-stop"), css("--m-dir")], glyph: ["notyet", "toward"],
             paths: ['<path d="M7 12h10"/>', '<path d="M4 12h11M10 6l6 6-6 6"/>'] },
    speed: { key: "speed", name: "Đi nhanh hay chậm?", short: "Tốc độ", horizon: "90 phút tới", hotkey: "3",
             question: "Ban ngày, khi voi đi, voi đi nhanh hay chậm?", classes: TK.tasks.speed.classes,
             colors: [css("--t-slow"), css("--t-fast")], glyph: ["slow", "fast"],
             paths: ['<path d="M5 15h14"/><path d="M9 11h6"/>', '<path d="M4 12h8M8 7l5 5-5 5M12 12h8"/>'] },
    stay: { key: "stay", name: "Ở lại hay rời vùng nước?", short: "Ở nước", horizon: "90 phút tới", hotkey: "4",
            question: "Voi đang ở trong vùng nước sẽ ở lại hay rời đi?", classes: TK.tasks.stay.classes,
            colors: [css("--c-stop"), css("--t-stay")], glyph: ["leave", "stay"],
            paths: ['<path d="M5 12h14M13 6l6 6-6 6"/>', '<circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="1.8" fill="#fff"/>'] },
  };
  const hexRgb = (h) => { const n = parseInt(h.replace("#", ""), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; };
  const COL = { accent: hexRgb(css("--accent")), water: hexRgb(css("--water-line")), ink: hexRgb(css("--ink")), surface: hexRgb(css("--surface")) };
  for (const t of Object.values(TASKS)) {
    t.rgb = t.colors.map(hexRgb);
    t.badge = t.colors.map((c, k) => svgUrl(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">
<circle cx="24" cy="24" r="21" fill="${c}" stroke="#ffffff" stroke-width="3"/>
<g transform="translate(9 9) scale(1.25)" fill="none" stroke="#ffffff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">${t.paths[k]}</g></svg>`));
  }
  const ICON_URL = {
    normal: [svgUrl(elephantSvg("#ffffff", false)), svgUrl(elephantSvg("#ffffff", true))],
    sel: [svgUrl(elephantSvg(css("--accent"), false)), svgUrl(elephantSvg(css("--accent"), true))],
  };
  const clsIco = (t, k) => `<span class="cls-ico" style="color:${t.colors[k]}">${ICO[t.glyph[k]]}</span>`;

  // ---------- Dữ liệu ----------
  const ELE = TRK.elephants.filter((e) => TK.elephants[e.id]).map((e) => {
    for (const k of TRK.delta) { const a = e[k]; for (let i = 1; i < a.length; i++) a[i] += a[i - 1]; }
    const lonF = new Float64Array(e.n), latF = new Float64Array(e.n);
    for (let i = 0; i < e.n; i++) { lonF[i] = e.lon[i] / 1e5; latF[i] = e.lat[i] / 1e5; }
    return Object.assign(e, { lonF, latF, mv: TK.elephants[e.id] });
  });
  const BYID = Object.fromEntries(ELE.map((e) => [e.id, e]));
  const tMin = Math.round((Date.parse("2009-01-01T00:00:00Z") - OFF * 3600e3 - T0) / 60000);
  let tMax = -Infinity;
  for (const e of ELE) tMax = Math.max(tMax, e.t[e.n - 1]);
  const localDate = (tm) => new Date(T0 + (tm + OFF * 60) * 60000);
  const localHour = (tm) => { const d = localDate(tm); return d.getUTCHours() + d.getUTCMinutes() / 60; };
  const fmtDate = (tm) => { const d = localDate(tm); return `${String(d.getUTCDate()).padStart(2, "0")}/${String(d.getUTCMonth() + 1).padStart(2, "0")}/${d.getUTCFullYear()} · ${fmtHour(localHour(tm))}`; };

  const app = { playing: false, speed: 0, time: tMin + 6 * 60, selected: null, follow: false, leaf: null, panel: null,
                task: "rest", visible: new Set(ELE.map((e) => e.id)) };
  let dirty = true;
  const shown = () => ELE.filter((e) => app.visible.has(e.id));
  const TASK = () => TASKS[app.task];
  const MODEL = (k = app.task) => TK.tasks[k];

  function bsearch(arr, v) {
    let lo = 0, hi = arr.length - 1;
    if (hi < 0 || v < arr[0]) return -1;
    while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (arr[mid] <= v) lo = mid; else hi = mid; }
    return arr[hi] <= v ? hi : lo;
  }
  function headAt(e, tm) {
    if (tm < e.t[0] || tm > e.t[e.n - 1]) return null;
    const i = bsearch(e.t, tm), j = Math.min(i + 1, e.n - 1), gap = e.t[j] - e.t[i];
    if (gap > LINK_MAX && tm - e.t[i] > 30) return null;
    const f = gap > 0 && gap <= LINK_MAX ? (tm - e.t[i]) / gap : 0;
    return { e, i, flip: j > i ? e.lonF[j] < e.lonF[i] : false, interp: gap > GAP_MIN && tm > e.t[i] + 30,
             lon: e.lonF[i] + (e.lonF[j] - e.lonF[i]) * f, lat: e.latF[i] + (e.latF[j] - e.latF[i]) * f };
  }
  function winRow(e, k) {
    const m = e.mv, lon = m.lon[k] / 1e5, lat = m.lat[k] / 1e5;
    return { e, k, t: m.t[k], lon, lat, wlon: lon + m.wx[k] / 1e5, wlat: lat + m.wy[k] / 1e5, dw: m.dw[k], temp: m.temp[k],
             woody: m.woody[k] < 0 ? null : m.woody[k] / 10, hsw: m.hsw[k] < 0 ? null : m.hsw[k] / 10, apath: m.apath[k], mtw: m.mtw[k],
             ...Object.fromEntries(["rest", "water", "speed", "stay"].map((q) =>
               [q, { pred: m[`pred_${q}`][k], actual: m[`actual_${q}`][k], leaf: m[`leaf_${q}`][k], conf: m[`conf_${q}`][k] / 100 }])) };
  }
  function winAt(e, tm) {
    const k = bsearch(e.mv.t, tm);
    return k < 0 || tm - e.mv.t[k] >= STEP ? null : winRow(e, k);
  }
  function leafUses(leaf) {
    const out = [], key = `leaf_${app.task}`;
    for (const e of shown()) for (let k = 0; k < e.mv.t.length; k++) if (e.mv[key][k] === leaf) out.push(winRow(e, k));
    return out.sort((a, b) => a.t - b.t);
  }

  // ---------- Bản đồ ----------
  function ringArea(r) { let s = 0; for (let i = 0; i < r.length - 1; i++) s += (r[i + 1][0] - r[i][0]) * (r[i + 1][1] + r[i][1]); return s; }
  const holes = [];
  let bb = [180, 90, -180, -90];
  for (const f of LAY.area.features) {
    const g = f.geometry;
    for (const poly of g.type === "Polygon" ? [g.coordinates] : g.coordinates) {
      holes.push(poly[0]);
      for (const [x, y] of poly[0]) bb = [Math.min(bb[0], x), Math.min(bb[1], y), Math.max(bb[2], x), Math.max(bb[3], y)];
    }
  }
  const outer = [[10, -45], [60, -45], [60, -5], [10, -5], [10, -45]];
  const mask = { type: "Feature", properties: {}, geometry: { type: "Polygon",
    coordinates: [outer, ...holes.map((h) => (Math.sign(ringArea(h)) === Math.sign(ringArea(outer)) ? h.slice().reverse() : h))] } };
  const map = new maplibregl.Map({
    container: "map",
    style: { version: 8,
      sources: {
        sat: { type: "raster", tileSize: 256, maxzoom: 18,
               tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
               attribution: "Ảnh vệ tinh © Esri, Maxar, Earthstar Geographics · Mặt nước © OpenStreetMap" },
        mask: { type: "geojson", data: mask }, area: { type: "geojson", data: LAY.area } },
      layers: [
        { id: "bg", type: "background", paint: { "background-color": css("--map-bg") } },
        { id: "sat", type: "raster", source: "sat", paint: { "raster-saturation": -0.1 } },
        { id: "mask", type: "fill", source: "mask", paint: { "fill-color": css("--map-bg"), "fill-opacity": 1 } },
        { id: "edge", type: "line", source: "area", paint: { "line-color": "#ffffff", "line-opacity": 0.35, "line-width": 1.2 } }] },
    bounds: [[bb[0], bb[1]], [bb[2], bb[3]]], fitBoundsOptions: { padding: { top: 90, bottom: 150, left: 40, right: 40 } },
    maxBounds: [[bb[0] - 3, bb[1] - 1], [bb[2] + 3, bb[3] + 1]], renderWorldCopies: false, dragRotate: false, maxZoom: 17,
    attributionControl: { compact: true },
  });
  map.touchZoomRotate.disableRotation();
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");
  map.once("load", () => map.setMinZoom(Math.max(0, map.getZoom() - 0.3)));
  map.on("zoom", () => render());
  const overlay = new deck.MapboxOverlay({ interleaved: false, layers: [], getTooltip, onClick });
  map.addControl(overlay);

  // Vệt đường đi thật: một màu duy nhất (trắng). Đoạn mất GPS (> 3 giờ, ≤ 2 ngày) nối thẳng và vẽ mờ.
  function buildTrips(list, rgb) {
    let nV = 0, nP = 0;
    for (const e of list) { nV += e.n; nP++; for (let i = 1; i < e.n; i++) if (e.t[i] - e.t[i - 1] > LINK_MAX) nP++; }
    const pos = new Float32Array(nV * 2), ts = new Float32Array(nV), col = new Uint8Array(nV * 4), starts = new Uint32Array(nP);
    let v = 0, p = 0;
    for (const e of list) {
      for (let i = 0; i < e.n; i++) {
        if (i === 0 || e.t[i] - e.t[i - 1] > LINK_MAX) starts[p++] = v;
        pos[v * 2] = e.lonF[i]; pos[v * 2 + 1] = e.latF[i]; ts[v] = e.t[i];
        const gapAfter = i < e.n - 1 && e.t[i + 1] - e.t[i] > GAP_MIN;
        col.set([rgb[0], rgb[1], rgb[2], gapAfter ? 60 : 230], v * 4);
        v++;
      }
    }
    return { length: nP, startIndices: starts,
             attributes: { getPath: { value: pos, size: 2 }, getTimestamps: { value: ts, size: 1 }, getColor: { value: col, size: 4 } } };
  }
  let tripsAll = buildTrips(shown(), [255, 255, 255]);
  const tripsOne = {};
  const tripsFor = (id) => (tripsOne[id] ||= buildTrips([BYID[id]], COL.accent));

  let leafData = null;
  function buildLeaf() { leafData = app.leaf == null ? null : leafUses(app.leaf); }

  // Huy hiệu hiển thị của một cửa sổ theo câu hỏi đang chọn (null = không có dự đoán / không áp dụng)
  const predOf = (w) => { const p = w[app.task].pred; return p >= 0 ? p : null; };

  function layers() {
    const D = deck, out = [], T = TASK(), zoom = map.getZoom(), near = zoom >= 11;
    if (LAY.water) {
      out.push(new D.GeoJsonLayer({ id: "water", data: LAY.water, stroked: true, filled: true,
        getFillColor: [...COL.water, near ? 140 : 80], getLineColor: [...COL.water, 220], lineWidthUnits: "pixels",
        getLineWidth: near ? 1.2 : 0.5, updateTriggers: { getFillColor: near, getLineWidth: near } }));
    }
    out.push(new D.GeoJsonLayer({ id: "rivers", data: LAY.rivers, stroked: true, filled: false,
      getLineColor: (f) => [...COL.water, f.properties.perennial ? 190 : 100], lineWidthUnits: "meters",
      getLineWidth: (f) => (f.properties.perennial ? 22 : 9), lineWidthMinPixels: 0.8, lineWidthMaxPixels: 7 }));
    out.push(new D.ScatterplotLayer({ id: "waterholes", data: LAY.waterholes.features, pickable: true,
      getPosition: (f) => f.geometry.coordinates, radiusUnits: "meters", getRadius: BUF, radiusMinPixels: 3, stroked: true,
      getFillColor: [...COL.water, 70], getLineColor: [...COL.water, 230], lineWidthUnits: "pixels", getLineWidth: 1.5 }));
    if (zoom >= 12) {
      out.push(new D.TextLayer({ id: "waterhole-names", data: LAY.waterholes.features, getPosition: (f) => f.geometry.coordinates,
        getText: (f) => f.properties.name, getSize: 11, getPixelOffset: [0, -14], getColor: [...COL.ink, 230],
        background: true, getBackgroundColor: [...COL.surface, 170], backgroundPadding: [3, 1],
        fontFamily: "system-ui, -apple-system, Segoe UI, sans-serif" }));
    }
    const sel = app.selected;
    out.push(new D.TripsLayer({ id: "trails", data: tripsAll, _pathType: "open", currentTime: app.time, trailLength: TRAIL,
      fadeTrail: true, widthUnits: "pixels", getWidth: 2.5, capRounded: true, jointRounded: true, opacity: sel ? 0.3 : 0.95 }));
    if (sel) {
      out.push(new D.TripsLayer({ id: "trail-sel", data: tripsFor(sel), _pathType: "open", currentTime: app.time, trailLength: TRAIL,
        fadeTrail: true, widthUnits: "pixels", getWidth: 4, capRounded: true, jointRounded: true }));
    }
    if (leafData) {
      out.push(new D.IconLayer({ id: "leaf-uses", data: leafData.filter((r) => predOf(r) != null), getPosition: (r) => [r.lon, r.lat],
        getIcon: (r) => ({ url: T.badge[predOf(r)], id: `${T.key}${predOf(r)}`, width: 48, height: 48 }), getSize: 12, sizeUnits: "pixels" }));
    }
    const heads = shown().map((e) => headAt(e, app.time)).filter(Boolean);
    const wins = heads.filter((h) => !h.interp).map((h) => { const w = winAt(h.e, app.time); return w && predOf(w) != null ? Object.assign(w, { hl: h }) : null; }).filter(Boolean);
    if (app.task === "water") {      // đường mảnh từ voi tới nguồn nước gần nhất khi cây dự đoán sẽ về nước
      out.push(new D.LineLayer({ id: "to-water", data: wins.filter((w) => w.water.pred === 1),
        getSourcePosition: (w) => [w.hl.lon, w.hl.lat], getTargetPosition: (w) => [w.wlon, w.wlat],
        getColor: [...T.rgb[1], 170], getWidth: 2, widthUnits: "pixels" }));
    }
    if (sel) {
      const h = heads.find((x) => x.e.id === sel);
      if (h) {
        out.push(new D.ScatterplotLayer({ id: "halo", data: [h], getPosition: (x) => [x.lon, x.lat], radiusUnits: "pixels",
          getRadius: 30, getFillColor: [...COL.accent, 50], stroked: false }));
        if (app.follow) map.jumpTo({ center: [h.lon, h.lat] });
      }
    }
    out.push(new D.IconLayer({ id: "elephants", data: heads, pickable: true, getPosition: (h) => [h.lon, h.lat],
      getIcon: (h) => { const s = h.e.id === sel ? "sel" : "normal"; return { url: ICON_URL[s][h.flip ? 1 : 0], id: `${s}${h.flip ? 1 : 0}`, width: 64, height: 64 }; },
      getSize: (h) => (h.e.id === sel ? 46 : 34), sizeUnits: "pixels" }));
    out.push(new D.IconLayer({ id: "badges", data: wins, pickable: true, getPosition: (w) => [w.hl.lon, w.hl.lat],
      getIcon: (w) => ({ url: T.badge[predOf(w)], id: `${T.key}${predOf(w)}`, width: 48, height: 48 }),
      getSize: 24, sizeUnits: "pixels", getPixelOffset: (w) => (w.e.id === sel ? [26, -24] : [20, -18]) }));
    out.push(new D.TextLayer({ id: "labels", data: heads, getPosition: (h) => [h.lon, h.lat], getText: (h) => h.e.id,
      getSize: 11, getPixelOffset: [0, 26], getTextAnchor: "middle", getAlignmentBaseline: "top",
      getColor: [...COL.ink, 255], background: true, getBackgroundColor: [...COL.surface, 200], backgroundPadding: [4, 1],
      fontFamily: "system-ui, -apple-system, Segoe UI, sans-serif", fontWeight: 600 }));
    return out;
  }
  function render() { overlay.setProps({ layers: layers() }); dirty = true; }

  function getTooltip({ layer, object }) {
    if (!object || !layer) return null;
    if (layer.id === "elephants" || layer.id === "badges") {
      const e = object.e, h = headAt(e, app.time), w = winAt(e, app.time), T = TASK();
      const p = w ? predOf(w) : null;
      const txt = h && h.interp ? "Đang mất tín hiệu GPS" : p != null ? `Cây dự đoán: <b>${T.classes[p]}</b>` : "Chưa có dự đoán";
      return { html: `<div class="t-head">${e.id}</div><div class="t-row">${txt}</div>` };
    }
    if (layer.id === "waterholes") return { html: `<div class="t-head">${object.properties.name}</div><div class="t-row">Hố nước</div>` };
    return null;
  }
  function onClick({ layer, object }) { if (layer && (layer.id === "elephants" || layer.id === "badges") && object) select(object.e.id); }

  // ---------- Thanh thời gian ----------
  const slider = $("timeSlider");
  slider.min = tMin; slider.max = tMax; slider.value = app.time;
  function seasonAt(tm) { for (const e of ELE) { const i = bsearch(e.t, tm); if (i >= 0 && tm <= e.t[e.n - 1]) return e.wet[i]; } return null; }
  (function seasonBar() {
    const wet = css("--water-line"), dry = css("--surface-2"), stops = [];
    let prev = null;
    for (let tm = tMin; tm <= tMax; tm += 1440) {
      const w = seasonAt(tm);
      if (w == null || w === prev) continue;
      const pct = (((tm - tMin) / (tMax - tMin)) * 100).toFixed(2);
      if (prev != null) stops.push(`${prev ? wet : dry} ${pct}%`);
      stops.push(`${w ? wet : dry} ${pct}%`);
      prev = w;
    }
    stops.push(`${prev ? wet : dry} 100%`);
    $("seasonBar").style.background = `linear-gradient(90deg, ${stops.join(",")})`;
    $("seasonBar").title = "Xanh: mùa mưa (lịch quy ước)";
  })();
  function updateClock() {
    $("clockDate").textContent = fmtDate(app.time);
    const w = seasonAt(app.time);
    $("seasonChip").textContent = w == null ? "—" : w ? "Mùa mưa" : "Mùa khô";
    const h = localHour(app.time), day = h >= 6 && h < 18;
    $("dayChip").innerHTML = ico(day ? "sun" : "moon");
    $("dayChip").title = day ? "Ban ngày" : "Ban đêm";
    slider.value = app.time;
  }
  function setPlaying(p) { app.playing = p; if (!p) app.stopAt = null; $("playBtn").innerHTML = ico(p ? "pause" : "play"); if (p) hideHint(); }
  function setTime(tm) { app.time = Math.max(tMin, Math.min(tMax, tm)); render(); updateClock(); }
  $("playBtn").onclick = () => { if (app.time >= tMax) app.time = tMin; setPlaying(!app.playing); };
  $("speedBtn").onclick = () => { app.speed = (app.speed + 1) % SPEEDS.length; $("speedBtn").textContent = 2 ** app.speed + "×"; };
  slider.addEventListener("input", () => setTime(+slider.value));
  let last = performance.now(), lastUi = 0;
  function tick(now) {
    const dt = Math.min(100, now - last);
    last = now;
    if (app.playing) {
      app.time += (SPEEDS[app.speed] * dt) / 1000;
      if (app.time >= tMax) { app.time = tMax; setPlaying(false); }
      if (app.stopAt != null && app.time >= app.stopAt) { app.time = app.stopAt; app.stopAt = null; setPlaying(false); }
      render();
    }
    if (dirty && now - lastUi > 200) { lastUi = now; dirty = false; updateClock(); if (app.selected) renderCard(); }
    requestAnimationFrame(tick);
  }
  $("hintEle").innerHTML = elephantSvg("#ffffff", false);
  function hideHint() { $("hint").classList.add("gone"); }
  setTimeout(hideHint, 15000);

  // ---------- Chú giải ----------
  function renderLegend() {
    const T = TASK();
    const line = (op) => `<svg viewBox="0 0 22 14"><path d="M1 7h20" stroke="#fff" stroke-width="2.5" opacity="${op}"/></svg>`;
    const badge = (k) => `<span class="sym"><span class="cls-ico mini" style="color:${T.colors[k]}">${ICO[T.glyph[k]]}</span></span>`;
    const rule = app.leaf != null ? MODEL().rules.find((r) => r.leaf === app.leaf) : null;
    $("legend").innerHTML = `
      ${rule ? `<button class="btn clear-leaf" id="clearLeaf">${ico("close")}Đang xem luật: ${T.classes[rule.pred]}</button>` : ""}
      <div class="lg-title">Huy hiệu cạnh voi = cây dự đoán ${T.horizon}</div>
      <div class="items" style="grid-template-columns:1fr">
        ${[1, 0].map((k) => `<span class="it">${badge(k)}${T.classes[k]}</span>`).join("")}
        <span class="it"><span class="sym">${line(0.9)}</span>Đường đi thật 3 ngày qua</span>
        <span class="it"><span class="sym">${line(0.3)}</span>Mất GPS, nối thẳng</span>
      </div>`;
    const c = $("clearLeaf");
    if (c) c.onclick = () => setLeaf(null);
  }

  // ---------- Điều kiện luật → chip ----------
  function intervals(steps) {
    const b = {};
    for (const [f, op, thr] of steps) {
      const cur = b[f] || [null, null];
      if (op === "<=") cur[1] = cur[1] == null ? thr : Math.min(cur[1], thr);
      else cur[0] = cur[0] == null ? thr : Math.max(cur[0], thr);
      b[f] = cur;
    }
    return b;
  }
  const signed = (v) => (v > 0 ? "+" : "") + fmt(v, 1);
  function fval(f, v) {
    switch (f) {
      case "hour": return fmtHour(v);
      case "temp": return fmt(v, 1) + "°C";
      case "temp_change_90": case "temp_change_180": return signed(v) + "°C";
      case "dw_km": return v < 1 ? fmtInt(Math.round(v * 1000)) + " m" : fmt(v, 2) + " km";
      case "woody": case "woody_mean_300m": return fmt(v, 0) + "%";
      case "fix_age_min": return fmt(v, 0) + " phút";
      case "hours_since_water": return fmt(v, 1) + " giờ";
      default: return fmt(v, 2);
    }
  }
  const SHORT = { hour: "giờ", temp: "nhiệt độ", temp_change_90: "nhiệt 90' so với trước", temp_change_180: "nhiệt 3 giờ so với trước", dw_km: "cách nước",
                  woody: "cây gỗ", woody_mean_300m: "cây gỗ ~300 m", fix_age_min: "tuổi GPS", hours_since_water: "đã rời nước" };
  const FICO = { hour: "clock", temp: "thermo", temp_change_90: "thermo", temp_change_180: "thermo", dw_km: "drop", woody: "leaf",
                 woody_mean_300m: "leaf", fix_age_min: "signal", hours_since_water: "hourglass" };
  const chip = (icon, text, title) => `<span class="chip" title="${title || ""}">${icon}${text}</span>`;
  function chipsFor(steps) {
    return Object.entries(intervals(steps)).map(([f, [lo, hi]]) => {
      if (f === "wet") return chip(ico(lo != null ? "drop" : "sun"), lo != null ? "Mùa mưa" : "Mùa khô", LABEL[f]);
      if (f === "woody_missing") return chip(ico("leaf"), lo != null ? "thiếu dữ liệu cây gỗ" : "có dữ liệu cây gỗ", LABEL[f]);
      const txt = lo != null && hi != null ? `${fval(f, lo)}–${fval(f, hi)}` : hi != null ? `≤ ${fval(f, hi)}` : `> ${fval(f, lo)}`;
      return chip(ico(FICO[f] || "chart"), `${SHORT[f] || f} ${txt}`, LABEL[f]);
    }).join("");
  }
  // Điều kiện của luật viết thành chữ (dùng cho câu "Cây này nói gì?")
  function textFor(steps) {
    return Object.entries(intervals(steps)).map(([f, [lo, hi]]) => {
      if (f === "wet") return lo != null ? "mùa mưa" : "mùa khô";
      if (f === "woody_missing") return lo != null ? "thiếu dữ liệu cây gỗ" : "có dữ liệu cây gỗ";
      const name = SHORT[f] || f;
      if (f === "hour") return lo != null && hi != null ? `từ ${fval(f, lo)} đến ${fval(f, hi)}` : hi != null ? `trước ${fval(f, hi)}` : `sau ${fval(f, lo)}`;
      return lo != null && hi != null ? `${name} ${fval(f, lo)}–${fval(f, hi)}` : hi != null ? `${name} ≤ ${fval(f, hi)}` : `${name} > ${fval(f, lo)}`;
    }).join(", ");
  }
  // Pattern (hiện ở góc sơ đồ cây và trên thanh thuyết trình)
  // Luật (lá) làm nên pattern đang nêu: cây 1 là luật chỉ có giờ 00:45–03:45; các cây khác là luật ổn định mạnh nhất
  function patternRule() {
    const M = MODEL();
    if (app.task === "rest") {
      const r = M.rules.find((q) => {
        const iv = intervals(q.steps), ks = Object.keys(iv);
        return ks.length === 1 && ks[0] === "hour" && Math.abs(iv.hour[0] - 0.75) < 0.01 && Math.abs(iv.hour[1] - 3.75) < 0.01;
      });
      if (r) return r;
    }
    return M.rules.filter((x) => x.stable).sort((a, b) => b.lift_2009 * Math.sqrt(b.n) - a.lift_2009 * Math.sqrt(a.n))[0] || null;
  }
  function presentNote() {
    if (app.task === "rest") {
      return { main: "Từ 00:45 đến 03:45 (ban đêm), voi nghỉ (ít di chuyển).", hint: "Có thể hiểu: voi đang ngủ hoặc nghỉ ngơi." };
    }
    const T = TASK(), r = patternRule();
    if (!r) return { main: "", hint: "" };
    return { main: `${textFor(r.steps)} → ${T.classes[r.pred].toLowerCase()}.`, hint: `Có thể hiểu: ${HINT[app.task][r.pred]}.` };
  }
  function renderNote() {
    const n = presentNote();
    $("treeNote").classList.toggle("left", app.task === "water" || app.task === "speed");
    $("treeNote").innerHTML = `<div class="tn-title">Pattern</div><div class="tn-main">${n.main}</div><div class="tn-hint">${n.hint}</div>
      <div class="tn-path"><i></i>Nhánh tô vàng: đường từ gốc tới lá cho ra pattern</div>`;
  }
  // Mức chung của một nhãn = tỉ lệ của nhãn đó trong toàn bộ dữ liệu học (2007–2008)
  const baseShare = (k, task = app.task) => { const r = MODEL(task).nodes[0]; return r.counts[k] / r.n; };
  const pc0 = (v) => fmtPct(v, 0);
  // Gợi ý để người xem tự diễn giải; chỉ là giả thuyết, dữ liệu GPS không quan sát trực tiếp hành vi.
  const HINT = {
    rest: ["có thể là ngủ hoặc nghỉ ngơi", "có thể đang kiếm ăn hoặc đi tới nơi khác"],
    water: ["chưa tới lúc đi uống nước", "có thể đang đi uống nước"],
    speed: ["có thể đang kiếm ăn (đi chậm, dừng lại ăn)", "có thể đang đi tới nơi khác"],
    stay: ["có thể chỉ ghé qua rồi đi tiếp", "có thể đang uống nước, tắm hoặc nghỉ gần nước"],
  };
  const splitText = (f, thr, dir) => (f === "wet" ? (dir === "left" ? "mùa khô" : "mùa mưa")
    : f === "woody_missing" ? (dir === "left" ? "có dữ liệu" : "thiếu dữ liệu") : (dir === "left" ? "≤ " : "> ") + fval(f, thr));
  function pathSteps(leafId) {
    const parent = {}, nodes = MODEL().nodes;
    for (const n of nodes) if (!n.leaf) { parent[n.left] = [n.id, "<="]; parent[n.right] = [n.id, ">"]; }
    const steps = [];
    let cur = leafId;
    while (parent[cur]) { const [p, op] = parent[cur]; const n = nodes[p]; steps.unshift([n.feature, op, n.threshold]); cur = p; }
    return steps;
  }
  const f2 = (v) => (v == null ? "—" : fmt(v, 2));
  const liftLine = (r) => `${f2(r.lift_fit)} · ${f2(r.lift_val)} · ${f2(r.lift_2009)}`;   // chỉ dùng trong tooltip
  function evidence(r) {
    const T = TASK();
    return `<div class="rstats">
      <span><b>${pc0(r.conf)}</b> là "${T.classes[r.pred].toLowerCase()}" <span class="muted">(chung ${pc0(baseShare(r.pred))})</span></span>
      <span title="Số mẫu học (2007–2008) và số cá thể">${fmtInt(r.n)} mẫu · ${r.n_ids} voi</span>
      <span title="Số voi (có đủ mẫu) cho thấy cùng xu hướng">${r.ids_lift_gt1}/${r.ids_eval} voi cùng xu hướng</span>
      ${r.stable ? '<span class="ok-tag" title="Quy luật vẫn đúng ở tập kiểm tra (2008, 2009) và ở đa số voi">đáng tin</span>'
                 : '<span class="weak" title="Tỉ lệ gần mức chung hoặc không nhất quán giữa các voi">gần mức chung</span>'}</div>`;
  }
  function distBar(counts, T) {
    const tot = counts.reduce((a, b) => a + b, 0) || 1;
    return `<div class="dist4">${[1, 0].map((c) => `<span style="width:${(counts[c] / tot) * 100}%;background:${T.colors[c]}" title="${T.classes[c]}: ${fmtPct(counts[c] / tot)}"></span>`).join("")}</div>`;
  }

  // ---------- Thẻ con voi ----------
  function select(id, zoomTo) {
    app.selected = id;
    if (!app.visible.has(id)) { app.visible.add(id); visibilityChanged(); }
    hideHint();
    const h = headAt(BYID[id], app.time);
    const at = zoomTo || (h && [h.lon, h.lat]);
    if (at) map.easeTo({ center: at, zoom: Math.max(map.getZoom(), 12), duration: 800 });
    $("card").hidden = false;
    renderCard(); render();
    if (app.panel === "elephants") renderElephants();
  }
  function closeCard() { app.selected = null; app.follow = false; $("card").hidden = true; render(); if (app.panel === "elephants") renderElephants(); }
  function actualText(key, w) {
    const a = w[key].actual;
    if (a < 0) return "chưa xác định (thiếu GPS)";
    const m = fmtInt(w.apath);
    if (key === "rest") return a === 0 ? `Nghỉ (đi ${m} m)` : `Di chuyển (đi ${m} m)`;
    if (key === "water") return a === 1 ? `Về tới vùng nước${w.mtw >= 0 ? ` sau ~${fmtInt(w.mtw)} phút` : ""}` : "Chưa về nước trong 3 giờ";
    if (key === "speed") return `${a === 1 ? "Đi nhanh" : "Đi chậm"} (đi ${m} m, mốc ${fmtInt(Math.round(TK.speed_threshold_m))} m)`;
    return a === 1 ? `Ở lại vùng nước (đi ${m} m)` : `Rời đi (đi ${m} m)`;
  }
  const NA = {
    water: (w) => (w.dw <= BUF ? "Voi đang ở trong vùng nước (≤ 200 m): câu hỏi này chỉ áp dụng khi voi ở xa nước." : "Chưa có dự đoán cho câu hỏi này."),
    speed: () => "Câu hỏi này chỉ áp dụng ban ngày (06:00–18:00).",
    stay: () => "Voi đang ở xa nước: câu hỏi này chỉ áp dụng khi voi ở trong vùng nước (≤ 200 m).",
    rest: () => "Chưa có dự đoán cho câu hỏi này.",
  };
  function renderCard() {
    const e = BYID[app.selected], el = $("card"), T = TASK();
    const h = headAt(e, app.time), w = winAt(e, app.time);
    let body;
    if (!h) body = `<p class="note">Không có dữ liệu GPS lúc này.</p>`;
    else if (h.interp) body = `<p class="note">${ico("signal")} Đang mất tín hiệu GPS: voi được vẽ đi thẳng từ điểm cũ tới điểm mới, chưa có dự đoán.</p>`;
    else if (!w) body = `<p class="note">Chưa có dự đoán ở mốc này (cửa sổ thiếu GPS).</p>`;
    else {
      const r = w[app.task];
      if (r.pred < 0) {
        body = `<p class="note">${ico("drop")} ${NA[app.task](w)}</p>`;
      } else {
        const node = MODEL().nodes[r.leaf], rule = MODEL().rules.find((x) => x.leaf === r.leaf), ok = r.pred === r.actual;
        const facts = [
          chip(ico("clock"), fmtHour(localHour(w.t)), "Mốc dự báo"),
          chip(ico("thermo"), `${w.temp}°C`, "Nhiệt độ vòng cổ"),
          chip(ico("drop"), fval("dw_km", w.dw / 1000), "Cách nguồn nước gần nhất"),
          chip(ico("leaf"), w.woody == null ? "cây gỗ: thiếu" : `cây gỗ ${fmt(w.woody, 0)}%`, "Độ che phủ cây gỗ tại GPS"),
          w.hsw == null ? "" : chip(ico("hourglass"), `đã rời nước ${fmt(w.hsw, 1)} giờ`, "Thời gian ngoài vùng 200 m quanh nước"),
        ].join("");
        body = `
          <div class="dir-big"><span class="cls-big" style="color:${T.colors[r.pred]}">${ICO[T.glyph[r.pred]]}</span>
            <div class="txt"><b>${T.classes[r.pred]}</b><span>${T.question}</span>
            <span class="conf">trong luật này, ${fmtPct(r.conf)} mẫu học là "${T.classes[r.pred].toLowerCase()}"</span></div></div>
          ${distBar(node.counts, T)}
          <div class="actual ${ok ? "is-ok" : "is-miss"}">
            <span class="lab">Thực tế ${T.horizon}</span>
            <span class="val">${r.actual >= 0 ? clsIco(T, r.actual) : ""}<b>${actualText(app.task, w)}</b></span>
            <span class="verdict">${r.actual < 0 ? "" : ok ? "trùng dự đoán" : "khác dự đoán"}</span>
          </div>
          <div class="chips" style="margin-top:10px">${facts}</div>
          <div class="why"><div class="lab">Vì (luật của cây)</div><div class="chips">${chipsFor(pathSteps(r.leaf))}</div>${evidence(rule)}</div>`;
      }
    }
    el.innerHTML = `
      <div class="card-head">
        <span class="name"><span class="ele">${elephantSvg(css("--accent"), false)}</span>${e.id}</span>
        <button class="icon-btn ${app.follow ? "on" : ""}" id="followBtn" title="Bám theo">${ico("target")}</button>
        <button class="icon-btn" id="cardClose" title="Đóng">${ico("close")}</button>
      </div>${body}`;
    $("followBtn").onclick = () => { app.follow = !app.follow; renderCard(); render(); };
    $("cardClose").onclick = closeCard;
  }

  // ---------- Bảng phụ ----------
  document.querySelector(".top-right").addEventListener("click", (ev) => {
    const b = ev.target.closest("button");
    if (!b || !b.dataset.open) return;
    if (b.dataset.open === "tree") { openTree(); return; }
    openPanel(app.panel === b.dataset.open ? null : b.dataset.open);
  });
  $("drawerClose").onclick = () => openPanel(null);
  function openPanel(name) {
    app.panel = name;
    document.querySelectorAll(".top-right .tool").forEach((b) => b.classList.toggle("on", b.dataset.open === name));
    $("drawer").hidden = !name;
    $("drawerBody").scrollTop = 0;
    if (name === "elephants") renderElephants();
    if (name === "pattern") renderPattern();
    if (name === "rules") renderRules();
  }
  function setLeaf(id) {
    app.leaf = id == null || app.leaf === id ? null : id;
    buildLeaf(); renderLegend(); render();
    if (app.panel === "rules") renderRules();
    if (!$("treeModal").hidden) drawTree();
  }
  function setTask(key) {
    if (key === app.task) return;
    app.task = key;
    document.querySelectorAll("#taskSwitch button").forEach((x) => x.classList.toggle("on", x.dataset.task === key));
    app.leaf = null; buildLeaf(); renderLegend(); render();
    if (document.body.classList.contains("present")) { chk.sel = null; app.stopAt = null; renderCheck(); }
    if (app.selected) renderCard();
    if (app.panel) openPanel(app.panel);
    if (!$("treeModal").hidden) openTree();
  }
  $("taskSwitch").addEventListener("click", (ev) => { const b = ev.target.closest("button"); if (b) setTask(b.dataset.task); });

  // ---- Voi ----
  function updateToolCount() {
    const b = document.querySelector('.top-right .tool[data-open="elephants"] span');
    if (b) b.textContent = `Voi ${app.visible.size}/${ELE.length}`;
  }
  function visibilityChanged() {
    tripsAll = buildTrips(shown(), [255, 255, 255]);
    if (app.selected && !app.visible.has(app.selected)) closeCard();
    buildLeaf(); render(); updateToolCount();
  }
  function renderElephants() {
    $("drawerTitle").textContent = "Voi";
    $("drawerBody").innerHTML = `
      <div class="ele-tools"><button class="btn" id="eleAll">Hiện tất cả</button><button class="btn" id="eleNone">Ẩn tất cả</button></div>
      <div class="ele-list">${ELE.map((e) => `
        <label class="ele-row ${app.selected === e.id ? "sel" : ""}">
          <input type="checkbox" data-id="${e.id}" ${app.visible.has(e.id) ? "checked" : ""}>
          <span class="ele-ico">${elephantSvg(app.selected === e.id ? css("--accent") : "#ffffff", false)}</span>
          <span class="ele-name">${e.id}</span>
          <span class="muted ele-meta" title="Số ngày có dự đoán năm 2009">${Math.round(e.mv.t.length * STEP / 1440)} ngày</span>
          <button class="icon-btn" data-go="${e.id}" title="Tới con voi này">${ico("target")}</button>
        </label>`).join("")}</div>`;
    const body = $("drawerBody");
    body.querySelectorAll("input[data-id]").forEach((ck) => ck.addEventListener("change", () => {
      if (ck.checked) app.visible.add(ck.dataset.id); else app.visible.delete(ck.dataset.id);
      visibilityChanged();
    }));
    body.querySelectorAll("button[data-go]").forEach((b) => b.addEventListener("click", (ev) => {
      ev.preventDefault();
      const e = BYID[b.dataset.go];
      if (!winAt(e, app.time)) { const k = e.mv.t.findIndex((t) => t >= app.time); setTime(e.mv.t[k >= 0 ? k : 0] + 1); }
      select(e.id);
    }));
    $("eleAll").onclick = () => { ELE.forEach((e) => app.visible.add(e.id)); visibilityChanged(); renderElephants(); };
    $("eleNone").onclick = () => { app.visible.clear(); visibilityChanged(); renderElephants(); };
  }

  // ---- Pattern ----
  // Thanh ngang: mỗi hàng một nhóm, độ dài = tỉ lệ.
  function bars(rows, key, color, base) {
    const max = Math.max(...rows.map((r) => r[key] ?? 0), 0.01);
    return `<div class="hbars">${rows.map((r) => `<span class="hb-l">${r.group}</span>
      <div class="hb-t" title="${fmtInt(r.n)} mẫu"><i style="width:${((r[key] ?? 0) / max) * 100}%;background:${color}"></i>${base != null ? `<u style="left:${(base / max) * 100}%"></u>` : ""}</div>
      <span class="hb-v">${fmtPct(r[key] ?? 0)}</span>`).join("")}</div>`;
  }
  const pat = (t, r) => `<div class="pat-rule"><span class="muted">khi</span> ${chipsFor(r.steps)}<span class="pat-lift" title="Tỉ lệ trong nhánh so với mức chung. Lift fit · validation · 2009: ${liftLine(r)}">${pc0(r.conf)} <span class="muted">(chung ${pc0(baseShare(r.pred, t.key))})</span></span></div>`;
  function topRules(k, cls, n = 2) {
    const rs = MODEL(k).rules.filter((r) => r.stable && r.pred === cls).sort((a, b) => b.lift_2009 * Math.sqrt(b.n) - a.lift_2009 * Math.sqrt(a.n)).slice(0, n);
    return rs.length ? `<div class="pat"><div class="pat-head">${clsIco(TASKS[k], cls)}<b>${TASKS[k].classes[cls]}</b></div>${rs.map((r) => pat(TASKS[k], r)).join("")}</div>` : "";
  }
  function modelBlock(k) {
    const m = MODEL(k), b = m.metrics.baselines, T = TASKS[k];
    return `<div class="sec">Độ chính xác của cây</div>
      <table class="cmp"><thead><tr><th>macro-F1</th><th>Validation 2008</th><th>2009 (đối chiếu)</th></tr></thead><tbody>
        <tr><td>Cây (${m.metrics.leaves} luật)</td><td>${f2(m.metrics.val.macro_f1)}</td><td>${f2(m.metrics["2009"].macro_f1)}</td></tr>
        <tr><td>Luôn đoán lớp đông nhất</td><td>${f2(b.val.majority.macro_f1)}</td><td>${f2(b["2009"].majority.macro_f1)}</td></tr>
      </tbody></table>
      <details><summary>Bỏ từng nhóm feature</summary>
        <table class="cmp" style="margin-top:8px"><thead><tr><th>Bỏ nhóm</th><th>Validation</th><th>2009</th></tr></thead><tbody>
          <tr><td>Không bỏ</td><td>${f2(m.metrics.val.macro_f1)}</td><td>${f2(m.metrics["2009"].macro_f1)}</td></tr>
          ${m.metrics.ablation.map((a) => `<tr><td>${a.dropped}</td><td>${f2(a.val.macro_f1)}</td><td>${f2(a["2009"].macro_f1)}</td></tr>`).join("")}
        </tbody></table></details>`;
  }
  function renderPattern() { return { rest: renderPatternRest, water: renderPatternWater, speed: renderPatternSpeed, stay: renderPatternStay }[app.task](); }
  const headline = () => `<div class="headline"><button class="btn primary" id="momentBtn">${ICO.spark} Xem khoảnh khắc tiêu biểu</button></div>`;
  function bindHeadline() { const b = $("momentBtn"); if (b) b.onclick = signatureMoment; }
  function signatureMoment() {
    const r = MODEL().rules.filter((x) => x.stable).sort((a, b2) => b2.lift_2009 * Math.sqrt(b2.n) - a.lift_2009 * Math.sqrt(a.n))[0];
    if (!r) return;
    app.leaf = r.leaf; buildLeaf(); renderLegend(); showExample(r.leaf);
  }
  function renderPatternSpeed() {
    const T = TASKS.speed, S2 = EDA.speed;
    $("drawerTitle").textContent = "Voi đi nhanh hay chậm?";
    $("drawerBody").innerHTML = `
      ${headline()}
      <div class="glossary"><b>Chỉ xét ban ngày (06:00–18:00), khi voi đi.</b> <b>Đi nhanh</b> = đường đi 90 phút trên ${fmtInt(S2.threshold)} m
        (trung vị của dữ liệu học); <b>đi chậm</b> = dưới mức đó. Cây dự đoán tốc độ <i>nếu</i> voi đi.</div>
      <div class="sec">Cây gỗ ~300 m quanh voi</div>
      ${bars(S2.woody, "fast", T.colors[1], S2.fast)}
      <p class="note">Tỉ lệ đi nhanh theo độ che phủ cây gỗ (vạch trắng là mức chung ${fmtPct(S2.fast)}): cây gỗ rậm thì voi đi chậm hơn, khớp với paper.</p>
      <div class="sec">Mùa (lịch quy ước)</div>
      ${bars(S2.season, "fast", T.colors[1], S2.fast)}
      <div class="sec">Nhiệt độ vòng cổ (°C)</div>
      ${bars(S2.temp, "fast", T.colors[1], S2.fast)}
      <p class="note">Nhiệt độ liên quan yếu và đi cùng giờ trong ngày; trong các luật của cây, nhiệt độ chỉ xuất hiện ở vùng cây thưa mùa mưa.</p>
      <div class="sec">Giờ trong ngày</div>
      ${bars(S2.hour, "fast", T.colors[1], S2.fast)}
      ${modelBlock("speed")}`;
    bindHeadline();
  }
  function renderPatternStay() {
    const T = TASKS.stay, S2 = EDA.stay;
    $("drawerTitle").textContent = "Ở lại hay rời vùng nước?";
    $("drawerBody").innerHTML = `
      ${headline()}
      <div class="glossary"><b>Chỉ xét khi voi đang ở trong vùng 200 m quanh nguồn nước.</b> <b>Ở lại</b> = đi dưới ${TK.stay_m} m trong 90 phút tới.
        Dữ liệu GPS không phân biệt được uống nước, tắm hay nghỉ.</div>
      <div class="sec">Ở lại vào giờ nào?</div>
      ${bars(S2.hour, "stay", T.colors[1], S2.share)}
      <p class="note">Vạch trắng là mức chung ${fmtPct(S2.share)}. Ban đêm voi ở lại vùng nước nhiều, ban ngày hầu như chỉ ghé qua rồi đi.</p>
      <div class="sec">Ban đêm: cây gỗ quanh nguồn nước</div>
      ${bars(S2.woody_night, "stay", T.colors[1])}
      ${modelBlock("stay")}`;
    bindHeadline();
  }
  function renderPatternRest() {
    $("drawerTitle").textContent = "Voi nghỉ khi nào?";
    const T = TASKS.rest, P = EDA.rest_place;
    const rows = ["00:00–04:30", "04:30–06:00", "06:00–18:00", "18:00–24:00"].map((wn) => {
      const a = P.find((r) => r.place.startsWith("Xa") && r.when === wn), b = P.find((r) => r.place.startsWith("Ở") && r.when === wn);
      return `<tr><td>${wn}</td><td>${fmtPct(a.rest)}</td><td>${fmtPct(b.rest)}</td></tr>`;
    }).join("");
    $("drawerBody").innerHTML = `
      ${headline()}
      <div class="glossary"><b>Nghỉ</b> = voi đi dưới 75 m trong 90 phút (gần như đứng một chỗ). Chưa khẳng định là ngủ.
        <b>Di chuyển</b> = đi từ 75 m trở lên.</div>
      <div class="sec">1 · Nghỉ tập trung vào giờ nào?</div>
      <div id="chRest"></div>
      ${topRules("rest", 0, 2)}
      <div class="sec">2 · Nghỉ có gắn với việc ở gần nước không?</div>
      <table class="cmp"><thead><tr><th>Tỉ lệ nghỉ</th><th>Xa nước</th><th>Ở vùng nước</th></tr></thead><tbody>${rows}</tbody></table>
      <p class="note">Gần như nhau: voi nghỉ ban đêm dù đang ở cạnh nước hay đã đi xa.</p>
      <div class="sec">3 · Cây gỗ có liên quan không? (00:00–04:30)</div>
      ${bars(EDA.rest_woody_night, "rest", T.colors[0])}
      <p class="note">Cây gỗ càng rậm, ban đêm nghỉ càng nhiều. Đây là liên hệ trong dữ liệu, chưa phải nguyên nhân.</p>
      <div class="sec">4 · Nhiệt độ có liên quan không? (09:00–15:00)</div>
      ${bars(EDA.rest_temp_day, "rest", T.colors[0])}
      <p class="note">Ban ngày voi hầu như luôn di chuyển, nhiệt độ gần như không đổi điều đó.</p>
      <div class="sec">5 · Mỗi con voi nghỉ khác nhau</div>
      ${bars(EDA.rest_by_id_core, "rest", T.colors[0])}
      <p class="note">Tỉ lệ nghỉ trong khung 00:45–03:45 của từng voi: từ ${fmtPct(Math.min(...EDA.rest_by_id_core.map((r) => r.rest)))} đến ${fmtPct(Math.max(...EDA.rest_by_id_core.map((r) => r.rest)))}. Cây không dùng danh tính voi, nên khác biệt này chưa nằm trong luật.</p>
      ${modelBlock("rest")}`;
    bindHeadline();
    Viz.lineChart($("chRest"), { title: "Tỉ lệ nghỉ theo giờ (2007–2008)", height: 120, xTicks: [0, 6, 12, 18, 22.5], xFormat: (h) => fmtHour(h), yMin: 0,
      yFormat: (v) => v + "%", valueFormat: (q) => fmt(q.y, 0) + "%",
      series: [{ name: "Nghỉ", color: T.colors[0], pts: EDA.rest_by_hour.map((v, s) => ({ x: s * 1.5, y: v * 100 })) }] });
  }
  function renderPatternWater() {
    const T = TASKS.water, tr = EDA.trips, base = EDA.water_control.p;
    $("drawerTitle").textContent = "Khi nào voi quay lại nước?";
    $("drawerBody").innerHTML = `
      ${headline()}
      <div class="glossary"><b>Về nước</b> = voi đang ở xa nước (&gt; 200 m) và trong 3 giờ tới có điểm GPS nằm trong vùng 200 m quanh nguồn nước.
        Đây là xu hướng quay lại nước, chưa quan sát được voi có uống.</div>
      <div class="sec">1 · Voi hay về nước vào giờ nào?</div>
      <div id="chWater"></div>
      <p class="note">Chỉ xét voi cách nước 0,3–1,5 km để so sánh công bằng giữa các giờ.</p>
      ${topRules("water", 1, 2)}
      <div class="sec">2 · Khi nào voi "khát" hơn?</div>
      <p class="note">Cố định giờ (06:00–16:00) và khoảng cách (0,3–1,5 km), vạch trắng là mức chung ${fmtPct(base)}.</p>
      <b class="sub">Nhiệt độ vòng cổ (°C)</b>${bars(EDA.water_temp, "p", T.colors[1], base)}
      <b class="sub">Cây gỗ (%)</b>${bars(EDA.water_woody, "p", T.colors[1], base)}
      <b class="sub">Mùa (lịch quy ước)</b>${bars(EDA.water_season, "p", T.colors[1], base)}
      <p class="note">Trời càng nóng voi càng có xu hướng quay lại nước; vùng cây rậm thì ít hơn. Mùa mưa có nhiều nguồn nước hơn nên khó tách riêng.</p>
      <div class="sec">3 · Khoảng cách tới nước</div>
      ${bars(EDA.water_dist, "p", T.colors[1])}
      <p class="note">Càng gần càng dễ về: đây là yếu tố mạnh nhất nhưng hiển nhiên.</p>
      <div class="sec">4 · Một chuyến đi giữa hai lần ghé nước</div>
      <p class="note">${fmtInt(tr.n)} chuyến (2007–2008). Trung vị: kéo dài ${fmt(tr.duration_h.dry, 0)} giờ mùa khô và ${fmt(tr.duration_h.wet, 0)} giờ mùa mưa, đi ${fmt(tr.path_km.dry, 1)} / ${fmt(tr.path_km.wet, 1)} km, xa nước nhất ${fmt(tr.max_dw_km.dry, 1)} / ${fmt(tr.max_dw_km.wet, 1)} km.</p>
      <div id="chTrips"></div>
      ${modelBlock("water")}`;
    bindHeadline();
    Viz.lineChart($("chWater"), { title: "Xác suất về nước trong 3 giờ, theo giờ (2007–2008)", height: 120, xTicks: [0, 6, 12, 18, 22.5], xFormat: (h) => fmtHour(h), yMin: 0,
      yFormat: (v) => v + "%", valueFormat: (q) => fmt(q.y, 0) + "%",
      series: [{ name: "Về nước", color: T.colors[1], pts: EDA.water_by_hour.map((r, s) => ({ x: s * 1.5, y: r.p * 100 })) }] });
    const tot = (a) => a.reduce((x, y) => x + y, 0);
    Viz.lineChart($("chTrips"), { title: "Giờ rời nước và giờ về nước của các chuyến", height: 120, xTicks: [0, 6, 12, 18, 23], xFormat: (h) => fmtHour(h), yMin: 0,
      yFormat: (v) => v + "%", valueFormat: (q) => fmt(q.y, 1) + "% số chuyến",
      series: [{ name: "Rời nước", color: css("--m-local"), pts: tr.leave_hour.map((v, h) => ({ x: h, y: (v / tot(tr.leave_hour)) * 100 })) },
               { name: "Về nước", color: T.colors[1], pts: tr.return_hour.map((v, h) => ({ x: h, y: (v / tot(tr.return_hour)) * 100 })) }] });
  }

  // ---- Luật ----
  let rulesAll = false, exampleIdx = {};
  function showExample(leaf) {
    const uses = leafUses(leaf).filter((u) => u[app.task].pred >= 0);
    if (!uses.length) return;
    let k = uses.findIndex((u) => u.t > app.time + 1);
    if (k < 0) k = 0;
    exampleIdx[`${app.task}${leaf}`] = k;
    setPlaying(false);
    setTime(uses[k].t + 1);
    select(uses[k].e.id, [uses[k].lon, uses[k].lat]);
    renderRules();
  }
  function renderRules() {
    const M = MODEL(), T = TASK();
    const r0 = M.rules.filter((q) => q.stable).sort((a, b) => b.conf / baseShare(b.pred) - a.conf / baseShare(a.pred))[0] || M.rules[0];
    const ex = { pct: pc0(r0.conf), cls: `"${T.classes[r0.pred].toLowerCase()}"`, base: pc0(baseShare(r0.pred)) };
    $("drawerTitle").textContent = `Luật · ${T.name.replace("?", "")}`;
    const sorted = M.rules.slice().sort((a, b) => (b.stable - a.stable) || (b.lift * Math.sqrt(b.support) - a.lift * Math.sqrt(a.support)));
    const list = rulesAll ? sorted : sorted.slice(0, 10);
    $("drawerBody").innerHTML = `
      <div class="explain">
        <p><b>Mỗi luật là một nhánh của cây.</b> Khi mọi điều kiện (ô xám) cùng đúng, thẻ cho biết nhãn nào chiếm nhiều nhất trong nhánh đó, đại diện cho ${T.horizon}.</p>
        <p><b>Ví dụ đọc một thẻ:</b> "${ex.pct} là ${ex.cls} (chung ${ex.base})" nghĩa là trong dữ liệu 2007–2008, khi có điều kiện của thẻ thì ${ex.pct} số lần voi ở nhãn này, trong khi toàn bộ dữ liệu chỉ có ${ex.base}. Phần còn lại thuộc nhãn kia. Chênh càng lớn thì điều kiện càng liên quan tới nhãn.</p>
        <p><b>đáng tin</b> = quy luật vẫn đúng ở tập kiểm tra (2008, 2009) và ở đa số voi. <b>gần mức chung</b> = nhánh không khác gì mức chung, không nên rút ra điều gì.</p>
        <p><b>Bấm luật</b> → bản đồ hiện huy hiệu ở mọi chỗ luật được dùng năm 2009. <b>Xem ví dụ</b> → nhảy tới một lần cụ thể.</p>
      </div>
      ${list.map((r) => {
        const on = app.leaf === r.leaf, n = on ? leafUses(r.leaf).filter((u) => u[app.task].pred >= 0).length : 0;
        return `<div class="rule ${on ? "on" : ""} ${r.stable ? "" : "is-weak"}" data-leaf="${r.leaf}">
          <div class="then">${clsIco(T, r.pred)}<b>${T.classes[r.pred]}</b></div>
          <div class="chips">${chipsFor(r.steps)}</div>
          ${distBar(r.counts, T)}
          ${evidence(r)}
          ${on ? `<div class="ractions"><button class="btn primary" data-ex="${r.leaf}">Xem ví dụ ${ICO.next}</button>
            <span class="muted">${fmtInt(n)} lần năm 2009${exampleIdx[`${app.task}${r.leaf}`] != null ? ` · ví dụ ${exampleIdx[`${app.task}${r.leaf}`] + 1}/${fmtInt(n)}` : ""}</span></div>` : ""}
        </div>`;
      }).join("")}
      ${sorted.length > 10 ? `<button class="btn more" id="moreRules">${rulesAll ? "Thu gọn" : `Xem cả ${sorted.length} luật`}</button>` : ""}`;
    const body = $("drawerBody");
    body.querySelectorAll(".rule").forEach((el) => el.addEventListener("click", (ev) => { if (!ev.target.closest("[data-ex]")) setLeaf(+el.dataset.leaf); }));
    body.querySelectorAll("[data-ex]").forEach((b) => b.addEventListener("click", () => showExample(+b.dataset.ex)));
    const m = $("moreRules");
    if (m) m.onclick = () => { rulesAll = !rulesAll; renderRules(); };
  }

  // ---------- Sơ đồ cây ----------
  const leafStrong = (n) => !!(MODEL().rules.find((r) => r.leaf === n.id) || {}).stable;
  function drawTree() {
    const M = MODEL(), T = TASK(), hl = new Set();
    if (app.selected) {
      const w = winAt(BYID[app.selected], app.time);
      if (w && w[app.task].leaf >= 0) {
        const parent = {};
        for (const n of M.nodes) if (!n.leaf) { parent[n.left] = n.id; parent[n.right] = n.id; }
        let cur = w[app.task].leaf;
        hl.add(cur);
        while (parent[cur] != null) { cur = parent[cur]; hl.add(cur); }
      }
    }
    const pr = patternRule(), pset = new Set();
    if (pr) {
      const par = {};
      for (const n of M.nodes) if (!n.leaf) { par[n.left] = n.id; par[n.right] = n.id; }
      for (let cur = pr.leaf; cur != null; cur = par[cur]) pset.add(cur);
    }
    const lines = Object.fromEntries(Object.entries(LABEL).map(([k, v]) => [k, [SHORT[k] ? SHORT[k][0].toUpperCase() + SHORT[k].slice(1) : v]]));
    lines.wet = ["Mùa"]; lines.woody_missing = ["Dữ liệu cây gỗ"];
    renderNote();
    Viz.renderTree($("treeDiagram"), M, {
      large: true, highlight: hl, pattern: pset.size ? pset : null, selectedLeaf: app.leaf, onLeafClick: (id) => setLeaf(id),
      featureLines: lines, featureDescriptions: LABEL, splitText,
      leafColor: (n) => T.colors[n.pred],
      leafText: (n) => [T.classes[n.pred], leafStrong(n) ? `~ ${HINT[app.task][n.pred]}` : ""],
      nodeTip: (n) => `<div class="t-head">${n.leaf ? `Nhãn: ${T.classes[n.pred]}` : `${LABEL[n.feature]}: chia tại ${fval(n.feature, n.threshold)}`}</div>`,
    });
  }
  // Hai chế độ xem sơ đồ: "width" = vừa chiều ngang, cuộn dọc (chữ đọc được); "all" = toàn cảnh trong một màn hình
  let treeMode = "width";
  function applyTreeZoom() {
    const svg = $("treeDiagram").querySelector("svg");
    if (!svg) return;
    const vb = svg.viewBox.baseVal, holder = $("treeModalBody");
    svg.setAttribute("preserveAspectRatio", "xMidYMin meet");
    if (treeMode === "all") { svg.style.width = "100%"; svg.style.height = "100%"; }
    else {
      const w = holder.clientWidth - 4, scale = Math.min(w / vb.width, 1.5);
      svg.style.width = vb.width * scale + "px"; svg.style.height = vb.height * scale + "px";
    }
    $("treeZoom").textContent = treeMode === "width" ? "Xem toàn cảnh" : "Chữ lớn, cuộn dọc";
  }
  $("treeZoom").onclick = () => { treeMode = treeMode === "width" ? "all" : "width"; applyTreeZoom(); };
  window.addEventListener("resize", () => { if (!$("treeModal").hidden) applyTreeZoom(); });
  function openTree() {
    const M = MODEL();
    $("treeModalTitle").textContent = `${M.metrics.leaves} luật · học 2007–2008`;
    $("treeTabs").innerHTML = Object.values(TASKS).map((t) => `<button data-task="${t.key}" class="${t.key === app.task ? "on" : ""}">${t.name.replace("?", "")}</button>`).join("");
    $("treeTabs").querySelectorAll("button").forEach((b) => b.addEventListener("click", () => setTask(b.dataset.task)));
    $("treeModal").hidden = false;
    drawTree();
    applyTreeZoom();
  }
  $("treeModalClose").onclick = () => { $("treeModal").hidden = true; };
  $("treeModal").addEventListener("click", (ev) => { if (ev.target.id === "treeModal") $("treeModal").hidden = true; });

  document.addEventListener("keydown", (ev) => {
    if (ev.target.tagName === "INPUT" && ev.target.type !== "range") return;
    if (ev.code === "Space") { ev.preventDefault(); $("playBtn").click(); }
    if (ev.code === "ArrowRight" || ev.code === "ArrowLeft") {
      ev.preventDefault();
      setTime(app.time + (ev.shiftKey ? 1440 : STEP) * (ev.code === "ArrowRight" ? 1 : -1));
    }
    if (ev.code === "Escape") {
      if (!$("treeModal").hidden) $("treeModal").hidden = true;
      else if (app.panel) openPanel(null);
      else if (app.selected) closeCard();
    }
  });

  // ---------- Trình bày: chế độ thuyết trình, phím tắt, lưu trạng thái ----------
  // Phím P: kiểm tra pattern trên 2009. Một ô duy nhất: pattern, độ đúng chung, vài con voi tiêu biểu, một ví dụ.
  const chk = { sel: null, k: 0, cache: {} };
  function patternSpec() {
    if (app.task === "rest") return { cls: 0, test: (w) => { const h = localHour(w.t); return h > 0.75 && h <= 3.75; } };
    const r = MODEL().rules.filter((x) => x.stable).sort((a, b) => b.lift_2009 * Math.sqrt(b.n) - a.lift_2009 * Math.sqrt(a.n))[0];
    return r ? { cls: r.pred, test: (w) => w[app.task].leaf === r.leaf } : null;
  }
  // Toàn bộ cửa sổ 2009 có dự đoán, tách thành: thuộc pattern / mọi cửa sổ, theo từng voi
  function checkData() {
    if (chk.cache[app.task]) return chk.cache[app.task];
    const spec = patternSpec(), key = app.task;
    let all = 0, allCls = 0, hit = 0, n = 0;
    const by = {};
    for (const e of ELE) for (let k = 0; k < e.mv.t.length; k++) {
      if (e.mv[`pred_${key}`][k] < 0 || e.mv[`actual_${key}`][k] < 0) continue;
      all++; if (e.mv[`actual_${key}`][k] === spec.cls) allCls++;
      const w = winRow(e, k);
      if (!spec.test(w)) continue;
      n++;
      const b = (by[e.id] ||= { id: e.id, n: 0, cls: 0, rows: [] });
      b.n++; b.rows.push(w);
      if (w[key].actual === spec.cls) { b.cls++; hit++; }
    }
    const eles = Object.values(by).filter((b) => b.n >= 10).map((b) => Object.assign(b, { rate: b.cls / b.n })).sort((a, b) => b.rate - a.rate);
    const pick = eles.slice(0, 3);
    const worst = eles.length > 3 ? eles[eles.length - 1] : null;
    return (chk.cache[key] = { spec, base: allCls / all, rate: n ? hit / n : 0, n, by, pick, worst, nEle: eles.length });
  }
  // Mỗi ngày lấy một lần xảy ra pattern của con voi đã chọn
  function examplesOf(d, id) {
    const seen = new Set(), out = [];
    for (const w of d.by[id].rows.sort((a, b) => a.t - b.t)) {
      const day = Math.floor((w.t + OFF * 60) / 1440);
      if (!seen.has(day)) { seen.add(day); out.push(w); }
    }
    return out;
  }
  function showCheckExample(id, k) {
    const d = checkData(), ex = examplesOf(d, id);
    if (!ex.length) return;
    chk.sel = id; chk.k = ((k % ex.length) + ex.length) % ex.length;
    const w = ex[chk.k];
    setPlaying(false); app.stopAt = null;
    setTime(w.t + 1);
    select(id, [w.lon, w.lat]);
    renderCheck();
  }
  function renderCheck() {
    const T = TASK(), d = checkData(), nt = presentNote();
    const cls = T.classes[d.spec.cls].toLowerCase().replace(/\s*\(.*\)/, "");
    const row = (b, tag) => `<button class="ck-ele ${chk.sel === b.id ? "on" : ""}" data-ele="${b.id}">
      <span class="ele-ico">${elephantSvg(chk.sel === b.id ? css("--accent") : "#ffffff", false)}</span>
      <b>${b.id}</b>${tag ? `<span class="ck-tag">${tag}</span>` : ""}<span class="ck-rate">${pc0(b.rate)} <span class="muted">${cls}</span></span></button>`;
    let ex = "";
    if (chk.sel && d.by[chk.sel]) {
      const list = examplesOf(d, chk.sel), w = list[chk.k];
      const r = w && w[app.task], ok = r && r.actual === d.spec.cls;
      if (w) ex = `<div class="ck-ex ${ok ? "is-ok" : "is-miss"}">
        <div class="ck-when">${fmtDate(w.t)} <span class="muted">· ví dụ ${chk.k + 1}/${list.length}</span></div>
        <div class="ck-vs"><span>Dự đoán</span><b>${clsIco(T, d.spec.cls)}${T.classes[d.spec.cls]}</b></div>
        <div class="ck-vs"><span>Thực tế ${T.horizon}</span><b>${r.actual >= 0 ? clsIco(T, r.actual) : ""}${actualText(app.task, w)}</b></div>
        <div class="ck-btns"><button class="btn" id="ckPlay">${ico("play")} Chạy ${T.horizon}</button>
          <button class="btn primary" id="ckNext">Ví dụ khác ${ICO.next}</button></div></div>`;
    }
    $("check").innerHTML = `
      <div class="ck-title">Pattern <span class="muted">· kiểm tra trên năm 2009</span></div>
      <div class="ck-main">${nt.main}</div>
      <div class="ck-hint">${nt.hint}</div>
      <div class="ck-stat"><b>${pc0(d.rate)}</b> là "${cls}" <span class="muted">(chung ${pc0(d.base)})</span> · ${fmtInt(d.n)} lần · ${d.nEle} voi</div>
      <div class="ck-sec">Chọn một con voi để xem</div>
      <div class="ck-list">${d.pick.map((b) => row(b)).join("")}${d.worst ? row(d.worst, "ít rõ nhất") : ""}</div>
      ${ex || '<div class="ck-empty">Bấm một con voi: bản đồ sẽ nhảy tới một lần pattern xảy ra.</div>'}`;
    $("check").querySelectorAll("[data-ele]").forEach((b) => b.addEventListener("click", () => showCheckExample(b.dataset.ele, 0)));
    const nx = $("ckNext"); if (nx) nx.onclick = () => showCheckExample(chk.sel, chk.k + 1);
    const pl = $("ckPlay");
    if (pl) pl.onclick = () => { const w = examplesOf(d, chk.sel)[chk.k]; setTime(w.t + 1); app.stopAt = w.t + STEP; setPlaying(true); };
  }
  function setPresent(on) {
    document.body.classList.toggle("present", on);
    document.querySelector('[data-act="present"]').classList.toggle("on", on);
    $("check").hidden = !on;
    if (on) {
      openPanel(null); closeCard(); $("treeModal").hidden = true;
      chk.sel = null; renderCheck();
    } else app.stopAt = null;
    setTimeout(() => map.resize(), 50);
  }
  function toggleFullscreen() { document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen().catch(() => {}); }
  const KEYS = Object.keys(TASKS);
  document.querySelector(".top-right").addEventListener("click", (ev) => {
    const b = ev.target.closest("[data-act]");
    if (!b) return;
    if (b.dataset.act === "present") setPresent(!document.body.classList.contains("present"));
    if (b.dataset.act === "full") toggleFullscreen();
  });
  document.addEventListener("keydown", (ev) => {
    if (ev.target.tagName === "INPUT" && ev.target.type !== "range") return;
    const k = ev.key.toLowerCase();
    const idx = KEYS.findIndex((q) => TASKS[q].hotkey === ev.key);
    if (idx >= 0) setTask(KEYS[idx]);
    else if (k === "p") setPresent(!document.body.classList.contains("present"));
    else if (k === "f") toggleFullscreen();
    else if (k === "h") document.body.classList.toggle("hide-ui");
    else if (k === "]" || k === "pagedown") setTask(KEYS[(KEYS.indexOf(app.task) + 1) % KEYS.length]);
    else if (k === "[" || k === "pageup") setTask(KEYS[(KEYS.indexOf(app.task) + KEYS.length - 1) % KEYS.length]);
  });
  // đường dẫn lưu trạng thái: #task=water&ele=AM99&t=123456
  function writeHash() {
    const q = new URLSearchParams({ task: app.task, t: Math.round(app.time) });
    if (app.selected) q.set("ele", app.selected);
    history.replaceState(null, "", "#" + q.toString());
  }
  setInterval(writeHash, 1500);
  (function readHash() {
    const q = new URLSearchParams(location.hash.slice(1));
    if (q.get("task") && TASKS[q.get("task")]) setTask(q.get("task"));
    if (q.get("t") && Number.isFinite(+q.get("t"))) setTime(+q.get("t"));
    if (q.get("ele") && BYID[q.get("ele")]) setTimeout(() => select(q.get("ele")), 300);
  })();

  $("brandIco").innerHTML = elephantSvg("#ffffff", false);
  $("loadIco").innerHTML = elephantSvg("#ffffff", false);
  fillIcons();
  setPlaying(false);
  updateToolCount();
  renderLegend();
  updateClock();
  render();
  $("loading").classList.add("done");
  requestAnimationFrame(tick);
  Object.assign(window, { __app: app, __ELE: ELE, __setTime: setTime, __select: select, __map: map });
})();
