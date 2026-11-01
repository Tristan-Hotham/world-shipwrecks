"""r/dataisbeautiful collage for world-shipwrecks: 2400 x 3000 px, light background. Numbers from data/results.json.
Every map label is checked geometrically: its box must not touch land or any wreck dot (it fails loudly otherwise)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figstyle import *
import matplotlib.patheffects as pe
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
from shapely.geometry import Polygon as SPoly, box as sbox
from shapely.ops import unary_union

R = jload(f"{DATA}/results.json")
D = wrecks()
T, CV, GY = R["timeline"], R["coverage"], R["gy"]
from matplotlib import font_manager as fm
BGc = "#F7F5F0"; SEAc = "#E8EFF3"; LANDc = "#E3DED2"
HALO = [pe.withStroke(linewidth=4, foreground=SEAc)]
CHECK = []      # (axes, text, transformer) checked after drawing
TARGET = []     # wanted lon, lat of each label; the label is moved to the nearest spot that passes the checks


def land_union(tr, clip=None, min_km2=0):
    ps = []
    for iso, ring in SHAPES:
        if clip and (ring[:, 0].max() < clip[0] or ring[:, 0].min() > clip[2] or ring[:, 1].max() < clip[1] or ring[:, 1].min() > clip[3]):
            continue
        x, y = tr.transform(np.clip(ring[:, 0], -179.9, 179.9), np.clip(ring[:, 1], -89.5, 89.5))
        p = SPoly(np.column_stack([x, y]))
        if not p.is_valid: p = p.buffer(0)
        if p.area >= min_km2 * 1e6: ps.append(p)
    return unary_union(ps)


ANCHOR = []    # feature point for a leader line (None for none)


def label(ax, lon, lat, txt, tr=EE, ha="center", fs=10.5, weight="medium", color=FG, anchor=None):
    X, Y = proj(lon, lat, tr)
    t = ax.text(X, Y, txt, ha=ha, va="center", fontsize=fs, color=color, family=MONO, linespacing=1.3, zorder=8, path_effects=HALO, fontweight=weight)
    CHECK.append((ax, t, tr))
    TARGET.append((lon, lat)); ANCHOR.append(anchor)
    return t


LS = R["lists"]
KC = [i for i in range(len(CAUSES)) if i != 6]
fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BGc)
fig.text(.045, .985, "Shipwrecks of the world", fontproperties=DISP, fontsize=48, color=FG, va="top")
fig.text(.045, .932, f"{LS['n']:,} shipwrecks listed on Wikipedia, year by year, 1700 to 2025. The world wars stand out: three of the five\n"
         f"worst years are war years. The 1800s plateau is partly the sources: British newspapers, above all Lloyd's List.",
         fontproperties=SERP, fontsize=13.2, color=FG, va="top", linespacing=1.45)

# ---- key panel: the timeline
fig.text(.045, .866, "Shipwrecks listed per year, by cause", fontproperties=DISPB, fontsize=18, color=FG, va="bottom")
tx = fig.add_axes([.075, .615, .9, .24]); tx.set_facecolor(BGc)
Yr = np.array(LS["years"]); tot = Yr[:, 1:].sum(axis=1); bot = np.zeros(len(Yr))
for i in KC:
    tx.bar(Yr[:, 0], Yr[:, i + 1], bottom=bot, width=1.0, color=CAUSES[i][1], lw=0); bot += Yr[:, i + 1]
for a_, b_ in ((1914, 1918), (1939, 1945)):
    tx.axvspan(a_ - .5, b_ + .5, color=HOT, alpha=.08, lw=0, zorder=0)
tx.set_xlim(1699, 2026); tx.set_ylim(0, LS["peak_n"] * 1.38); spines(tx); tx.tick_params(labelsize=10)
tx.set_xticks(range(1700, 2030, 25)); tx.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
ANN = []
def ann(txt, xy, xyt, ha="left", **kw):
    t = tx.annotate(txt, xy, xytext=xyt, fontsize=10, ha=ha, va="center", color=kw.get("color", FG), linespacing=1.3,
                    arrowprops=dict(arrowstyle="-", color=MUT, lw=.7) if xy else None, zorder=9)
    ANN.append(t); return t
ann(f"First World War:\n{LS['ww1_avg']:,.0f} a year;\n{LS['y1917']:,} in 1917", (1917, LS["y1917"]), (1921, LS["peak_n"] * 1.22), color=HOT)
ann(f"Second World War\n{LS['ww2_avg']:,.0f} a year; {LS['peak_n']:,}\nin {LS['peak_year']}, the worst year", (LS["peak_year"], LS["peak_n"]), (1956, LS["peak_n"] * .72), color=HOT)
ann(f"Age of sail and Lloyd's List:\n{LS['high19_avg']:,.0f} a year 1850 to 1879,\n{LS['uk_c19_pct']:.0f}% of 1800s wrecks British", (1830, 2300), (1703, LS["peak_n"] * .5))
ann(f"fewer\nsources:\n{LS['dip_avg']:,.0f} a\nyear,\n1890 to\n1913", (1902, 450), (1902, 1100), ha="center")
ann(f"since 1966:\n{LS['modern_avg']:,.0f} a year", (1990, 220), (1992, 600), ha="center")
H = [Rectangle((0, 0), 1, 1, fc=CAUSES[i][1]) for i in KC]
LEG = SERP.copy(); LEG.set_size(11.5)
fig.legend(H, [CAUSES[i][0] for i in KC], loc="upper left", bbox_to_anchor=(.035, .603), ncol=4, frameon=False, prop=LEG, handletextpad=.4, columnspacing=1.2, handlelength=1.2)

# ---- numbers row
nums = [(f"{LS['war_years_in_top5']} of 5", HOT, f"worst years are war\nyears: {LS['top'][0]['y']}, {LS['top'][1]['y']}, {LS['top'][2]['y']}"),
        (f"{LS['ww2_vs_inter']:.0f}×", "#B3202A", "as many a year in 1939 to\n1945 as between the wars"),
        (f"{LS['war_ww2_pct']:.0f}%", "#3B3B3B", "of 1939 to 1945 losses were\nto torpedoes, aircraft, mines"),
        (f"{LS['c19_aground_pct']:.0f}%", "#C9A227", "of 1800s wrecks ran\naground or were driven ashore")]
for i, (big, col, sm) in enumerate(nums):
    xx = .045 + i * .238
    fig.text(xx, .552, big, fontproperties=DISP, fontsize=32, color=col, va="top")
    fig.text(xx, .515, sm, family=MONO, fontsize=10, color=FG, va="top", linespacing=1.4)

# ---- flags by decade
fig.text(.045, .452, "Whose ships: share of listed wrecks by flag, per decade", fontproperties=DISPB, fontsize=18, color=FG, va="bottom")
fx = fig.add_axes([.075, .305, .6, .138]); fx.set_facecolor(BGc)
Yf = np.array(LS["years_flag"]); dec = (Yf[:, 0] // 10) * 10
decs = np.array([d for d in np.unique(dec) if Yf[dec == d, 1:].sum() >= 300])
M = np.array([Yf[dec == d, 1:].sum(axis=0) for d in decs]); M = M / M.sum(axis=1, keepdims=True)
b0 = np.zeros(len(decs))
for i, (nm, col) in enumerate(FLAGC):
    fx.bar(decs, M[:, i], bottom=b0, width=9, color=col, lw=0); b0 += M[:, i]
fx.set_xlim(decs.min() - 6, 2026); fx.set_ylim(0, 1); spines(fx); fx.tick_params(labelsize=10)
fx.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
fig.legend([Rectangle((0, 0), 1, 1, fc=c) for _, c in FLAGC], [n for n, _ in FLAGC], loc="upper left", bbox_to_anchor=(.69, .445), ncol=2, frameon=False,
           prop=fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf", size=10.5), handlelength=1.1, columnspacing=1, handletextpad=.4, labelspacing=.45)
fig.text(.045, .281, f"Decades with at least 300 listed wrecks. British ships are {LS['uk_c19_pct']:.0f}% of the 1800s and {LS['uk_ww2_pct']:.0f}% of 1939 to 1945.", family=MONO, fontsize=10, color=MUT, va="top")

# ---- world map of wrecks with a place
ax = fig.add_axes([.03, .1, .58, .145])
outline(ax, fc=SEAc, ec="#C9CDD0", lw=.8); world(ax, lw=.3, land=LANDc, ec=BGc)
era_dots(ax, D, s_und=.8, s_dat=3.2, edge=BGc)
LW = land_union(EE, min_km2=10000)
fig.text(.045, .254, f"{R['source']['n']:,} wrecks with a place, coloured by era (grey: no year)", fontproperties=DISPB, fontsize=14, color=FG, va="bottom")
EH = [Line2D([], [], ls="", marker="o", ms=6, mfc=ECOL[i], mec="none", label=ERAS[i][0]) for i in range(len(ERAS) - 1)]
EH.append(Line2D([], [], ls="", marker="o", ms=4, mfc="#A9A398", mec="none", label="Year not recorded"))
fig.legend(handles=EH, loc="upper left", bbox_to_anchor=(.035, .097), ncol=4, frameon=False, fontsize=8.6, handletextpad=.2, columnspacing=1.0, labelspacing=.3)

# ---- British Isles panel
ab = fig.add_axes([.64, .06, .34, .155]); lo0, la0, lo1, la1 = -11.6, 49.4, 3.2, 61.9
ext = bi_ext(lo0, la0, lo1, la1)
ab.add_patch(Rectangle((ext[0], ext[2]), ext[1] - ext[0], ext[3] - ext[2], fc=SEAc, ec="#C9CDD0", lw=.8, zorder=0))
world_hi(ab, tr=BI, ext=ext, lw=.35, land=LANDc, ec=BGc, clip=(-16, 44, 9, 66))
bi = D[D.lon.between(-13, 4) & D.lat.between(48.5, 63)]
era_dots(ab, bi, tr=BI, s_und=.35, s_dat=2.2, edge=BGc)
LB = unary_union([p if p.is_valid else p.buffer(0) for p in (SPoly(np.column_stack(BI.transform(r[:, 0], r[:, 1]))) for r in hi_rings((-16, 44, 9, 66)))])
fig.text(.645, .254, "British Isles", fontproperties=DISPB, fontsize=14, color=FG, va="bottom")
fig.text(.645, .25, f"Scotland {CV['scotland']:,} · Wales {CV['wales']:,}\nEngland {CV['england']:,} · N. Ireland {CV['ni']:,}", family=MONO, fontsize=9, color=MUT, va="top", linespacing=1.35)

fig.text(.045, .006, "Sources: Wikipedia contributors, Lists of shipwrecks (CC BY-SA); Wikidata (CC0), incl. Canmore and Coflein records; NOAA Office of Coast Survey,\n"
         "AWOIS (public domain); Natural Earth. Counts are wrecks recorded in these lists, not all wrecks. Duplicates removed.\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib  ·  maps.tristanhotham.com/world-shipwrecks", family=MONO, fontsize=8.4, color=MUT, linespacing=1.5, va="bottom")

# ---- place every map label on the nearest open sea, then check it against land, wreck dots and other labels
fig.canvas.draw()
rend = fig.canvas.get_renderer()
PTS = {}


def problems(axx, t, tr, placed, tol=0):
    bb = t.get_window_extent(rend).expanded(1.02, 1.04)
    inv = axx.transData.inverted()
    (x0, y0), (x1, y1) = inv.transform([[bb.x0, bb.y0], [bb.x1, bb.y1]])
    land = LW if axx is ax else LB
    out = []
    if land.intersects(sbox(x0, y0, x1, y1)): out.append("land")
    if id(axx) not in PTS:
        pts = D if axx is ax else bi
        px, py = proj(pts.lon, pts.lat, tr); PTS[id(axx)] = axx.transData.transform(np.column_stack([px, py]))
    q = PTS[id(axx)]
    n = int(((q[:, 0] > bb.x0 - 3) & (q[:, 0] < bb.x1 + 3) & (q[:, 1] > bb.y0 - 3) & (q[:, 1] < bb.y1 + 3)).sum())
    if n > tol: out.append(f"covers {n} wrecks")
    axb = axx.get_window_extent(rend)
    if not (axb.x0 + 4 <= bb.x0 and bb.x1 <= axb.x1 - 4 and axb.y0 + 4 <= bb.y0 and bb.y1 <= axb.y1 - 4): out.append("outside panel")
    if any(bb.overlaps(o) for o in placed): out.append("overlaps a label")
    return out


placed = []
TOL = {}
for (axx, t, tr), (lon, lat) in zip(CHECK, TARGET):
    big = axx is ax
    st = 1.0 if big else .1
    cand = sorted(((dx, dy) for dx in np.arange(-60, 60.1, st) for dy in np.arange(-30, 30.1, st)) if big else
                  ((dx, dy) for dx in np.arange(-6, 6.01, st) for dy in np.arange(-3, 3.01, st)), key=lambda d: d[0] ** 2 + (2 * d[1]) ** 2)
    ok = False
    for tol in (0, 3):      # first look for a spot touching no wreck at all; else allow up to 3 isolated dots (never a cluster)
        for dx, dy in cand:
            if not (-180 < lon + dx < 180 and -80 < lat + dy < 85): continue
            t.set_position(proj(lon + dx, lat + dy, tr))
            if not problems(axx, t, tr, placed, tol):
                ok = True; break
        if ok: break
    if not ok:
        raise SystemExit("no open spot for " + t.get_text())
    TOL[id(t)] = tol
    placed.append(t.get_window_extent(rend).expanded(1.02, 1.04))
    print(f"{t.get_text().splitlines()[0]:28s} moved {dx:+.1f} lon, {dy:+.1f} lat")
LEAD = []
for (axx, t, tr), a in zip(CHECK, ANCHOR):
    if a is None: continue
    bb = t.get_window_extent(rend); ax_, ay_ = axx.transData.transform(np.column_stack(proj([a[0]], [a[1]], tr)))[0]
    if bb.x0 - 4 <= ax_ <= bb.x1 + 4 and bb.y0 - 4 <= ay_ <= bb.y1 + 4: continue      # label sits on its feature
    ex_ = min(max(ax_, bb.x0), bb.x1); ey_ = min(max(ay_, bb.y0), bb.y1)                  # nearest point of the label box
    inv = axx.transData.inverted(); (p0, p1) = inv.transform([[ax_, ay_], [ex_, ey_]])
    axx.plot([p0[0], p1[0]], [p0[1], p1[1]], color=FG, lw=.7, zorder=7, solid_capstyle="round")
    axx.scatter([p0[0]], [p0[1]], s=6, color=FG, zorder=7)
    LEAD.append(((ax_, ay_), (ex_, ey_), t))
BAD = []
for axx, t, tr in CHECK:
    bb = t.get_window_extent(rend).expanded(1.02, 1.04)
    inv = axx.transData.inverted()
    (x0, y0), (x1, y1) = inv.transform([[bb.x0, bb.y0], [bb.x1, bb.y1]])
    land = LW if axx is ax else LB
    if land.intersects(sbox(x0, y0, x1, y1)): BAD.append(("label on land", t.get_text()))
    pts = D if axx is ax else bi
    px, py = proj(pts.lon, pts.lat, tr)
    q = axx.transData.transform(np.column_stack([px, py]))
    inside = (q[:, 0] > bb.x0 - 3) & (q[:, 0] < bb.x1 + 3) & (q[:, 1] > bb.y0 - 3) & (q[:, 1] < bb.y1 + 3)
    if inside.sum() > TOL.get(id(t), 0): BAD.append(("label covers wrecks", t.get_text(), int(inside.sum())))
    print(f"check {t.get_text().splitlines()[0]:24s} covers {int(inside.sum())} isolated dots")
    axb = axx.get_window_extent(rend)
    if not (axb.x0 <= bb.x0 and bb.x1 <= axb.x1 and axb.y0 <= bb.y0 and bb.y1 <= axb.y1): BAD.append(("label outside panel", t.get_text()))
lat_ = np.linspace(-90, 90, 181)
xl, yl = EE.transform(np.full_like(lat_, -180), lat_); xr, yr = EE.transform(np.full_like(lat_, 180), lat_[::-1])
GLOBE = SPoly(np.column_stack([np.r_[xl, xr], np.r_[yl, yr]]))
for t in []:
    bb = t.get_window_extent(rend); (x0, y0), (x1, y1) = ax.transData.inverted().transform([[bb.x0, bb.y0], [bb.x1, bb.y1]])
    if GLOBE.intersects(sbox(x0, y0, x1, y1)): BAD.append(("corner label touches the globe", t.get_text()))
# raise each timeline annotation until it clears the bars beneath it (it stays inside the panel or the check fails)
import matplotlib.text as mtext
TBB = lambda t: (t.update_positions(rend), mtext.Text.get_window_extent(t, rend))[1]      # the text box only, not the leader line


def clear_of_bars(t):
    bb = TBB(t).expanded(1.02, 1.08)
    (x0, y0), (x1, y1) = tx.transData.inverted().transform([[bb.x0, bb.y0], [bb.x1, bb.y1]])
    under = (Yr[:, 0] >= np.floor(x0) - 1) & (Yr[:, 0] <= np.ceil(x1) + 1)
    return (not under.any()) or tot[under].max() < y0
for t in ANN:
    k = 0
    while not clear_of_bars(t) and k < 200:
        x, y = t.xyann; t.xyann = (x, y + LS["peak_n"] * .01); k += 1
# timeline annotations must sit on paper above the bars and inside the panel
for t in ANN:
    bb = TBB(t).expanded(1.02, 1.08)
    (x0, y0), (x1, y1) = tx.transData.inverted().transform([[bb.x0, bb.y0], [bb.x1, bb.y1]])
    under = (Yr[:, 0] >= np.floor(x0) - 1) & (Yr[:, 0] <= np.ceil(x1) + 1)
    if under.any() and tot[under].max() >= y0: BAD.append(("annotation over bars", t.get_text(), int(tot[under].max()), int(y0)))
    axb = tx.get_window_extent(rend)
    if not (axb.x0 <= bb.x0 and bb.x1 <= axb.x1 and bb.y1 <= axb.y1): BAD.append(("annotation outside panel", t.get_text()))
for i in range(len(ANN)):
    for j in range(i + 1, len(ANN)):
        if TBB(ANN[i]).overlaps(TBB(ANN[j])): BAD.append(("annotations overlap", ANN[i].get_text(), ANN[j].get_text()))
# an annotation's leader line must not cross another annotation
from shapely.geometry import LineString
for t in ANN:
    if t.xy is None or t.arrow_patch is None: continue
    p0 = tx.transData.transform(t.xy); p1 = tx.transData.transform(t.xyann)
    ln = LineString([p0, p1])
    for u in ANN:
        if u is t: continue
        b = TBB(u)
        if ln.intersects(sbox(b.x0, b.y0, b.x1, b.y1)): BAD.append(("leader crosses an annotation", t.get_text(), u.get_text()))
# leader lines must not cross another label
from shapely.geometry import LineString
for (a0, a1, t0) in LEAD:
    ln = LineString([a0, a1])
    for _, t, _ in CHECK:
        if t is t0: continue
        b = t.get_window_extent(rend)
        if ln.intersects(sbox(b.x0, b.y0, b.x1, b.y1)): BAD.append(("leader crosses a label", t0.get_text(), t.get_text()))
# labels must not overlap each other
boxes = [t.get_window_extent(rend) for _, t, _ in CHECK]
for i in range(len(boxes)):
    for j in range(i + 1, len(boxes)):
        if boxes[i].overlaps(boxes[j]): BAD.append(("labels overlap", CHECK[i][1].get_text(), CHECK[j][1].get_text()))
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shipwrecks_of_the_world.png")
if BAD:
    fig.savefig(os.path.join(WORK, "collage_failed.png"), facecolor=BGc, dpi=100)
    raise SystemExit("label check failed: " + repr(BAD))
fig.savefig(out, facecolor=BGc, dpi=200)
print("ok", out, len(CHECK), "labels checked")
