"""House style for static figures: fonts (static instances cut from the variable Fraunces in /home/claude/ref/fonts,
written to WORK), the palette, Natural Earth outlines in Equal Earth, and a British Isles projection."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
import numpy as np
import pandas as pd
from pyproj import Transformer
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERB = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#636A72", "axes.labelcolor": "#1D2128",
                     "xtick.color": "#636A72", "ytick.color": "#636A72"})
BG, FG, MUT, LAND, RULE, SEA = "#F6F4EF", "#1D2128", "#636A72", "#E2DED3", "#DDD8CC", "#E9EFF2"
HOT, COOL = "#B3202A", "#2F7FB8"
ECOL = [e[1] for e in ERAS]; SCOL = [s[1] for s in SOURCES]; CCOL = [c[1] for c in CAUSES]; TCOL = [t[1] for t in TYPES]

EE = Transformer.from_crs(4326, 8857, always_xy=True)
BI = Transformer.from_crs(4326, "+proj=laea +lat_0=55 +lon_0=-4 +datum=WGS84", always_xy=True)
W = jload(f"{DATA}/world.json")


def rings(geom):
    cs = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in cs:
        yield np.array(poly[0])


SHAPES = []
for f in W["features"]:
    for ring in rings(f["geometry"]):
        SHAPES.append((f["properties"]["iso"], ring))
WORLD_EXT = (-17.0e6, 17.0e6, -8.75e6, 8.7e6)


def world(ax, tr=EE, lw=.3, ext=WORLD_EXT, ec="#FFFFFF", land=LAND, z=1, clip=None):
    for iso, ring in SHAPES:
        if clip and (ring[:, 0].max() < clip[0] or ring[:, 0].min() > clip[2] or ring[:, 1].max() < clip[1] or ring[:, 1].min() > clip[3]):
            continue
        x, y = tr.transform(np.clip(ring[:, 0], -179.9, 179.9), np.clip(ring[:, 1], -89.5, 89.5))
        ax.add_patch(MPoly(np.column_stack([x, y]), closed=True, fc=land, ec=ec, lw=lw, zorder=z))
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")


def outline(ax, fc=None, lw=.8, ec=MUT, z=0):
    lat = np.linspace(-90, 90, 181)
    xl, yl = EE.transform(np.full_like(lat, -180), lat); xr, yr = EE.transform(np.full_like(lat, 180), lat[::-1])
    ax.add_patch(MPoly(np.column_stack([np.r_[xl, xr], np.r_[yl, yr]]), closed=True, fc=fc or "none", ec=ec, lw=lw, zorder=z))


def proj(lon, lat, tr=EE):
    return tr.transform(np.asarray(lon, dtype=float), np.asarray(lat, dtype=float))


def wrecks():
    return pd.read_csv(f"{DATA}/wrecks.csv", low_memory=False, dtype={"country_or_flag": str, "flag_group": str, "uk_nation": str})


def spines(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def era_dots(ax, D, tr=EE, s_und=1.2, s_dat=5, und_col="#A9A398", alpha=.85, z=3, edge="#ffffff"):
    u = D[D.year.isna()]
    x, y = proj(u.lon, u.lat, tr); ax.scatter(x, y, s=s_und, c=und_col, lw=0, alpha=.55, zorder=z)
    d = D[D.year.notna()].sort_values("year")
    x, y = proj(d.lon, d.lat, tr)
    ax.scatter(x, y, s=s_dat, c=[ECOL[e] for e in d.era], lw=.25, edgecolor=edge, alpha=alpha, zorder=z + 1)


def bi_ext(lon0=-11.2, lat0=49.6, lon1=2.2, lat1=61.2):
    xs, ys = proj([lon0, lon1, lon0, lon1, -4], [lat0, lat0, lat1, lat1, lat0], BI)
    return (min(xs), max(xs), min(ys), max(ys))


_HI = None


def hi_rings(clip):
    """Natural Earth 1:10m country rings that touch a lon/lat box (for close-up maps)."""
    global _HI
    if _HI is None:
        G = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")
        _HI = [np.array(r[0]) for f in G["features"] for r in (f["geometry"]["coordinates"] if f["geometry"]["type"] == "MultiPolygon" else [f["geometry"]["coordinates"]])]
    return [r for r in _HI if not (r[:, 0].max() < clip[0] or r[:, 0].min() > clip[2] or r[:, 1].max() < clip[1] or r[:, 1].min() > clip[3])]


def world_hi(ax, tr, ext, clip, lw=.3, ec="#FFFFFF", land=LAND, z=1):
    for ring in hi_rings(clip):
        x, y = tr.transform(ring[:, 0], ring[:, 1])
        ax.add_patch(MPoly(np.column_stack([x, y]), closed=True, fc=land, ec=ec, lw=lw, zorder=z))
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")
