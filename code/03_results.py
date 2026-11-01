"""All numbers: data/results.json (every number quoted anywhere), data tables (decades.csv, years.csv, graveyards.csv,
causes.csv, flags.csv), and page data (points.json, site.json). Ancient wrecks (DARMC/OXREP geodatabase) enter only
as counts per century."""
import numpy as np
import pandas as pd
from common import *

D = pd.read_csv(f"{DATA}/wrecks.csv", low_memory=False, dtype={"country_or_flag": str, "flag_group": str, "uk_nation": str})
CL = jload(f"{WORK}/clean.json")
CT = jload(f"{WORK}/countries.json")
N = len(D)
pc = lambda a, b: round(100 * a / b, 2) if b else 0.0
dated = D[D.year.notna()].copy(); dated["year"] = dated.year.astype(int)
R = {"meta": {"doi": DOI, "blog": BLOG, "page": PAGE, "repo": REPO, "retrieved": RETRIEVED}}

# ---------- sources and coverage ----------
src_n = D.source.value_counts().sort_index()
R["source"] = {"n": N, "wd_items": CL["wd_items"], "wd_no_point": CL["wd_no_point"],
               "wd_not_ships": CL.get("wd_aircraft_dropped", 0) + CL.get("wd_not_vessel_dropped", 0),
               "wd_mapped": CL["wd_mapped"], "awois_rows": CL["awois_rows"], "awois_rocks": CL["awois_rocks_dropped"],
               "awois_dups": CL["awois_duplicates_dropped"], "awois_kept": CL["awois_kept"],
               "by_source": [{"name": SOURCES[i][0], "n": int(src_n.get(i, 0)), "pct": pc(src_n.get(i, 0), N),
                              "dated": int(dated.source.eq(i).sum()), "dated_pct": pc(dated.source.eq(i).sum(), src_n.get(i, 0))} for i in range(5)]}
R["source"]["wd_scot_wales"] = int(src_n[0] + src_n[1])
R["source"]["wd_scot_wales_pct"] = pc(src_n[0] + src_n[1], CL["wd_mapped"])
R["source"]["wd_other"] = int(src_n[2])
assert R["source"]["wd_mapped"] == src_n[0] + src_n[1] + src_n[2] and src_n[3] == CL["awois_kept"] and src_n[4] == CL["lists_points_kept"]
R["source"]["lists_points"] = int(src_n[4]); R["source"]["lists_points_dup"] = CL["lists_points_dup"]; R["source"]["lists_points_gave_year"] = CL["lists_points_gave_year"]
R["source"]["extra_items_with_dates"] = CL["extra_items_with_dates"]
assert CL["wd_items"] == CL["wd_mapped"] + CL["wd_no_point"] + R["source"]["wd_not_ships"]

meth = dated.year_method.str.replace(r"^AWOIS duplicate: .*", "AWOIS (record matched to a Wikidata item)", regex=True).value_counts()
uk = D[D.near_iso == "GBR"]; nat = uk.uk_nation.value_counts()
cont = D.near_continent.replace({"Seven seas (open ocean)": "Open ocean"}).value_counts()
R["coverage"] = {"dated": len(dated), "dated_pct": pc(len(dated), N), "undated": N - len(dated),
                 "methods": [{"m": k, "n": int(v)} for k, v in meth.items()],
                 "uk": len(uk), "uk_pct": pc(len(uk), N),
                 "scotland": int(nat.get("Scotland", 0)), "scotland_pct": pc(nat.get("Scotland", 0), N),
                 "wales": int(nat.get("Wales", 0)), "wales_pct": pc(nat.get("Wales", 0), N),
                 "england": int(nat.get("England", 0)), "england_pct": pc(nat.get("England", 0), N),
                 "ni": int(nat.get("Northern Ireland", 0)),
                 "us": int((D.near_iso == "USA").sum()), "us_pct": pc((D.near_iso == "USA").sum(), N),
                 "continents": {k: {"n": int(v), "pct": pc(v, N)} for k, v in cont.items()},
                 "rest": int(N - len(uk) - (D.near_iso == "USA").sum()), "rest_pct": pc(N - len(uk) - (D.near_iso == "USA").sum(), N),
                 "canmore_unknown": int(meth.get("label: unknown vessel lost in a year (Canmore)", 0)),
                 "notable": int((D.sitelinks > 0).sum()), "notable_dated": int((dated.sitelinks > 0).sum()),
                 "notable_dated_pct": pc((dated.sitelinks > 0).sum(), (D.sitelinks > 0).sum())}
R["coverage"]["europe_na_pct"] = pc(cont.get("Europe", 0) + cont.get("North America", 0), N)
R["coverage"]["outside_europe_na"] = int(N - cont.get("Europe", 0) - cont.get("North America", 0))
R["coverage"]["england_per_scotland"] = round(nat.get("Scotland", 0) / max(1, nat.get("England", 0)), 1)

# ---------- timeline ----------
Y0 = 1700
yrs = list(range(Y0, 2027))
ytab = pd.crosstab(dated.year, dated.source).reindex(index=yrs, columns=range(5), fill_value=0)
ytab.index.name = "year"; ytab.columns = ["canmore", "coflein", "wikidata_other", "awois", "wikipedia_points"]
ytab["all"] = ytab.sum(axis=1)
ytab.to_csv(f"{WORK}/map_years.csv")
dec = dated[dated.year >= Y0].assign(dec=lambda x: x.year // 10 * 10)
dtab = pd.crosstab(dec.dec, dec.source).reindex(index=range(Y0, 2030, 10), columns=range(5), fill_value=0)
dtab.columns = ["canmore", "coflein", "wikidata_other", "awois", "wikipedia_points"]; dtab["all"] = dtab.sum(axis=1); dtab.index.name = "decade"
dtab.to_csv(f"{WORK}/map_decades.csv")
ww1 = dated.year.between(1914, 1918); ww2 = dated.year.between(1939, 1945)
inter = dated.year.between(1919, 1938); post = dated.year.between(1946, 1965)
peak = ytab["all"].idxmax()
T = {"decades": [{"dec": int(d0), "n": int(dtab.loc[d0, "all"])} for d0 in dtab.index],
     "peak_year": int(peak), "peak_n": int(ytab.loc[peak, "all"]),
     "ww1": int(ww1.sum()), "ww1_pct": pc(ww1.sum(), len(dated)), "ww2": int(ww2.sum()), "ww2_pct": pc(ww2.sum(), len(dated)),
     "ww1_per_year": round(ww1.sum() / 5, 1), "ww2_per_year": round(ww2.sum() / 7, 1),
     "inter_per_year": round(inter.sum() / 20, 1), "post_per_year": round(post.sum() / 20, 1),
     "y1942": int(ytab.loc[1942, "all"]), "y1942_awois": int(ytab.loc[1942, "awois"]),
     "y1917": int(ytab.loc[1917, "all"]), "y1918": int(ytab.loc[1918, "all"]),
     "pre1700": int((dated.year < 1700).sum()),
     "sail": int(dated[(dated.source == 0) & dated.year.between(1700, 1879)].shape[0]),
     "canmore_dated": int(dated.source.eq(0).sum())}
T["ww2_vs_inter"] = round(T["ww2_per_year"] / T["inter_per_year"], 1)
T["sail_pct_canmore"] = pc(T["sail"], T["canmore_dated"])
cd = dtab["canmore"]; T["canmore_peak_dec"] = int(cd.idxmax()); T["canmore_peak_n"] = int(cd.max())
cy = ytab["canmore"]; T["canmore_peak_year"] = int(cy.idxmax()); T["canmore_peak_year_n"] = int(cy.max())
aw = dated[dated.source == 3]
T["awois_dated"] = len(aw); T["awois_ww2"] = int(aw.year.between(1939, 1945).sum()); T["awois_ww2_pct"] = pc(T["awois_ww2"], len(aw))
T["awois_1942_war"] = int(((aw.year == 1942) & (aw.cause == 0)).sum())
T["awois_war_ww1"] = int(((aw.year.between(1917, 1918)) & (aw.cause == 0)).sum())
wo = dated[dated.source == 2]
T["wdo_dated"] = len(wo); T["wdo_ww2"] = int(wo.year.between(1939, 1945).sum()); T["wdo_ww2_pct"] = pc(T["wdo_ww2"], len(wo))
T["wdo_ww1"] = int(wo.year.between(1914, 1918).sum())
dd = dtab["all"]; T["top_decade"] = int(dd.idxmax()); T["top_decade_n"] = int(dd.max())
R["timeline"] = T
cen = dated.assign(c=lambda x: np.floor(x.year / 100).astype(int)).c.value_counts().sort_index()
R["centuries"] = [{"c": int(c), "n": int(v)} for c, v in cen.items()]

# ---------- ancient wrecks, aggregated only ----------
an = pd.read_csv(f"{GH}/austinw8_ancient_shipwrecks/geodatabase_shipwrecks.csv", encoding="latin1", low_memory=False)
s = pd.to_numeric(an.Start_Date, errors="coerce"); e = pd.to_numeric(an.End_Date, errors="coerce")
s = s.where(s.notna() & e.notna(), pd.to_numeric(an.OXREP_Earliest_Date, errors="coerce"))
e = e.where(e.notna(), pd.to_numeric(an.OXREP_Latest_Date, errors="coerce"))
ok = s.notna() & e.notna() & (e >= s) & ((e - s) <= 300)
cent = np.zeros(30)   # centuries 1500 BC (index 0 = -1500..-1401) to AD 1400s
for a, b in zip(s[ok], e[ok]):
    span = np.arange(int(a), int(b) + 1); span = span[span != 0]
    for c in np.floor((span + 1500) / 100).astype(int):
        if 0 <= c < 30: cent[c] += 1 / len(span)
lab = lambda i: ("1st century BC" if i == 14 else f"{15 - i}00s BC") if i < 15 else ("AD 1st century" if i == 15 else f"AD {i - 15}00s")
pk = int(np.argmax(cent))
R["ancient"] = {"n_rows": len(an), "n_used": int(ok.sum()), "cent": [{"i": i, "label": lab(i), "n": round(float(cent[i]), 1)} for i in range(30)],
                "peak_label": lab(pk), "peak_n": round(float(cent[pk]), 0),
                "peak2_n": round(float(sorted(cent)[-2]), 0),
                "roman_share": pc(cent[13:17].sum(), cent.sum()),
                "ad1000s": round(float(cent[25]), 0)}
assert R["ancient"]["peak_label"] in ("1st century BC", "AD 1st century")

# ---------- causes and types ----------
cc = D.cause.value_counts().reindex(range(len(CAUSES)), fill_value=0)
known = int(cc[:-1].sum())
R["causes"] = {"known": known, "known_pct": pc(known, N),
               "list": [{"name": CAUSES[i][0], "n": int(cc[i]), "pct_known": pc(cc[i], known) if i < len(CAUSES) - 1 else None} for i in range(len(CAUSES))],
               "war_pct_known": pc(cc[0], known), "weather_ground_pct_known": pc(cc[1] + cc[2], known),
               "awois_known": int((D[D.source == 3].cause < len(CAUSES) - 1).sum()), "wd_known": int((D[D.source < 3].cause < len(CAUSES) - 1).sum())}
ck = dated[dated.cause < len(CAUSES) - 1]
R["causes"]["war_in_ww2_pct"] = pc(((ck.cause == 0) & ck.year.between(1939, 1945)).sum(), (ck.cause == 0).sum())
pd.DataFrame([{"cause": CAUSES[i][0], "wrecks": int(cc[i]), "noaa_awois": int((D[D.source == 3].cause == i).sum()),
               "wikidata": int((D[D.source < 3].cause == i).sum())} for i in range(len(CAUSES))]).to_csv(f"{DATA}/causes.csv", index=False)
tt = D.type.value_counts().reindex(range(len(TYPES)), fill_value=0)
tk = int(tt[:-1].sum())
R["types"] = {"known": tk, "known_pct": pc(tk, N), "list": [{"name": TYPES[i][0], "n": int(tt[i]), "pct_known": pc(tt[i], tk) if i < len(TYPES) - 1 else None} for i in range(len(TYPES))]}

# ---------- flags (only the "other" Wikidata wrecks: for the Scottish and Welsh imports the country is the location) ----------
fo = D[(D.source == 2) & D.flag_group.notna() & (D.flag_group != "")]
fg = fo.flag_group.value_counts()
R["flags"] = {"n_with": len(fo), "n_other": int(src_n[2]), "pct_with": pc(len(fo), src_n[2]),
              "list": [{"name": k, "n": int(v), "pct": pc(v, len(fo)),
                        "ww2": int(fo[(fo.flag_group == k) & fo.year.between(1939, 1945)].shape[0])} for k, v in fg.head(15).items()]}
fg.rename_axis("flag_group").reset_index(name="wrecks").to_csv(f"{DATA}/flags.csv", index=False)
fm = D[D.source.isin([2, 4]) & D.flag_group.notna() & (D.flag_group != "")].flag_group.value_counts()
FLAGS = [k for k in fm.index[:12]] + ["Other", "Not recorded"]

# ---------- graveyards ----------
GY = [("Firth of Clyde", [-5.5, 55.2, -4.5, 56.1], "Scotland"), ("Firth of Forth", [-3.8, 55.95, -2.0, 56.35], "Scotland"),
      ("Orkney and Scapa Flow", [-3.5, 58.65, -2.3, 59.45], "Scotland"), ("Aberdeen coast", [-2.3, 56.9, -1.7, 57.75], "Scotland"),
      ("Shetland", [-2.3, 59.8, -0.6, 60.95], "Scotland"), ("Gulf of Mexico, US coast", [-98, 25.5, -80.5, 31], "United States"),
      ("Pembrokeshire and Milford Haven", [-5.8, 51.55, -4.8, 52.1], "Wales"), ("Anglesey and Holyhead", [-4.8, 53.1, -4.0, 53.45], "Wales"),
      ("Moray Firth", [-4.3, 57.45, -2.6, 57.85], "Scotland"), ("Approaches to New York", [-74.3, 39.8, -72.8, 40.7], "United States"),
      ("Great Lakes", [-92.5, 41.3, -75.8, 49.1], "United States and Canada"), ("Chesapeake Bay", [-77.5, 36.8, -75.8, 39.6], "United States"),
      ("Cape Hatteras and the Outer Banks", [-76.5, 34.3, -74.8, 36.6], "United States"), ("English Channel", [-6, 48.5, 2, 51.2], "England and France"),
      ("Florida Keys", [-82.2, 24.3, -80.2, 25.3], "United States"), ("Baltic Sea", [12.8, 53.5, 30.5, 66], "Northern Europe"),
      ("Cape Peninsula and False Bay", [17.8, -34.5, 19.0, -33.7], "South Africa"), ("Skagerrak and Kattegat", [7.5, 55.6, 12.8, 59.3], "Denmark, Norway and Sweden"),
      ("Truk Lagoon", [151.4, 7.1, 152.1, 7.7], "Micronesia"), ("Ironbottom Sound", [159.6, -9.6, 160.5, -8.9], "Solomon Islands"),
      ("Torres Strait", [141.0, -11.0, 144.0, -9.0], "Australia and Papua New Guinea")]
grows = []
for nm, b, where in GY:
    m = D[D.lon.between(b[0], b[2]) & D.lat.between(b[1], b[3])]
    md = m[m.year.notna()]
    top = m.sort_values("sitelinks", ascending=False)
    grows.append({"name": nm, "where": where, "box": b, "n": len(m), "dated": len(md), "ww": int(md.year.between(1914, 1918).sum() + md.year.between(1939, 1945).sum()),
                  "main_source": SOURCES[int(m.source.mode()[0])][0] if len(m) else "", "famous": [x for x in top[top.sitelinks > 0].name.head(3)],
                  "lon": round((b[0] + b[2]) / 2, 2), "lat": round((b[1] + b[3]) / 2, 2)})
R["graveyards"] = sorted(grows, key=lambda g: -g["n"])
R["gy"] = {g["name"]: g for g in grows}
pd.DataFrame([{k: v for k, v in g.items() if k not in ("famous",)} | {"famous": "; ".join(g["famous"])} for g in R["graveyards"]]).to_csv(f"{DATA}/graveyards.csv", index=False)
famous_empty = [g["name"] for g in grows if g["n"] < 20]
R["gy_empty"] = famous_empty
R["gy_small_n"] = len(famous_empty)

# ---------- oldest dated, famous ----------
old = dated.sort_values(["year", "sitelinks"], ascending=[True, False]).head(14)
R["oldest"] = [{"name": r["name"], "y": int(r.year), "how": r.year_method, "where": r.near_country if r.near_iso != "GBR" else f"{r.uk_nation}, UK",
                "id": r["id"]} for _, r in old.iterrows()]
spot = {}
for n in ["Titanic", "Mary Rose", "RMS Lusitania", "Bismarck", "SS Edmund Fitzgerald", "Batavia", "HMS Royal Oak", "USS Arizona (BB-39)",
          "Antikythera wreck", "Uluburun shipwreck", "Girona", "Costa Concordia", "Tirpitz", "Nuestra Señora de Atocha", "SMS Kronprinz", "Japanese battleship Yamato"]:
    m = D[(D.name == n) & (D.source == 2)].sort_values("sitelinks", ascending=False)
    assert len(m), n
    r = m.iloc[0]
    spot[n] = {"y": None if pd.isna(r.year) else int(r.year), "where": r.near_country, "id": r["id"]}
R["spot"] = spot
R["notable_top"] = [{"name": r["name"], "sl": int(r.sitelinks), "y": None if pd.isna(r.year) else int(r.year)} for _, r in D.sort_values("sitelinks", ascending=False).head(10).iterrows()]
R["depth"] = {"awois_with_depth": int(D[(D.source == 3)].depth_m.notna().sum())}

R["source_checks"] = {"awois_both": CL["awois_both"], "awois_both_agree": CL["awois_both_agree"], "country_qids": CL["country_qids"], "country_qids_labelled": CL["country_qids_labelled"]}
jsave(R, f"{DATA}/results.json", indent=1)

# ---------- Wikipedia lists: the global timeline ----------
L = pd.read_csv(f"{DATA}/wiki_list_wrecks.csv.gz", low_memory=False)
LC = CL["lists"]
Ly = L[L.year.notna()].copy(); Ly["year"] = Ly.year.astype(int)
Ly = Ly[Ly.year.between(1700, 2025)]
FG = [f[0] for f in FLAGC]
yc = pd.crosstab(Ly.year, Ly.cause_group).reindex(index=range(1700, 2026), columns=range(len(CAUSES)), fill_value=0)
yf = pd.crosstab(Ly.year, Ly.flag_group).reindex(index=range(1700, 2026), columns=FG, fill_value=0)
yall = yc.sum(axis=1)
out = pd.DataFrame({"year": yc.index, "wrecks": yall.values})
for i, c in enumerate(CAUSES): out["cause: " + c[0]] = yc[i].values
for f in FG: out["flag: " + f] = yf[f].values
out.to_csv(f"{DATA}/list_years.csv", index=False)
Ld = L[L.decade.notna()].copy(); Ld["decade"] = Ld.decade.astype(int)
dc = pd.crosstab(Ld.decade, Ld.cause_group).reindex(index=range(1700, 2030, 10), columns=range(len(CAUSES)), fill_value=0)
od = pd.DataFrame({"decade": dc.index, "wrecks": dc.sum(axis=1).values})
for i, c in enumerate(CAUSES): od["cause: " + c[0]] = dc[i].values
od.to_csv(f"{DATA}/list_decades.csv", index=False)
avg = lambda a, b: round(float(yall.loc[a:b].mean()), 1)
tot = lambda a, b: int(yall.loc[a:b].sum())
war = Ly[Ly.cause_group == 0]
top = yall.sort_values(ascending=False)
ww2 = Ly[Ly.year.between(1939, 1945)]; ww1 = Ly[Ly.year.between(1914, 1918)]
c19 = Ly[Ly.year.between(1800, 1899)]
cc = Ly.cause_group.value_counts().reindex(range(len(CAUSES)), fill_value=0); ck = int(cc[:-1].sum())
fl_all = Ly.flag_group.value_counts()
LS = {"rows": LC["rows"], "n": LC["after_dedup"], "dups": LC["dups"], "no_ship": LC["no_ship"], "dated": len(Ly), "decade_only": LC["decade_only"],
      "with_coords": LC["with_coords"], "points": int(src_n[4]),
      "years": [[int(y)] + [int(v) for v in yc.loc[y]] for y in yc.index],
      "years_flag": [[int(y)] + [int(v) for v in yf.loc[y]] for y in yf.index],
      "decades": [{"dec": int(d0), "n": int(dc.loc[d0].sum()), "v": [int(v) for v in dc.loc[d0]]} for d0 in dc.index],
      "top": [{"y": int(y), "n": int(n)} for y, n in top.head(10).items()],
      "peak_year": int(top.index[0]), "peak_n": int(top.iloc[0]),
      "peak19_year": int(yall.loc[1800:1899].idxmax()), "peak19_n": int(yall.loc[1800:1899].max()),
      "ww1": tot(1914, 1918), "ww1_avg": avg(1914, 1918), "ww2": tot(1939, 1945), "ww2_avg": avg(1939, 1945),
      "y1917": int(yall[1917]), "y1942": int(yall[1942]), "y1944": int(yall[1944]),
      "inter_avg": avg(1919, 1938), "post_avg": avg(1946, 1965), "dip_avg": avg(1890, 1913), "high19_avg": avg(1850, 1879),
      "modern_avg": avg(1966, 2025), "early_avg": avg(1700, 1749),
      "c19": len(c19), "c19_pct": pc(len(c19), len(Ly)), "y1800_1880_pct": pc(Ly.year.between(1800, 1880).sum(), len(Ly)),
      "uk_pct": pc((Ly.flag_group == "United Kingdom").sum(), len(Ly)),
      "uk_c19_pct": pc((c19.flag_group == "United Kingdom").sum(), len(c19)),
      "uk_ww2_pct": pc((ww2.flag_group == "United Kingdom").sum(), len(ww2)),
      "war_ww2_pct": pc((ww2.cause_group == 0).sum(), len(ww2)), "war_ww1_pct": pc((ww1.cause_group == 0).sum(), len(ww1)),
      "war_total": len(war), "war_in_wars_pct": pc(war.year.between(1914, 1918).sum() + war.year.between(1939, 1945).sum(), len(war)),
      "war_kinds_ww2": {k: int(v) for k, v in ww2[ww2.cause_group == 0].war_kind.value_counts().items()},
      "c19_aground_pct": pc((c19.cause_group == 2).sum(), len(c19)), "c19_founder_pct": pc((c19.cause_group == 1).sum(), len(c19)),
      "causes": [{"name": CAUSES[i][0], "n": int(cc[i]), "pct": pc(cc[i], len(Ly)), "pct_known": pc(cc[i], ck) if i < len(CAUSES) - 1 else None} for i in range(len(CAUSES))],
      "cause_known": ck, "cause_known_pct": pc(ck, len(Ly)),
      "flags": [{"name": k, "n": int(v), "pct": pc(v, len(Ly)), "ww2": int((ww2.flag_group == k).sum())} for k, v in fl_all.items()],
      "flag_recorded_pct": pc((Ly.flag_group != "Not recorded").sum(), len(Ly))}
LS["ww2_vs_inter"] = round(LS["ww2_avg"] / LS["inter_avg"], 1); LS["ww2_vs_high19"] = round(LS["ww2_avg"] / LS["high19_avg"], 2)
LS["ww1_vs_dip"] = round(LS["ww1_avg"] / LS["dip_avg"], 1)
LS["years_over3000"] = [int(y) for y in yall[yall >= 3000].index]
LS["war_years_in_top5"] = sum(1 for t in LS["top"][:5] if 1914 <= t["y"] <= 1918 or 1939 <= t["y"] <= 1945)
R["lists"] = LS
jsave(R, f"{DATA}/results.json", indent=1)

# ---------- page data ----------
fidx = {k: i for i, k in enumerate(FLAGS)}
def fl(r):
    if r.source not in (2, 4) or not isinstance(r.flag_group, str) or not r.flag_group: return fidx["Not recorded"]
    return fidx.get(r.flag_group, fidx["Other"])
order = D.assign(o=D.year.notna().astype(int) * 2 + (D.sitelinks > 0)).sort_values(["o", "sitelinks"]).index
rows = []
for i in order:
    r = D.loc[i]
    rows.append([round(r.lat, 4), round(r.lon, 4), None if pd.isna(r.year) else int(r.year), int(r.cause), int(r.type), fl(r), int(r.source),
                 r["name"], r["id"].replace("AWOIS ", "A"), int(r.sitelinks)] + ([r["description"]] if r.source == 4 else []))
jsave({"cols": ["lat", "lon", "year", "cause", "type", "flag", "source", "name", "id", "sitelinks", "list page (Wikipedia entries)"], "rows": rows}, f"{DATA}/points.json")
SITE = {"eras": [[e[0], e[1], e[2], e[3]] for e in ERAS], "causes": CAUSES, "flagc": FLAGC, "types": TYPES, "sources": SOURCES, "flags": FLAGS,
        "cname": CT["cname"], "cpos": CT["cpos"]}
jsave(SITE, f"{DATA}/site.json")
print("results ok; dated", len(dated), "points", len(rows), os.path.getsize(f"{DATA}/points.json") // 1024, "KB")
print(json.dumps({k: R[k] for k in ("coverage", "timeline")}, default=str)[:3000])
print(json.dumps(R["causes"])[:800]); print(R["flags"]["list"][:8]); print([(g["name"], g["n"]) for g in R["graveyards"]]); print(R["oldest"][:6]); print(R["ancient"]["peak_label"], R["ancient"]["peak_n"], R["ancient"]["n_used"])
