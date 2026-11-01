"""Wikipedia's "List of shipwrecks in {Month} {Year}" pages (and year and decade pages), 1700 to 2025, as a structured
table: one row per ship entry with the page title, year, month, date heading, ship, flag, a bucketed cause and, for a
minority, coordinates. Text of Wikipedia is CC BY-SA 4.0 (Wikipedia contributors); the table derived here is shared
under the same licence.

Cleaning: rows are deduplicated on page title + ship + date heading (rows without a ship name are kept, since several
unnamed vessels can be lost on one day). Year pages for years that also have month pages hold only "Unknown date"
entries, so the two do not double count. Decade pages (the 1700s to 1750s) have no year: the year is taken from the
date heading where it contains one; otherwise the row counts only towards its decade. Flags are grouped across
regimes and spellings; causes are grouped into the study's categories."""
import numpy as np
import pandas as pd
from common import *

# study cause categories (index into CAUSES) for the list's cause buckets
CAUSE_MAP = {"torpedo": 0, "mine": 0, "aircraft": 0, "other war": 0, "foundered": 1, "wrecked/aground": 2, "collision": 3,
             "fire/explosion": 4, "scuttled": 5, "other/unknown": 7, "ice": 7, "": 7}
WAR_KIND = {"torpedo": "Torpedo", "mine": "Mine", "aircraft": "Aircraft", "other war": "Gunfire, capture or other war"}

FLAG_RULES = [   # (group, regex on the flag as written)
    ("United Kingdom", r"^(ukgbi|uk|united kingdom|united kingdom of great britain and ireland|kingdom of great britain|kingdom of england|kingdom of scotland|kingdom of ireland|great britain|england|scotland|isle of man|guernsey|jersey)$"),
    ("United States", r"^(united states|usa|us|confederate states of america|united states of america)$"),
    ("France", r"^(france|fra|kingdom of france|french first republic|first french empire|second french empire|french second republic|french third republic|free france|vichy france|july monarchy|bourbon restoration)$"),
    ("Germany", r"^(germany|nazi germany|german empire|german reich|weimar republic|west germany|east germany|allied-occupied germany|prussia|kingdom of prussia|hamburg|bremen|lübeck|lubeck|mecklenburg|mecklenburg-schwerin|oldenburg|kingdom of hanover|electorate of hanover|hanover|north german confederation|schleswig-holstein)$"),
    ("Netherlands", r"^(netherlands|kingdom of the netherlands|united kingdom of the netherlands|dutch republic|batavian republic|kingdom of holland)$"),
    ("Norway", r"^(norway|norway-sweden|sweden-norway)$"),
    ("Sweden", r"^(sweden)$"),
    ("Denmark", r"^(denmark|denmark-norway)$"),
    ("Russia and the Soviet Union", r"^(russia|russian empire|soviet union|tsardom of russia|russian federation)$"),
    ("Japan", r"^(japan|empire of japan)$"),
    ("Italy", r"^(italy|kingdom of italy|kingdom of sardinia|kingdom of the two sicilies|papal states|republic of genoa|republic of venice|austrian italy)$"),
    ("Spain", r"^(spain|kingdom of spain|spanish empire)$"),
    ("Greece", r"^(greece|kingdom of greece|first hellenic republic)$"),
    ("Canada", r"^(canada|province of canada|newfoundland|dominion of newfoundland|nova scotia|new brunswick|prince edward island)$"),
    ("Portugal", r"^(portugal|kingdom of portugal)$"),
]
FLAG_RULES = [(g, re.compile(p, re.I)) for g, p in FLAG_RULES]


def flag_group(f):
    f = (f or "").strip()
    if not f: return "Not recorded"
    for g, rx in FLAG_RULES:
        if rx.match(f): return g
    return "Other"


MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def load_lists():
    w = pd.read_csv(f"{RAW}/wiki_shipwreck_lists.tsv", sep="\t", dtype=str, keep_default_na=False, quoting=3)
    C = {"rows": len(w)}
    w = pd.concat([w[w.ship == ""], w[w.ship != ""].drop_duplicates(["title", "ship", "section"])]).sort_index()
    C["after_dedup"] = len(w); C["dups"] = C["rows"] - len(w); C["no_ship"] = int((w.ship == "").sum())
    y = pd.to_numeric(w.year, errors="coerce")
    sy = pd.to_numeric(w.section.str.extract(r"\b(1[6-9]\d\d|20[0-2]\d)\b")[0], errors="coerce")
    ty = pd.to_numeric(w.title.str.extract(r"in (?:[A-Z][a-z]+ )?(\d{4})$")[0], errors="coerce")
    C["year_from_section"] = int((y.isna() & sy.notna()).sum())
    y = y.fillna(sy).fillna(ty)
    dec = pd.to_numeric(w.title.str.extract(r"the (\d{4})s$")[0], errors="coerce")
    w["year"] = y.astype("Int64")
    w["decade"] = (y // 10 * 10).fillna(dec).astype("Int64")
    C["decade_only"] = int(w.year.isna().sum())
    w["cause_group"] = w.cause.map(CAUSE_MAP).fillna(7).astype(int)
    unk = set(w.cause.unique()) - set(CAUSE_MAP); assert not unk, unk
    w["war_kind"] = w.cause.map(WAR_KIND).fillna("")
    w["flag_group"] = [flag_group(f) for f in w.flag]
    w["lat"] = pd.to_numeric(w.lat, errors="coerce"); w["lon"] = pd.to_numeric(w.lon, errors="coerce")
    ok = w.lat.between(-90, 90) & w.lon.between(-180, 180) & ~((w.lat == 0) & (w.lon == 0))
    w.loc[~ok, ["lat", "lon"]] = np.nan
    C["with_coords"] = int(ok.sum())
    w["month"] = pd.to_numeric(w.month, errors="coerce").astype("Int64")
    return w.reset_index(drop=True), C

