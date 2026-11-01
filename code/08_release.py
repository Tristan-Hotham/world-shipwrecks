"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23850289, https://doi.org/10.5281/zenodo.23850289 and https://blog.tristanhotham.com/2026/10/31/world-shipwrecks/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile, importlib.util
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Shipwrecks_of_the_World"
T, CV, CA, TY, GY, S = R["timeline"], R["coverage"], R["causes"], R["types"], R["gy"], R["source"]

# the page build checks the shared facts; these are numbers written in alt text in the blog
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "04_build_site.py")); spec.loader.exec_module(importlib.util.module_from_spec(spec))
LS = R["lists"]
Y = {r[0]: sum(r[1:]) for r in LS["years"]}
assert Y[1917] == 4083 and Y[1944] == 4570 and LS["peak19_n"] == 3794
assert sum(2000 <= Y[y] <= 3800 for y in range(1842, 1881)) >= .85 * 39 and max(Y[y] for y in range(1842, 1881)) <= 3800, "plateau"
F = pd.read_csv(f"{DATA}/list_years.csv"); F["dec"] = F.year // 10 * 10; G = F.groupby("dec").sum(numeric_only=True)
uk = G["flag: United Kingdom"] / G["wrecks"]; us = G["flag: United States"] / G["wrecks"]
assert all(.58 <= uk[d] <= .87 for d in range(1740, 1890, 10) if d != 1810), uk.loc[1740:1880].round(2).to_dict()     # 1810s: many flags unrecorded
assert us[1890] > .35 and us[1900] > .35
assert [f"{c['pct']:.0f}" for c in LS["causes"]] == ["10", "15", "53", "4", "4", "2", "0", "12"]     # as the figure prints them
assert [round(b["pct"]) for b in S["by_source"]] == [44, 11, 4, 12, 29]
assert (round(CV["scotland_pct"]), round(CV["wales_pct"]), round(CV["us_pct"]), round(CV["rest_pct"])) == (45, 11, 16, 23)
assert [GY[k]["n"] for k in ("Firth of Clyde", "Shetland", "Gulf of Mexico, US coast", "English Channel", "Truk Lagoon", "Ironbottom Sound", "Torres Strait")] == [2676, 1587, 1398, 953, 20, 11, 1]
assert round(TY["list"][3]["pct_known"]) == 37

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG|DOI_URL|BLOG_URL|DOI\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u), post, re.M) for u in used) and "wp:image" not in post
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "Shipwrecks of the world, and how many over time",
        "slug": "world-shipwrecks",
        "excerpt": f"Wikipedia lists {LS['n']:,} shipwrecks since 1700. I counted them year by year: three of the five worst years are war years, with {LS['peak_year']} the worst. The huge 1800s plateau owes a lot to British newspapers.",
        "seo_description": f"{LS['n']:,} shipwrecks listed on Wikipedia since 1700, counted by year, cause and flag: the world wars, the age of sail and Lloyd's List.",
        "tags": ["shipwrecks", "maps", "data visualisation", "maritime history", "Second World War", "Wikipedia", "Lloyd's List", "open data"],
        "header_alt": f"Title card reading 'Shipwrecks of the world' in black and red on pale paper, beside a bar chart of wrecks listed per year from 1700 to 2025: a long ochre plateau in the 1800s and two red spikes in the world wars. Text: {LS['n']:,} wrecks listed on Wikipedia since 1700; worst year {LS['peak_year']}, with {LS['peak_n']:,}."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/world-shipwrecks_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"world-shipwrecks/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        if os.path.exists(os.path.join(ROOT, fn)):
            z.write(os.path.join(ROOT, fn), f"world-shipwrecks/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "world-shipwrecks/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("~", " ")
zmeta = {"title": "Shipwrecks of the World, and How Many over Time: Three Centuries of Recorded Losses",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {BLOG}.</p><p>Data: Wikipedia contributors, Lists of shipwrecks (CC BY-SA 4.0; the derived table is shared under the same licence); Wikidata (CC0), including records imported from Canmore and Coflein; NOAA Office of Coast Survey, AWOIS (public domain); Natural Earth.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["shipwrecks", "maritime history", "Wikipedia", "Lloyd's List", "Wikidata", "AWOIS", "Second World War", "open data", "maps"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://en.wikipedia.org/wiki/Lists_of_shipwrecks", "relation": "isDerivedFrom", "resource_type": "other"},
                                 {"identifier": "https://www.wikidata.org/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://nauticalcharts.noaa.gov/data/wrecks-and-obstructions.html", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
