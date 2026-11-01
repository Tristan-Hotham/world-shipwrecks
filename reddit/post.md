## Title

[OC] 243,071 shipwrecks listed on Wikipedia since 1700, counted year by year: the worst year was 1944, with 4,570

## Body

Wikipedia has a "List of shipwrecks" page for every month since the 1820s (and every year or decade before). I turned all of them, 1700 to 2025, into one table (243,071 wrecks after removing duplicates) and counted by year, cause and flag. Three of the five worst years are war years (1944, 1917, 1942); the Second World War averages 7 times the interwar rate. The big caveat is the 1800s plateau (2,746 a year in 1850 to 1879, 66% British ships): the pages lean on British newspapers and Lloyd's List, and the counts drop to 483 a year when those sources thin out after the 1880s. So this counts recorded wrecks, not all wrecks. Interactive map of 52,124 wrecks with a place, with a play button and decade filter: https://maps.tristanhotham.com/world-shipwrecks/

## Source comment

Sources: Wikipedia contributors, Lists of shipwrecks (CC BY-SA 4.0), as a structured table of every list page 1700 to 2025, deduplicated on page, ship and date; Wikidata (CC0), including records imported from Canmore and Coflein; NOAA Office of Coast Survey, AWOIS (public domain); Natural Earth. Flags grouped across regimes (e.g. German Empire and Nazi Germany as Germany). Chart annotations and map labels were placed by a script that checks they sit on paper or open sea and never cover bars or wreck clusters.

Tools: Python (pandas, shapely, pyproj, matplotlib); Leaflet for the interactive map.

Interactive version: https://maps.tristanhotham.com/world-shipwrecks/
Paper: https://doi.org/10.5281/zenodo.23850289
Blog post: https://blog.tristanhotham.com/2026/10/31/world-shipwrecks/
