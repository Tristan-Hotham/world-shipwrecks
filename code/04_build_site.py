"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; page data (results, site.json, world.json, cities) is embedded; data/points.json is loaded by the page.
Facts stated in words (page, blog, paper, collage) are checked here. The full-screen map snippet is pasted before </body>."""
import json
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
T, CV, CA, GY = R["timeline"], R["coverage"], R["causes"], R["gy"]
D = pd.read_csv(f"{DATA}/wrecks.csv", low_memory=False, dtype={"country_or_flag": str, "flag_group": str, "uk_nation": str})

# facts stated in words (page, blog, paper, collage)
LS = R["lists"]
assert LS["peak_year"] == 1944 and [t["y"] for t in LS["top"][1:3]] == [1917, 1942] and LS["war_years_in_top5"] == 3
assert LS["peak19_year"] == 1880 and LS["dip_avg"] < LS["high19_avg"] / 4 and LS["inter_avg"] < LS["ww1_avg"]
assert LS["ww2_avg"] > LS["high19_avg"] > LS["ww1_avg"]
L = pd.read_csv(f"{DATA}/wiki_list_wrecks.csv.gz", low_memory=False)
mo = L[L.title.str.match(r"^List of shipwrecks in [A-Z][a-z]+ \d{4}$")]
assert mo.year.min() == 1820                                                                   # "monthly pages from the 1820s"
FL = [f["name"] for f in LS["flags"] if f["name"] not in ("Not recorded", "Other")]
assert FL[:5] == ["United Kingdom", "United States", "Germany", "France", "Norway"]
W2 = {f["name"]: f["ww2"] for f in LS["flags"]}
assert all(W2[k] > 1000 for k in ("Germany", "Japan", "Italy", "Russia and the Soviet Union")) and W2["France"] < 1000
assert R["graveyards"][0]["name"] == "Firth of Clyde" and R["graveyards"][1]["name"] == "Firth of Forth" and R["graveyards"][2]["name"] == "Orkney and Scapa Flow"
assert GY["English Channel"]["main_source"].startswith("Wikipedia") and GY["Truk Lagoon"]["n"] < 50 and GY["Torres Strait"]["n"] < 5
assert [R["oldest"][i]["name"] for i in (0, 1, 3)] == ["Dokos shipwreck", "Uluburun shipwreck", "Antikythera wreck"]
assert R["ancient"]["peak_label"] == "AD 1st century"
assert CV["england"] < CV["scotland"] / 5 and R["coverage"]["uk_pct"] > 50
TY = R["types"]["list"]; assert TY[3]["n"] > TY[2]["n"] > TY[4]["n"]
pts = D[D.source == 4]; assert pts.year.between(1914, 1918).sum() + pts.year.between(1939, 1945).sum() > len(pts) / 2   # "mostly war losses"


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = re.sub(r"\{\{(?!DOI\}\}|BLOG_URL\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), tpl)
    assert "{{" not in html.replace("10.5281/zenodo.23850289", "").replace("https://blog.tristanhotham.com/2026/10/31/world-shipwrecks/", ""), re.findall(r"\{\{[^}]*\}\}", html)[:5]
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*WORLD*/", open(f"{DATA}/world.json", encoding="utf-8").read())
    html = html.replace("/*CITIES*/", J([{"name": x["name"], "lat": x["lat"], "lon": x["lon"], "pop": x["pop"]} for x in jload(f"{DATA}/cities.json")]))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
