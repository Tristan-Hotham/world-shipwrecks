"""Shared paths and helpers for the world-shipwrecks project.

Raw inputs (read in place, never modified):
  /home/claude/newdata/raw5/wikidata_wrecks.tsv
      Wikidata (CC0), queried through QLever: every item with coordinates (P625) that is an instance of shipwreck
      (Q852190) or has a significant event (P793) of shipwrecking or shipwreck. Columns: item, English label, P31 type
      (rows repeat per type), P585 date, P585 qualifier on the shipwrecking event, P730 service retirement, P17 country or
      P8047 flag, operator, P1478 cause, number of sitelinks, English description. Retrieved 2026.
  /home/claude/newdata/raw5/wiki_shipwreck_lists.tsv
      Structured table scraped from every English Wikipedia "List of shipwrecks in {Month} {Year}" page, plus year and
      decade pages, 1700 to 2025: title, year, month, date heading, ship, flag, bucketed cause, coordinates where given.
      Wikipedia contributors, CC BY-SA 4.0; the derived table (data/wiki_list_wrecks.csv.gz) is shared under the same licence.
  /home/claude/newdata/raw5/wreck_events.tsv, sinking_events_dated.tsv, wreck_dates.tsv
      Extra Wikidata statements for the wreck items: significant events with dates (shipwrecking, sinking, scuttling...),
      and dates (inception P571, dissolved P576, end time P582, service retirement P730, service entry P729). CC0.
  /home/claude/newdata/raw5/wreck_types.tsv
      English labels and counts of the P31 types of all shipwreck items (Wikidata, CC0).
  /dev/shm/wrecks/gh/jalbertbowden_AWOIS-data/AWOIS/AWOIS_*-Wrecks.kmz
      NOAA Office of Coast Survey, Automated Wreck and Obstruction Information System (AWOIS), wrecks layer, as KMZ
      (US Government work, public domain). GitHub mirror: https://github.com/jalbertbowden/AWOIS-data (git clone).
  /dev/shm/wrecks/gh/austinw8_ancient_shipwrecks/geodatabase_shipwrecks.csv
      Summary Geodatabase of Shipwrecks 1500 BCE to 1500 CE (Harvard Mapping Past Societies / DARMC, merging the Oxford
      Roman Economy Project database after Parker and Strauss), via https://github.com/austinw8/ancient_shipwrecks.
      Licence of the data not stated in the mirror: used for aggregate counts per century only, no records redistributed.
  /home/claude/newdata/raw/geo/  Natural Earth countries, admin-1, populated places (public domain).
"""
import json, gzip, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("WRECK_RAW", "/home/claude/newdata/raw5")
GH = os.environ.get("WRECK_GH", "/dev/shm/wrecks/gh")          # git clones of the GitHub mirrors (see above)
GEO = os.environ.get("WRECK_GEO", "/home/claude/newdata/raw/geo")
QIDLAB = os.environ.get("WRECK_QIDLAB", "/home/claude/newdata")  # other Wikidata extracts, used only for English labels of country QIDs
FONTS = os.environ.get("WRECK_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("WRECKTMP", "/dev/shm/wrecks"), "work")
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "world-shipwrecks"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23850289"                  # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/world-shipwrecks/"            # filled in by the publisher
RETRIEVED = "2026"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")

# where the record comes from (order = legend order)
SOURCES = [("Wikidata: Scottish wrecks (from Canmore)", "#2F7FB8"),
           ("Wikidata: Welsh wrecks (from Coflein)", "#5E8C4A"),
           ("Wikidata: other wrecks", "#B3202A"),
           ("NOAA AWOIS: United States waters", "#C9A227"),
           ("Wikipedia shipwreck lists (entries with coordinates)", "#7A4E9C")]
# eras of loss (order = legend order); index len(ERAS)-1 is "not dated"
ERAS = [("Before 1700", "#6B4E9B", -9999, 1699), ("1700 to 1799", "#3E7CB1", 1700, 1799), ("1800 to 1913", "#2A9D8F", 1800, 1913),
        ("First World War, 1914 to 1918", "#E07B24", 1914, 1918), ("1919 to 1938", "#C9A227", 1919, 1938),
        ("Second World War, 1939 to 1945", "#B3202A", 1939, 1945), ("1946 on", "#4F6D7A", 1946, 2100), ("Not dated", "#B9B3A6", None, None)]
CAUSES = [("War: torpedo, mine, aircraft or gunfire", "#B3202A"), ("Foundered or storm", "#3E7CB1"),
          ("Wrecked or ran aground", "#C9A227"), ("Collision", "#7A4E9C"), ("Fire or explosion", "#E07B24"),
          ("Scuttled or sunk on purpose", "#2A9D8F"), ("Accident, kind not recorded", "#8A8F96"), ("Cause not recorded", "#CFC9BB")]
# flag groups for the Wikipedia lists timeline (order = legend order), colours
FLAGC = [("United Kingdom", "#2F7FB8"), ("United States", "#B3202A"), ("France", "#7A4E9C"), ("Germany", "#3B3B3B"),
         ("Norway", "#2A9D8F"), ("Netherlands", "#E07B24"), ("Sweden", "#C9A227"), ("Denmark", "#9C5B2E"),
         ("Russia and the Soviet Union", "#8E3B5A"), ("Japan", "#D96C6C"), ("Italy", "#5E8C4A"), ("Spain", "#B59A3A"),
         ("Other", "#8A8F96"), ("Not recorded", "#CFC9BB")]
TYPES = [("Warship", "#2B3A55"), ("Submarine", "#B3202A"), ("Steam or motor ship", "#E07B24"), ("Sailing vessel", "#2A9D8F"),
         ("Fishing vessel", "#3E7CB1"), ("Barge, boat or small craft", "#9C8460"), ("Ship, type not recorded", "#B9B3A6")]


def era_of(y):
    if y is None or y != y:
        return len(ERAS) - 1
    for i, e in enumerate(ERAS[:-1]):
        if e[2] <= y <= e[3]:
            return i
    return len(ERAS) - 1


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "yr": return f"{-int(v)} BC" if int(v) < 0 else str(int(v))
    raise ValueError(f)
