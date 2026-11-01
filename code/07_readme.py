"""README.md, LICENSE and reddit/post.md, with numbers from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
s, cv, t, ca, gy, an = R["source"], R["coverage"], R["timeline"], R["causes"], R["gy"], R["ancient"]
N = lambda v: f"{round(v):,}"
LS = R["lists"]
readme = f"""# Shipwrecks of the world, and how many over time

{N(LS['n'])} shipwrecks listed on English Wikipedia's "List of shipwrecks" pages, 1700 to 2025, counted year by year by cause and flag, with an honest look at what drives the counts. Plus an interactive map of {N(s['n'])} wrecks with a place, from the Wikipedia lists, Wikidata (including bulk imports from Canmore and Coflein) and NOAA's AWOIS, with a year slider, play button, decade buttons, filters and a sea-depth base map.

Interactive page: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}

## Headline results

- War years: three of the five worst years are war years: {LS['top'][0]['y']} ({N(LS['top'][0]['n'])} wrecks listed, the most of any year), {LS['top'][1]['y']} ({N(LS['top'][1]['n'])}) and {LS['top'][2]['y']} ({N(LS['top'][2]['n'])}). The Second World War averages {N(LS['ww2_avg'])} a year, {LS['ww2_vs_inter']:.1f} times the interwar rate; {LS['war_ww2_pct']:.0f}% of its entries were lost to torpedoes, aircraft, mines or gunfire.
- The 1800s plateau: {LS['c19_pct']:.0f}% of all entries are from the 1800s, averaging {N(LS['high19_avg'])} a year from 1850 to 1879 (peak {N(LS['peak19_n'])} in {LS['peak19_year']}); {LS['c19_aground_pct']:.0f}% of them ran aground. {LS['uk_c19_pct']:.0f}% are British ships, reflecting the British newspapers and Lloyd's List the pages draw on. From 1890 to 1913 the average falls to {N(LS['dip_avg'])} a year.
- Flags: {LS['uk_pct']:.0f}% of all listed wrecks are British; in 1939 to 1945 only {LS['uk_ww2_pct']:.0f}%.
- Map: {N(s['n'])} wrecks with a place; {cv['uk_pct']:.0f}% in UK waters ({cv['scotland_pct']:.0f}% off Scotland), {cv['us_pct']:.0f}% off the United States, {cv['rest_pct']:.0f}% elsewhere; {cv['dated_pct']:.0f}% have a year of loss.
- Before 1700: the ancient-wreck aggregate (Summary Geodatabase of Shipwrecks) peaks in the {an['peak_label']}.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; page data embedded, `data/points.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/wiki_list_wrecks.csv.gz` | The {N(LS['n'])} deduplicated Wikipedia list entries: page, year, decade, month, date heading, ship, flag, flag group, cause bucket, cause group, kind of war loss, coordinates. CC BY-SA 4.0. |
| `data/list_years.csv`, `data/list_decades.csv` | Listed wrecks per year (1700 to 2025, by cause and by flag group) and per decade (by cause). |
| `data/wrecks.csv` | All {N(s['n'])} mapped wrecks: id (Wikidata QID, AWOIS record or WP row), source, name, coordinates, year of loss and how it was found, cause, vessel type, Wikidata types, country or flag, flag group, sitelinks, description, AWOIS least depth (m), nearest country and continent, UK nation, era. |
| `data/graveyards.csv` | Named graveyard boxes with counts. |
| `data/causes.csv`, `data/flags.csv` | Causes of mapped wrecks by source; flags of the other Wikidata wrecks. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/points.json`, `data/site.json`, `data/world.json`, `data/cities.json` | Page data. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures (`paper/`), blog post, figures and meta (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `qa/` | Screenshots of the page at desktop and phone widths. |

## Method in brief

- Wikipedia lists: a table scraped from every "List of shipwrecks" page, 1700 to 2025 ({N(LS['rows'])} rows): {N(LS['dups'])} repeats of the same ship under the same date heading on the same page removed (rows without a ship name kept). Year pages for years with monthly pages hold only "Unknown date" entries, so they do not double count. {LS['decade_only']} decade-page entries without a year count by decade only. Flags grouped across regimes and spellings; causes grouped into seven groups.
- Wikidata: every item with coordinates that is a shipwreck or has a shipwrecking event, via QLever ({N(s['wd_items'])} items, {N(s['wd_mapped'])} mapped), with extra event and date statements for years of loss. NOAA AWOIS: {N(s['awois_kept'])} wrecks in US waters after removing rocks and duplicates. List entries with coordinates are mapped unless they match a mapped wreck of the same name within 20 km.
- Years of loss on the map: Wikidata events and dates, Canmore "Unknown 1830" labels, AWOIS survey notes, the list pages; never inferred from launch years or wars.
- Caveats: the series counts recorded wrecks in a volunteer compilation, weighted to British ships and British sources (Lloyd's List) in the 1800s and thin from the 1890s; compare shapes within periods rather than heights across them. The map is dominated by the Canmore and Coflein imports and by AWOIS.

## How to rerun

Needs Python 3 with numpy, pandas, shapely, pyproj, matplotlib and fontTools, xelatex and pdftotext; node with Playwright for `code/qa.js`. Raw inputs are read in place (paths in `code/common.py`): the Wikipedia list table and Wikidata extracts in `/home/claude/newdata/raw5/`, git clones of https://github.com/jalbertbowden/AWOIS-data and https://github.com/austinw8/ancient_shipwrecks in `/dev/shm/wrecks/gh/` (set `WRECK_GH`), and Natural Earth files in `/home/claude/newdata/raw/geo/`. Intermediate files go to `/dev/shm/wrecks/work` (set `WRECKTMP`).

```
python3 code/01_clean.py        # Wikipedia lists (via lists.py), Wikidata and AWOIS: years, causes, flags, duplicates, nearest land
python3 code/02_geo.py          # outlines and place names
python3 code/03_results.py      # results.json, tables, page data
python3 code/04_build_site.py   # index.html
python3 code/05_figures.py      # header, blog and paper figures
python3 code/06_paper.py        # paper PDF
python3 reddit/collage.py       # collage (annotations and labels checked against bars, land and wrecks)
python3 code/07_readme.py       # README, LICENSE, Reddit post
python3 code/08_release.py      # blog post, Zenodo files
```

## Sources and licences

- Wikipedia contributors, Lists of shipwrecks (https://en.wikipedia.org/wiki/Lists_of_shipwrecks), CC BY-SA 4.0. `data/wiki_list_wrecks.csv.gz` is derived structured data from these pages and is shared under CC BY-SA 4.0.
- Wikidata (https://www.wikidata.org/), CC0, queried with QLever (https://qlever.cs.uni-freiburg.de/). Many records were imported from Canmore, Historic Environment Scotland (https://canmore.org.uk/), and Coflein, Royal Commission on the Ancient and Historical Monuments of Wales (https://coflein.gov.uk/).
- NOAA Office of Coast Survey, Automated Wreck and Obstruction Information System (https://nauticalcharts.noaa.gov/data/wrecks-and-obstructions.html). US Government work, public domain. Copy: https://github.com/jalbertbowden/AWOIS-data.
- Summary Geodatabase of Shipwrecks 1500 BCE to 1500 CE (Harvard Mapping Past Societies, incorporating the Oxford Roman Economy Project shipwrecks database by J. Strauss, after A. J. Parker), copy at https://github.com/austinw8/ancient_shipwrecks. Used only as counts per century.
- Natural Earth countries, admin-1 units and populated places (https://www.naturalearthdata.com/). Public domain.
- Base map tiles on the page: © Esri (World Ocean Base and Reference, Hillshade, Canvas, Imagery).

## Citation

Hotham, T. (2026) Shipwrecks of the world, and how many over time: three centuries of recorded losses. Zenodo. https://doi.org/{DOI}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = """Code (everything in code/ and reddit/collage.py): MIT License

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy,
modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Text, figures and derived data (data/, release/, reddit/*.png, header.png, index.html text): Creative Commons Attribution 4.0
International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/. Attribution: Tristan Hotham (2026).
Exception: data/wiki_list_wrecks.csv.gz is derived from Wikipedia (Wikipedia contributors, CC BY-SA 4.0) and is shared under
CC BY-SA 4.0, https://creativecommons.org/licenses/by-sa/4.0/.

Third-party data: Wikipedia text is CC BY-SA 4.0. Wikidata content is CC0. NOAA AWOIS is a US Government work in the public domain. Natural Earth is public
domain. The Summary Geodatabase of Shipwrecks is not redistributed here; only counts per century derived from it are included.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

post = f"""## Title

[OC] {N(LS['n'])} shipwrecks listed on Wikipedia since 1700, counted year by year: the worst year was {LS['peak_year']}, with {N(LS['peak_n'])}

## Body

Wikipedia has a "List of shipwrecks" page for every month since the 1820s (and every year or decade before). I turned all of them, 1700 to 2025, into one table ({N(LS['n'])} wrecks after removing duplicates) and counted by year, cause and flag. Three of the five worst years are war years ({LS['top'][0]['y']}, {LS['top'][1]['y']}, {LS['top'][2]['y']}); the Second World War averages {LS['ww2_vs_inter']:.0f} times the interwar rate. The big caveat is the 1800s plateau ({N(LS['high19_avg'])} a year in 1850 to 1879, {LS['uk_c19_pct']:.0f}% British ships): the pages lean on British newspapers and Lloyd's List, and the counts drop to {N(LS['dip_avg'])} a year when those sources thin out after the 1880s. So this counts recorded wrecks, not all wrecks. Interactive map of {N(s['n'])} wrecks with a place, with a play button and decade filter: {PAGE}

## Source comment

Sources: Wikipedia contributors, Lists of shipwrecks (CC BY-SA 4.0), as a structured table of every list page 1700 to 2025, deduplicated on page, ship and date; Wikidata (CC0), including records imported from Canmore and Coflein; NOAA Office of Coast Survey, AWOIS (public domain); Natural Earth. Flags grouped across regimes (e.g. German Empire and Nazi Germany as Germany). Chart annotations and map labels were placed by a script that checks they sit on paper or open sea and never cover bars or wreck clusters.

Tools: Python (pandas, shapely, pyproj, matplotlib); Leaflet for the interactive map.

Interactive version: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}
"""
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
for txt in (readme, post, lic):
    for bad in ("—", "–", "--", "DSIT", "DCMS"):
        assert bad not in txt.replace("|---|---|", ""), bad
print("readme, licence, post ok")
