# Shipwrecks of the world, and how many over time

243,071 shipwrecks listed on English Wikipedia's "List of shipwrecks" pages, 1700 to 2025, counted year by year by cause and flag, with an honest look at what drives the counts. Plus an interactive map of 52,124 wrecks with a place, from the Wikipedia lists, Wikidata (including bulk imports from Canmore and Coflein) and NOAA's AWOIS, with a year slider, play button, decade buttons, filters and a sea-depth base map.

Interactive page: https://maps.tristanhotham.com/world-shipwrecks/
Paper: https://doi.org/10.5281/zenodo.23850289
Blog post: https://blog.tristanhotham.com/2026/10/31/world-shipwrecks/

## Headline results

- War years: three of the five worst years are war years: 1944 (4,570 wrecks listed, the most of any year), 1917 (4,083) and 1942 (4,027). The Second World War averages 3,044 a year, 6.9 times the interwar rate; 69% of its entries were lost to torpedoes, aircraft, mines or gunfire.
- The 1800s plateau: 71% of all entries are from the 1800s, averaging 2,746 a year from 1850 to 1879 (peak 3,794 in 1880); 65% of them ran aground. 66% are British ships, reflecting the British newspapers and Lloyd's List the pages draw on. From 1890 to 1913 the average falls to 483 a year.
- Flags: 56% of all listed wrecks are British; in 1939 to 1945 only 24%.
- Map: 52,124 wrecks with a place; 61% in UK waters (45% off Scotland), 16% off the United States, 23% elsewhere; 36% have a year of loss.
- Before 1700: the ancient-wreck aggregate (Summary Geodatabase of Shipwrecks) peaks in the AD 1st century.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; page data embedded, `data/points.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/wiki_list_wrecks.csv.gz` | The 243,071 deduplicated Wikipedia list entries: page, year, decade, month, date heading, ship, flag, flag group, cause bucket, cause group, kind of war loss, coordinates. CC BY-SA 4.0. |
| `data/list_years.csv`, `data/list_decades.csv` | Listed wrecks per year (1700 to 2025, by cause and by flag group) and per decade (by cause). |
| `data/wrecks.csv` | All 52,124 mapped wrecks: id (Wikidata QID, AWOIS record or WP row), source, name, coordinates, year of loss and how it was found, cause, vessel type, Wikidata types, country or flag, flag group, sitelinks, description, AWOIS least depth (m), nearest country and continent, UK nation, era. |
| `data/graveyards.csv` | Named graveyard boxes with counts. |
| `data/causes.csv`, `data/flags.csv` | Causes of mapped wrecks by source; flags of the other Wikidata wrecks. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/points.json`, `data/site.json`, `data/world.json`, `data/cities.json` | Page data. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures (`paper/`), blog post, figures and meta (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `qa/` | Screenshots of the page at desktop and phone widths. |

## Method in brief

- Wikipedia lists: a table scraped from every "List of shipwrecks" page, 1700 to 2025 (252,288 rows): 9,217 repeats of the same ship under the same date heading on the same page removed (rows without a ship name kept). Year pages for years with monthly pages hold only "Unknown date" entries, so they do not double count. 516 decade-page entries without a year count by decade only. Flags grouped across regimes and spellings; causes grouped into seven groups.
- Wikidata: every item with coordinates that is a shipwreck or has a shipwrecking event, via QLever (30,940 items, 30,821 mapped), with extra event and date statements for years of loss. NOAA AWOIS: 6,170 wrecks in US waters after removing rocks and duplicates. List entries with coordinates are mapped unless they match a mapped wreck of the same name within 20 km.
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

Hotham, T. (2026) Shipwrecks of the world, and how many over time: three centuries of recorded losses. Zenodo. https://doi.org/10.5281/zenodo.23850289

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
