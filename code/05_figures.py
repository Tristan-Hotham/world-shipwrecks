"""Header card, blog figures (release/blog/b_*.png) and paper figures (release/paper/f_*.png)."""
from matplotlib.patches import Patch, Rectangle
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe
from figstyle import *

R = jload(f"{DATA}/results.json")
D = wrecks()
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PA, exist_ok=True)
T = R["timeline"]


def both(fig, name):
    fig.savefig(os.path.join(PA, "f_" + name + ".png"), dpi=200, facecolor=fig.get_facecolor())
    fig.savefig(os.path.join(BL, "b_" + name + ".png"), dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def era_legend(fig, y=.02, ncol=4, fs=10):
    H = [Line2D([], [], ls="", marker="o", ms=7, mfc=ECOL[i], mec="none", label=ERAS[i][0]) for i in range(len(ERAS) - 1)]
    H.append(Line2D([], [], ls="", marker="o", ms=4, mfc="#A9A398", mec="none", label="Not dated"))
    fig.legend(handles=H, loc="lower center", bbox_to_anchor=(.5, y), ncol=ncol, frameon=False, fontsize=fs, handletextpad=.3, columnspacing=1.2)


# 1. world map by era, with the British Isles
fig = plt.figure(figsize=(13, 8.2), facecolor=BG)
ax = fig.add_axes([0, .33, .70, .6]); outline(ax, fc=SEA, ec="#C9CDD0"); world(ax, lw=.25)
era_dots(ax, D, s_und=1, s_dat=6)
ax.text(.01, 1.0, f"{R['source']['n']:,} wrecks with a place; coloured dots have a year of loss", transform=ax.transAxes, fontproperties=DISPB, fontsize=15, color=FG, va="bottom")
ab = fig.add_axes([.715, .13, .275, .76]); ext = bi_ext(lat1=61.8)
ab.add_patch(Rectangle((ext[0], ext[2]), ext[1] - ext[0], ext[3] - ext[2], fc=SEA, ec="#C9CDD0", zorder=0))
world_hi(ab, tr=BI, ext=ext, lw=.3, clip=(-15, 45, 8, 65))
bi = D[D.lon.between(-12, 3) & D.lat.between(49, 62)]
era_dots(ab, bi, tr=BI, s_und=.6, s_dat=4)
ab.text(0, 1.085, "British Isles", transform=ab.transAxes, fontproperties=DISPB, fontsize=15, color=FG, va="bottom", zorder=9)
ab.text(0, 1.008, f"Scotland {R['coverage']['scotland']:,} · Wales {R['coverage']['wales']:,}\nEngland {R['coverage']['england']:,} · N. Ireland {R['coverage']['ni']:,}", transform=ab.transAxes, fontsize=9.5, color=MUT, va="bottom", zorder=9, linespacing=1.4)
a2 = fig.add_axes([.05, .11, .62, .17]); a2.set_facecolor(BG)
dd = [d for d in T["decades"]]
a2.bar([d["dec"] for d in dd], [d["n"] for d in dd], width=8.5, color=[ECOL[era_of(d["dec"] + 5)] if d["dec"] not in (1910, 1940) else ECOL[3 if d["dec"] == 1910 else 5] for d in dd])
spines(a2); a2.set_title("Mapped wrecks with a year, per decade", fontsize=11, loc="left", color=FG)
era_legend(fig, y=.0, ncol=4, fs=9.5)
both(fig, "maps")

 
LS = R["lists"]
KC = [i for i in range(len(CAUSES)) if i != 6]
# 2. Wikipedia lists: wrecks per year, by cause
def list_years(ax, mode="cause", share=False, legend=True, fs=9.5):
    Yr = np.array(LS["years"] if mode == "cause" else LS["years_flag"])
    cats = [(CAUSES[i][0], CAUSES[i][1], i) for i in KC] if mode == "cause" else [(f[0], f[1], i) for i, f in enumerate(FLAGC)]
    x = Yr[:, 0]; tot = Yr[:, 1:].sum(axis=1); bot = np.zeros(len(Yr))
    for nm, col, i in cats:
        v = Yr[:, i + 1] / np.maximum(tot, 1) if share else Yr[:, i + 1]
        ax.bar(x, v, bottom=bot, width=1.0, color=col, lw=0, label=nm); bot += v
    for a, b in ((1914, 1918), (1939, 1945)):
        ax.axvspan(a - .5, b + .5, color=HOT, alpha=.08, lw=0, zorder=0)
    ax.set_xlim(1699, 2026); spines(ax)
    if legend: ax.legend(frameon=False, fontsize=fs, loc="upper left", ncol=2 if mode == "cause" else 2)
    return bot.max()


fig, ax = plt.subplots(figsize=(12, 5), facecolor=BG); ax.set_facecolor(BG)
mx = list_years(ax)
ax.set_ylim(0, mx * 1.12); ax.set_ylabel("wrecks listed per year")
ax.text(1912, mx * 1.05, "First World War", color=HOT, fontsize=10, ha="right"); ax.text(1947, mx * 1.05, "Second World War", color=HOT, fontsize=10, ha="left")
ax.annotate(f"{LS['peak_year']}: {LS['peak_n']:,}", (LS["peak_year"], LS["peak_n"]), xytext=(1960, LS["peak_n"] * .80), fontsize=10, arrowprops=dict(arrowstyle="-", color=MUT, lw=.7))
ax.annotate(f"{LS['peak19_year']}: {LS['peak19_n']:,}", (LS["peak19_year"], LS["peak19_n"]), xytext=(1886, LS["peak19_n"] * 1.06), fontsize=10, arrowprops=dict(arrowstyle="-", color=MUT, lw=.7))
fig.tight_layout(); both(fig, "years")

# 3. Wikipedia lists: share by flag per decade
fig, ax = plt.subplots(figsize=(12, 4.6), facecolor=BG); ax.set_facecolor(BG)
Yf = np.array(LS["years_flag"]); dec = (Yf[:, 0] // 10) * 10
decs = np.array([d for d in np.unique(dec) if Yf[dec == d, 1:].sum() >= 300])   # decades with at least 300 listed wrecks
M = np.array([Yf[dec == d, 1:].sum(axis=0) for d in decs]); M = M / np.maximum(M.sum(axis=1, keepdims=True), 1)
bot = np.zeros(len(decs))
for i, (nm, col) in enumerate(FLAGC):
    ax.bar(decs, M[:, i], bottom=bot, width=9, color=col, label=nm, lw=0); bot += M[:, i]
ax.set_xlim(decs.min() - 6, 2030); ax.set_ylim(0, 1); ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}")); spines(ax)
ax.set_ylabel("share of listed wrecks"); ax.legend(frameon=False, fontsize=9, loc="center left", bbox_to_anchor=(1.0, .5))
fig.tight_layout(); both(fig, "flags")

# 4. ancient and medieval wrecks per century
fig, ax = plt.subplots(figsize=(11, 4), facecolor=BG); ax.set_facecolor(BG)
C = [c for c in R["ancient"]["cent"] if c["i"] >= 7]
ax.bar([c["i"] for c in C], [c["n"] for c in C], width=.85, color=["#9C5B2E" if 13 <= c["i"] <= 18 else "#C7A27A" for c in C])
ax.set_xticks([c["i"] for c in C if c["i"] % 2 == 1]); ax.set_xticklabels([c["label"].replace("AD 1st century", "AD 1st c.").replace("1st century BC", "1st c. BC") for c in C if c["i"] % 2 == 1], rotation=40, ha="right", fontsize=9)
ax.text(15.6, R["ancient"]["peak_n"] * .97, f"{R['ancient']['peak_label']}: about {R['ancient']['peak_n']:.0f}", fontsize=10)
ax.set_ylabel("wrecks (spread over date range)"); spines(ax); fig.tight_layout(); both(fig, "ancient")

# 5. the record: sources, and where the wrecks lie
fig, axs = plt.subplots(2, 1, figsize=(11, 5.2), facecolor=BG, gridspec_kw={"hspace": 1.1})
B = R["source"]["by_source"]
for ax, (title, vals, cats, cols) in zip(axs, [
        ("Where the record comes from", [b["n"] for b in B], [b["name"] for b in B], SCOL),
        ("Where the wrecks lie (nearest land)", [R["coverage"][k] for k in ("scotland", "wales", "england", "ni", "us", "rest")],
         ["Scotland", "Wales", "England", "Northern Ireland", "United States", "Rest of the world"], ["#2F7FB8", "#5E8C4A", "#B3202A", "#7A4E9C", "#C9A227", "#4F6D7A"])]):
    ax.set_facecolor(BG); x = 0; tot = sum(vals)
    for v, c, nm in zip(vals, cols, cats):
        ax.barh(0, v, left=x, color=c, height=.8)
        if v / tot > .06: ax.text(x + v / 2, 0, f"{100 * v / tot:.0f}%", ha="center", va="center", color="#fff", fontsize=10, fontweight="medium")
        x += v
    fig.subplots_adjust(bottom=.16, top=.92)
    ax.set_xlim(0, tot); ax.axis("off"); ax.set_title(title, loc="left", fontsize=11.5, color=FG)
    ax.legend(handles=[Patch(fc=c, label=n) for c, n in zip(cols, cats)], loc="upper center", bbox_to_anchor=(.5, -.05), ncol=3 if len(cats) == 6 else 2, frameon=False, fontsize=9)
both(fig, "record")

# 6. graveyards
G = R["graveyards"]
fig, ax = plt.subplots(figsize=(11, 7), facecolor=BG); ax.set_facecolor(BG)
ys = np.arange(len(G))[::-1]
sc = {s[0]: s[1] for s in SOURCES}
ax.barh(ys, [g["n"] for g in G], color=[sc.get(g["main_source"], "#B9B3A6") for g in G], height=.72)
for yv, g in zip(ys, G):
    ax.text(g["n"] + 25, yv, f"{g['n']:,}", va="center", fontsize=9.5)
ax.set_yticks(ys); ax.set_yticklabels([g["name"] for g in G], fontsize=10); spines(ax); ax.set_xlabel("wrecks in the record")
ax.legend(handles=[Patch(fc=c, label=n) for n, c in SOURCES], frameon=False, fontsize=9, loc="lower right", title="mostly from", title_fontsize=9)
fig.tight_layout(); both(fig, "graveyards")

# 7. causes (lists) and vessel types (map)
fig, axs = plt.subplots(1, 2, figsize=(12.5, 4.3), facecolor=BG)
C0 = [dict(LS["causes"][i], col=CAUSES[i][1]) for i in KC]
T0 = [dict(R["types"]["list"][i], col=TCOL[i], pct=R["types"]["list"][i]["pct_known"]) for i in range(len(TYPES) - 1)]
for ax, L0, title in ((axs[0], C0, f"Cause, Wikipedia lists ({LS['dated']:,} wrecks)"), (axs[1], T0, f"Vessel, mapped wrecks ({R['types']['known']:,} with a type)")):
    ax.set_facecolor(BG); o = sorted(range(len(L0)), key=lambda i: L0[i]["n"])
    ax.barh(range(len(o)), [L0[i]["n"] for i in o], color=[L0[i]["col"] for i in o], height=.7)
    ax.set_yticks(range(len(o))); ax.set_yticklabels([L0[i]["name"].replace(": torpedo, mine, aircraft or gunfire", "") for i in o], fontsize=9.5)
    for k, i in enumerate(o): ax.text(L0[i]["n"], k, f" {L0[i]['pct']:.0f}%", va="center", fontsize=9)
    spines(ax); ax.set_title(title, loc="left", fontsize=11.5, color=FG); ax.set_xlim(0, max(l["n"] for l in L0) * 1.18)
    ax.xaxis.set_major_locator(plt.MaxNLocator(4)); ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
fig.tight_layout(); both(fig, "causes")

# header card 1200 x 630
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
ax = fig.add_axes([.43, .13, .54, .74]); ax.set_facecolor(BG)
mx = list_years(ax, legend=False); ax.set_ylim(0, mx * 1.1); ax.tick_params(labelsize=10)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.text(1916, mx * 1.03, "WWI", color=HOT, fontsize=11, ha="right"); ax.text(1937, mx * 1.03, "WWII", color=HOT, fontsize=11, ha="right")
ax.set_title("Wrecks listed per year, by cause", loc="left", fontsize=11, color=MUT)
fig.text(.04, .86, "Shipwrecks", fontproperties=DISP, fontsize=52, color=FG, va="top")
fig.text(.04, .72, "of the world", fontproperties=DISP, fontsize=40, color=HOT, va="top")
fig.text(.04, .56, f"{LS['n']:,} wrecks listed\non Wikipedia since 1700.\nWorst year: {LS['peak_year']},\nwith {LS['peak_n']:,}.", fontproperties=SERP, fontsize=17, color=FG, va="top", linespacing=1.45)
fig.text(.04, .08, "Dr Tristan Hotham · maps.tristanhotham.com", fontsize=11, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
plt.close(fig)
print("figures done")
