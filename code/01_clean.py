"""Clean and combine the wreck records.

Wikidata: one row per item (types, countries collected), coordinates parsed, the import it came from recognised
(Canmore for Scotland, Coflein for Wales, otherwise "other"), a year of loss derived in a fixed order, a cause and a
vessel type read from labels and descriptions. NOAA AWOIS: wreck placemarks parsed from the KMZ files, year and cause
read from the survey history text. AWOIS records that duplicate a Wikidata item (same name within 5 km) are dropped.
Each wreck gets the nearest present-day country (Natural Earth) and, in the UK, the nearest nation.
Output: data/wrecks.csv and WORK/clean.json (counts used by 03_results.py)."""
import glob, html, zipfile
import numpy as np
import pandas as pd
import shapely
from shapely.geometry import shape, Point
from common import *

C = {}   # cleaning counts
YMAX = 2026

# ---------------- Wikidata ----------------
d = pd.read_csv(f"{RAW}/wikidata_wrecks.tsv", sep="\t", dtype=str, quoting=3, keep_default_na=False)
d.columns = [c.lstrip("?") for c in d.columns]
strip = lambda s: s[1:-1] if len(s) >= 2 and s[0] == '"' and s[-1] == '"' else s
C["wd_rows"] = len(d); C["wd_items"] = d.s.nunique()
TL = {}
for _, r in pd.read_csv(f"{RAW}/wreck_types.tsv", sep="\t", dtype=str, quoting=3, keep_default_na=False).iterrows():
    TL[r["?t"]] = strip(r["?tL"])

# English labels for country / flag QIDs, taken from other Wikidata extracts in the raw folder
need = set(d.country) - {""}
QL = {}
for f in glob.glob(f"{QIDLAB}/raw*/**/*.tsv", recursive=True):
    t = open(f, encoding="utf-8", errors="ignore").read()
    for q, l in re.findall(r"entity/(Q\d+)>\s*\"([^\"]+)\"@en", t):
        if q in need and q not in QL:
            QL[q] = l
C["country_qids"] = len(need); C["country_qids_labelled"] = sum(q in QL for q in need)


def year_of(s):
    m = re.match(r"^(-?)(\d{1,4})-", s or "")
    if not m: return None
    y = int(m.group(2)) * (-1 if m.group(1) else 1)
    if m.group(1): y -= 1          # Wikidata RDF uses XSD years: -0060 is 61 BC
    return y if y <= YMAX else None


VERB = r"(?:sank|sunk|sinking|wrecked|wreck(?:ed)? (?:of|in)|lost|scuttled|torpedoed|foundered|stranded|ran aground|went aground|burnt|burned|blown up|destroyed)"
P_VERB = re.compile(VERB + r"\b(?P<mid>[^.;()]{0,70}?)\b(?P<y>1\d{3}|20[0-2]\d)\b", re.I)
P_UNK = re.compile(r"^(?:Unknown|Unnamed|Unidentified)(?: (?:wreck|vessel|ship|shipwreck|craft|boat))?[:,]? (?P<y>1[5-9]\d\d|20[0-2]\d)\b", re.I)
P_PLUS = re.compile(r"\(\+ ?(?P<y>1[5-9]\d\d|20[0-2]\d)\)")
P_PAREN = re.compile(r"\((?P<y>1\d{3}|20[0-2]\d|\d{1,4} BC)\)\s*$")
BLOCK = re.compile(r"\b(built|launched|commissioned|laid down|completed|constructed|raised|refloated|salvaged|discovered|found|located|rediscovered)\b", re.I)


def text_year(lab, desc, is_wreck):
    for t in (desc, lab):
        for m in P_VERB.finditer(t):
            if BLOCK.search(m.group("mid")):
                continue
            return int(m.group("y")), "text: sank or wrecked in a year"
    m = P_PLUS.search(lab)
    if m: return int(m.group("y")), "label: loss year after a plus sign"
    m = P_UNK.match(lab)
    if m: return int(m.group("y")), "label: unknown vessel lost in a year (Canmore)"
    if is_wreck:
        m = P_PAREN.search(lab)
        if m:
            g = m.group("y")
            return (-int(g.split()[0]) if "BC" in g else int(g)), "label: year in brackets"
    return None, None


CAUSE_RX = [  # first match wins (index into CAUSES)
    (5, r"scuttl|sunk as (?:a )?target|target ship|expended as|artificial reef|as an? (?:artificial )?reef|deliberately sunk|intentionally sunk|sunk to (?:form|create|make)|blockship"),
    (0, r"torpedo|u-boat attack|sunk by (?:a )?(?:german|japanese|italian|british|american|u-|submarine|aircraft|mine|gunfire|enemy)|struck a mine|hit a mine|mined\b|by a mine|bombed|bombing|air attack|kamikaze|gunfire|shellfire|enemy action|naval battle|battle of"),
    (3, r"collision|collided|rammed"),
    (4, r"\bfire\b|caught fire|burnt|burned|explosion|exploded|blew up|blown up"),
    (1, r"storm|gale|hurricane|typhoon|cyclone|heavy weather|heavy seas|blizzard|tempest"),
    (2, r"aground|stranded|stranding|wrecked on (?:a |the )?(?:reef|rocks|bar|shoal|coast)|struck (?:a |the )?(?:reef|rocks)|ran ashore|driven ashore|foundered on"),
]
CAUSE_RX = [(i, re.compile(p, re.I)) for i, p in CAUSE_RX]


def cause_of(*texts):
    t = " | ".join(x for x in texts if x)
    for i, rx in CAUSE_RX:
        if rx.search(t):
            return i
    return len(CAUSES) - 1


TYPE_RX = [  # index into TYPES; first match wins, on type labels then description
    (1, r"submarine|u-boat|\bU-\d|\bUC-\d|\bUB-\d"),
    (0, r"destroyer|cruiser|battleship|dreadnought|frigate|corvette|torpedo boat|warship|gunboat|minesweeper|minelayer|naval trawler|ship of the line|aircraft carrier|monitor|sloop-of-war|man-of-war|navy|naval|armed merchant cruiser|escort|patrol|landing ship|landing craft|motor launch|motor torpedo|depot ship|hospital ship|auxiliary|warship|galleon|first-rate|second-rate|third-rate|fourth-rate|fifth-rate|sixth-rate|frigate|privateer"),
    (4, r"fishing|drifter|trawler|smack|whaler|whaling|seiner|herring|coble|fifie|zulu"),
    (2, r"steam|motor ship|motor vessel|cargo ship|merchant vessel|merchant ship|tanker|liner|freighter|ferry|paddle|collier|liberty ship|tug|ocean liner|passenger ship|container|bulk carrier|reefer|ore carrier|lake freighter|cargo"),
    (3, r"sloop|lugger|bark|barque|brigantine|brig\b|schooner|ketch|cutter|yawl|snow\b|wherry|galliot|full-rigged|sailing|clipper|fluyt|hoy|pink\b|dogger|ship-rigged|square rigger|east indiaman|indiaman|carrack|caravel|junk"),
    (5, r"barge|lighter|boat|yacht|gabbart|scow|pontoon|launch|dredger|hulk|canoe|raft|punt|keel\b|flat\b|wreck of a boat"),
]
TYPE_RX = [(i, re.compile(p, re.I)) for i, p in TYPE_RX]


def type_of(*texts):
    for t in texts:
        if not t: continue
        for i, rx in TYPE_RX:
            if rx.search(t):
                return i
    return len(TYPES) - 1


# flags grouped across regimes (names as recorded in Wikidata)
FLAG_GROUPS = {
    "United Kingdom": ["United Kingdom", "United Kingdom of Great Britain and Ireland", "Kingdom of Great Britain", "Kingdom of England", "Kingdom of Scotland"],
    "United States": ["United States", "Confederate States of America"],
    "Germany": ["Germany", "German Empire", "German Reich", "Nazi Germany", "East Germany", "West Germany", "Kingdom of Prussia"],
    "Japan": ["Japan", "Empire of Japan"],
    "Italy": ["Italy", "Kingdom of Italy"],
    "Russia and the Soviet Union": ["Russia", "Russian Empire", "Soviet Union"],
    "Netherlands": ["Netherlands", "Dutch Republic", "Kingdom of the Netherlands"],
    "France": ["France", "Kingdom of France", "French First Republic", "Vichy France", "French Third Republic"],
}
G_OF = {n: g for g, ns in FLAG_GROUPS.items() for n in ns}

NOTSHIP = re.compile(r"aircraft|airplane|aeroplane|douglas dc|helicopter|\bbomber\b|plane crash|plane wreck|airliner|\bB-(?:17|24|25|29)\b", re.I)
# extra Wikidata dates: loss events with a date, and date properties of the wreck items
EXTRA = {}
ev = pd.read_csv(f"{RAW}/wreck_events.tsv", sep="\t", dtype=str, quoting=3, keep_default_na=False)
ev = ev[ev["?eventL"].str.strip('"').isin(["shipwrecking", "sinking", "scuttling", "destruction"])]      # not groundings: many ships survived one
for _, r in ev.iterrows():
    for v in (r["?time"], r["?start"], r["?end"]):
        if year_of(v) is not None:
            EXTRA.setdefault(r["?s"], {}).setdefault("event", []).append(year_of(v)); break
se = pd.read_csv(f"{RAW}/sinking_events_dated.tsv", sep="\t", dtype=str, quoting=3, keep_default_na=False)
for _, r in se.drop_duplicates(["?s", "?time"]).iterrows():
    if year_of(r["?time"]) is not None:
        EXTRA.setdefault(r["?s"], {}).setdefault("event", []).append(year_of(r["?time"]))
wd2 = pd.read_csv(f"{RAW}/wreck_dates.tsv", sep="\t", dtype=str, quoting=3, keep_default_na=False)
for _, r in wd2.iterrows():
    if r["?p"] in ("P571", "P576", "P582", "P585", "P730") and year_of(r["?v"]) is not None:
        EXTRA.setdefault(r["?s"], {}).setdefault(r["?p"], []).append(year_of(r["?v"]))
C["extra_items_with_dates"] = len(EXTRA)

NONVESSEL = re.compile(r"island|atoll|shoal|oil spill|unidentified object|territor|beach|settlement", re.I)
rows = []
for s, g in d.groupby("s", sort=False):
    r0 = g.iloc[0]
    coords = [c for c in g.coord.unique() if c.startswith("POINT(")]
    if not coords:
        C["wd_no_point"] = C.get("wd_no_point", 0) + 1
        continue
    lon, lat = map(float, re.match(r"POINT\(([-\d.eE]+) ([-\d.eE]+)\)", coords[0]).groups())
    lab, desc = strip(r0.sL), strip(r0.desc)
    if NOTSHIP.search(lab + " | " + desc):
        C["wd_aircraft_dropped"] = C.get("wd_aircraft_dropped", 0) + 1
        continue
    types = list(dict.fromkeys(g.type))
    tlabs = [TL.get(t, "") for t in types]
    ctry = [QL.get(q, q) for q in dict.fromkeys(x for x in g.country if x)]
    if "Canmore" in lab or re.search(r"Scottish|Canmore", desc, re.I):
        src = 0
    elif re.match(r"^shipwreck, [\d.]+ k?m from ", desc):
        src = 1
    else:
        src = 2
    y, how = None, None
    ex = EXTRA.get(s, {})
    cands = [([year_of(v) for v in g.sunk.unique() if v] + ex.get("event", []), "Wikidata: date of the shipwrecking or sinking event"),
             ([year_of(v) for v in g.date.unique() if v] + ex.get("P585", []), "Wikidata: point in time"),
             ([year_of(v) for v in g.end.unique() if v] + ex.get("P730", []), "Wikidata: service retirement"),
             (ex.get("P576", []) + ex.get("P582", []), "Wikidata: dissolved or end time"),
             (ex.get("P571", []) if set(types) == {"Q852190"} else [], "Wikidata: inception of a wreck-only item")]
    for k, (ys, nm) in enumerate(cands):
        ys = [v for v in ys if v is not None]
        if ys:
            y, how = (max(ys) if k == 0 else min(ys)), nm      # the last shipwrecking or sinking event is the final loss
            break
    if y is None:
        y, how = text_year(lab, desc, "Q852190" in types)
    tl = "; ".join(t for t in tlabs if t and t not in ("shipwreck", "ship"))
    if NONVESSEL.search(tl) and type_of(tl) == len(TYPES) - 1 and "Q852190" not in types:
        C["wd_not_vessel_dropped"] = C.get("wd_not_vessel_dropped", 0) + 1     # islands, shoals, an oil spill
        continue
    rows.append({"id": s, "source": src, "name": lab or "(no English label)", "lat": round(lat, 5), "lon": round(lon, 5),
                 "year": y, "year_method": how or "", "cause": cause_of(desc, lab), "type": type_of(tl, desc, lab),
                 "type_labels": "; ".join(t for t in tlabs if t), "country_or_flag": "; ".join(ctry),
                 "flag_group": G_OF.get(ctry[0], ctry[0]) if ctry else "", "sitelinks": int(r0.sl or 0),
                 "description": desc, "depth_m": None})
W = pd.DataFrame(rows)
C["wd_mapped"] = len(W)
C["wd_by_source"] = W.source.value_counts().sort_index().tolist()

# ---------------- NOAA AWOIS ----------------
arows = []
for f in sorted(glob.glob(f"{GH}/jalbertbowden_AWOIS-data/AWOIS/AWOIS_*-Wrecks.kmz")):
    with zipfile.ZipFile(f) as z:
        t = z.read("doc.kml").decode("utf-8", errors="replace")
    for pm in re.findall(r"<Placemark.*?</Placemark>", t, re.S):
        arows.append({k: html.unescape(v).strip() for k, v in re.findall(r"<th>(\w+)</th>\s*<td>(.*?)</td>", pm, re.S)})
A = pd.DataFrame(arows)
C["awois_rows"] = len(A)
A = A[~A.FEATURE_TYPE.str.startswith("Rock")].copy()
C["awois_rocks_dropped"] = C["awois_rows"] - len(A)
H = A.HISTORY.fillna("").str.replace(r"\s+", " ", regex=True)
P_AW = re.compile(r"\b(?:SUNK|SANK|LOST|WRECKED|FOUNDERED|STRANDED|BURNED|TORPEDOED|ABANDONED|SCUTTLED)\b(?: (?:ON|IN|DURING|ABOUT|APPROX\.?|CIRCA))? (?:(\d{1,2})/(\d{1,2})/(\d{2}|\d{4})\b|((?:18|19|20)\d\d)\b|(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*\.? (?:\d{1,2},? )?((?:18|19|20)\d\d|\d\d)\b)")


def aw_year(t):
    for m in P_AW.finditer(t):
        for gi in (3, 4, 5):
            v = m.group(gi)
            if v:
                y = int(v) if len(v) == 4 else 1900 + int(v)    # two-digit years in AWOIS lists are 20th century
                return y if y <= YMAX else None
    return None


AW_CAUSE = [
    (5, r"ARTIFICIAL REEF|SUNK AS (?:AN? )?(?:TARGET|REEF)|SCUTTLED|INTENTIONALLY SUNK|DELIBERATELY SUNK|TO ESTAB(?:LISH)? (?:AN? )?(?:ARTIFICIAL )?REEF|REEF SITE|REEF PROGRAM|FOR (?:A )?REEF"),
    (0, r"BY (?:GERMAN |ENEMY )?SUBMARINE|BY (?:A )?(?:GERMAN )?SUB\b|TORPEDO|U-BOAT|BY (?:ENEMY |NAVY |A )?MINE\b|ENEMY ACTION|GUNFIRE|SHELLED BY|BOMBED"),
    (3, r"COLLISION|COLLIDED"),
    (4, r"\bFIRE\b(?! ISLAND)|BURNED|EXPLOSION|EXPLODED"),
    (1, r"HURRICANE|STORM|\bGALE\b|HEAVY WEATHER|HEAVY SEAS"),
    (2, r"STRANDED|STRANDING|AGROUND"),
    (6, r"MARINE CAS[UA]+LTY"),
]
AW_CAUSE = [(i, re.compile(p)) for i, p in AW_CAUSE]


def aw_cause(t):
    for i, rx in AW_CAUSE:
        if rx.search(t): return i
    return len(CAUSES) - 1


def aw_type(t):
    m = re.search(r"NO\. ?\d+; ([A-Z][A-Z /-]{2,30}?)[,;]", t)
    k = m.group(1) if m else ""
    if not k:
        m = re.search(r"\b(SCHOONER|TANKER|FREIGHTER|LIBERTY SHIP|TRAWLER|BARGE|TUG|STEAMER|STEAMSHIP|DESTROYER|SUBMARINE|U-BOAT|MENHADEN|FISHING VESSEL|YACHT|SLOOP|BARK|BARKENTINE|BRIG)\b", t)
        k = m.group(1) if m else ""
    return type_of(k.lower().replace("ftr", "freighter")) if k else len(TYPES) - 1


UNIT = {"Feet and tenths": .3048, "Fathoms and tenths": 1.8288, "Meters and tenths": 1.0}
ys = pd.to_numeric(A.YEARSUNK, errors="coerce")
yt = pd.Series([aw_year(t) for t in H], index=A.index)
A["year"] = yt.where(yt.notna(), ys)
A["how"] = np.where(yt.notna(), "AWOIS: year sunk in the history text", np.where(ys.notna(), "AWOIS: YEARSUNK field", ""))
C["awois_year_text"] = int(yt.notna().sum()); C["awois_yearsunk_field"] = int(ys.notna().sum())
both = yt.notna() & ys.notna(); C["awois_both"] = int(both.sum()); C["awois_both_agree"] = int((yt[both] == ys[both]).sum())
dep = pd.to_numeric(A.DEPTH, errors="coerce") * A.SOUNDING_TYPE.map(UNIT)
nm = A.VESSLTERMS.fillna("").str.strip()
B = pd.DataFrame({"id": "AWOIS " + A.RECRD, "source": 3,
                  "name": np.where(nm.str.upper().isin(["", "UNKNOWN", "WRECK", "UNKNOWN WRECK", "UNK"]), "Unknown wreck", nm.str.title()),
                  "lat": pd.to_numeric(A.LATDEC).round(5), "lon": pd.to_numeric(A.LONDEC).round(5), "year": A.year, "year_method": A.how,
                  "cause": [aw_cause(t) for t in H], "type": [aw_type(t) for t in H], "type_labels": A.FEATURE_TYPE.fillna(""),
                  "country_or_flag": "", "flag_group": "", "sitelinks": 0, "description": A.FEATURE_TYPE.fillna(""),
                  "depth_m": dep.round(1)})
B = B[B.lat.between(-90, 90) & B.lon.between(-180, 180)]

# ---------------- duplicates between Wikidata and AWOIS ----------------
def key(s):
    s = norm(s)
    s = re.sub(r"^(?:ss|ms|mv|rms|uss|hms|ssv|usat|usns|sv|ex)\s+", "", s)
    return s


wo = W[W.source == 2]
wk = {}
for i, r in wo.iterrows():
    wk.setdefault(key(r["name"]), []).append(i)
drop = []
for i, r in B.iterrows():
    k = key(r["name"])
    if r["name"] == "Unknown wreck" or k not in wk: continue
    for j in wk[k]:
        a = W.loc[j]
        dkm = 111 * np.hypot(a.lat - r.lat, (a.lon - r.lon) * np.cos(np.radians(r.lat)))
        if dkm < 5:
            drop.append(i)
            if pd.isna(W.at[j, "year"]) and pd.notna(r.year):
                W.at[j, "year"] = r.year; W.at[j, "year_method"] = "AWOIS duplicate: " + r.year_method
            if W.at[j, "cause"] == len(CAUSES) - 1: W.at[j, "cause"] = r.cause
            break
C["awois_duplicates_dropped"] = len(drop)
B = B.drop(drop)
C["awois_kept"] = len(B)

# ---------------- Wikipedia shipwreck lists: entries with coordinates ----------------
from lists import load_lists
LW_, LC = load_lists()
LW_.to_csv(f"{DATA}/wiki_list_wrecks.csv.gz", index=False,
           columns=["title", "year", "decade", "month", "section", "ship", "flag", "flag_group", "cause", "cause_group", "war_kind", "lat", "lon"])
C["lists"] = LC
P = LW_[LW_.lat.notna()].copy()
P = pd.DataFrame({"id": ["WP" + str(i) for i in P.index], "source": 4,
                  "name": np.where(P.ship.str.strip() == "", "Unnamed vessel", P.ship.str.strip()),
                  "lat": P.lat.round(5), "lon": P.lon.round(5), "year": P.year, "year_method": "Wikipedia list page",
                  "cause": P.cause_group, "type": len(TYPES) - 1, "type_labels": "", "country_or_flag": P.flag,
                  "flag_group": np.where(P.flag_group == "Not recorded", "", np.where(P.flag_group == "Other", P.flag, P.flag_group)), "sitelinks": 0, "description": P.title, "depth_m": None})
# drop list entries that duplicate a mapped wreck (same name within 20 km); give the wreck the list's year and cause if it had none
base = pd.concat([W[W.source == 2], B])
bk = {}
for i, r in base.iterrows():
    bk.setdefault(key(r["name"]), []).append((r.lat, r.lon, r.source, r["id"]))
idx_of = {(r.source, r["id"]): i for i, r in pd.concat([W, B]).reset_index(drop=True).iterrows()}
WB = pd.concat([W, B], ignore_index=True)
drop = []; got_year = 0
for i, r in P.iterrows():
    k = key(r["name"])
    if r["name"] == "Unnamed vessel" or k not in bk: continue
    for la, lo, so, iid in bk[k]:
        if 111 * np.hypot(la - r.lat, (lo - r.lon) * np.cos(np.radians(r.lat))) < 20:
            drop.append(i); j = idx_of[(so, iid)]
            if pd.isna(WB.at[j, "year"]) and pd.notna(r.year):
                WB.at[j, "year"] = int(r.year); WB.at[j, "year_method"] = "Wikipedia list page (matched entry)"; got_year += 1
            if WB.at[j, "cause"] == len(CAUSES) - 1: WB.at[j, "cause"] = r.cause
            break
C["lists_points_dup"] = len(drop); C["lists_points_gave_year"] = got_year
P = P.drop(drop)
C["lists_points_kept"] = len(P)
D = pd.concat([WB, P], ignore_index=True)
D["year"] = D.year.astype("Int64")

# ---------------- nearest country and UK nation ----------------
W10 = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")
iso_of = lambda p: p["ISO_A3_EH"] if p.get("ISO_A3_EH") not in ("-99", None) else p["ADM0_A3"]
geoms, isos, names, conts = [], [], [], []
for f in W10["features"]:
    p = f["properties"]
    geoms.append(shape(f["geometry"]).buffer(0)); isos.append(iso_of(p))
    names.append((p["NAME_EN"] or p["NAME"]).replace("United States of America", "United States").replace("People's Republic of China", "China"))
    conts.append(p["CONTINENT"])
tree = shapely.STRtree(geoms)
pts = shapely.points(D.lon.values, D.lat.values)
idx, dist = tree.query_nearest(pts, return_distance=True, all_matches=False)
near = np.empty(len(D), dtype=int); near[idx[0]] = idx[1]
dd = np.empty(len(D)); dd[idx[0]] = dist
D["near_iso"] = [isos[k] for k in near]; D["near_country"] = [names[k] for k in near]; D["near_continent"] = [conts[k] for k in near]
D["shore_deg"] = np.round(dd, 3)
A1 = jload(f"{GEO}/ne_10m_admin_1_states_provinces.geojson")
ug, un = [], []
for f in A1["features"]:
    p = f["properties"]
    if p.get("adm0_a3") == "GBR":
        ug.append(shape(f["geometry"]).buffer(0)); un.append(p.get("geonunit") or "")
ut = shapely.STRtree(ug)
uk = np.where(D.near_iso == "GBR")[0]
k2 = ut.query_nearest(pts[uk], all_matches=False)
nat = np.array([""] * len(D), dtype=object); nat[uk[k2[0]]] = [un[k] for k in k2[1]]
D["uk_nation"] = nat
C["uk_nations"] = D[D.near_iso == "GBR"].uk_nation.value_counts().to_dict()

D["era"] = [era_of(None if pd.isna(y) else int(y)) for y in D.year]
D = D.sort_values(["source", "id"]).reset_index(drop=True)
D.to_csv(f"{DATA}/wrecks.csv", index=False)
jsave(C, f"{WORK}/clean.json", indent=1)
print(json.dumps(C, indent=1, default=str))
print("dated", D.year.notna().sum(), "of", len(D)); print(D.year_method.value_counts())
print(D.groupby("source").year.apply(lambda s: s.notna().sum()))
print("cause", D.cause.value_counts().sort_index().tolist()); print("type", D.type.value_counts().sort_index().tolist())
