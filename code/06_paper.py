"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/<NAME>.pdf and .tex (figures f_*.png sit beside them). The DOI stays a placeholder."""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Shipwrecks_of_the_World"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")

# checks for statements made in words in the paper only
LS = R["lists"]
assert R["coverage"]["methods"][0]["m"] == "Wikipedia list page"
assert [f["name"] for f in LS["flags"] if f["name"] not in ("Not recorded", "Other")][:5] == ["United Kingdom", "United States", "Germany", "France", "Norway"]
C = LS["causes"]; assert C[2]["n"] > C[1]["n"] > C[0]["n"] > C[3]["n"] > C[4]["n"] > C[5]["n"]


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "pc1": return f"{float(v):.1f}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "yr": return f"{-int(v)}~BC" if int(v) < 0 else str(int(v))
    return tex(str(v))


yr = lambda y: f"{-y}~BC" if y < 0 else str(y)
rows = "".join(f"{t['y']} & {t['n']:,}\\\\\n" for t in LS["top"])
TT = ("\\begin{table}[tbp]\\centering\\small\\caption{The ten years with most shipwrecks listed on Wikipedia.}\\label{tab:top}"
      "\\begin{tabular}{rr}\\toprule Year & Wrecks listed\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(f['name'])} & {f['n']:,} & {f['pct']:.1f}\\% & {f['ww2']:,}\\\\\n" for f in LS["flags"][:16])
TF = ("\\begin{table}[tbp]\\centering\\small\\caption{Listed wrecks by flag group, 1700 to 2025, and in 1939 to 1945.}\\label{tab:flags}"
      "\\begin{tabular}{lrrr}\\toprule Flag & Wrecks & Share & 1939 to 1945\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(m['m'])} & {m['n']:,}\\\\\n" for m in R["coverage"]["methods"])
TM = ("\\begin{table}[tbp]\\centering\\small\\caption{Where the years of loss come from (first source that applies).}\\label{tab:methods}"
      "\\begin{tabular}{lr}\\toprule Source of the year & Wrecks\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(o['name'])} & {yr(o['y'])} & {tex(o['where'])} & {tex(o['how'])}\\\\\n" for o in R["oldest"])
TO = ("\\begin{table}[tbp]\\centering\\small\\caption{The oldest dated wrecks in the combined record.}\\label{tab:oldest}"
      "\\begin{tabular}{p{4.2cm}rp{3.2cm}p{5.2cm}}\\toprule Wreck & Year & Nearest land & Year from\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(g['name'])} & {tex(g['where'])} & {g['n']:,} & {g['dated']:,} & {g['ww']:,}\\\\\n" for g in R["graveyards"])
TG = ("\\begin{table}[tbp]\\centering\\small\\caption{Wrecks in named graveyards (simple boxes). WW: dated to 1914 to 1918 or 1939 to 1945.}\\label{tab:gy}"
      "\\begin{tabular}{llrrr}\\toprule Area & Where & Wrecks & Dated & WW\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = t.replace("{{meta.doi}}", "@@DOI@@")
t = re.sub(r"\{\{(?!TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
for k, v in (("TOP", TT), ("FLAGS", TF), ("METHODS", TM), ("OLDEST", TO), ("GY", TG)):
    t = t.replace("{{TABLE_%s}}" % k, v)
assert "{{" not in t and "--" not in t and "\u2014" not in t and "\u2013" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:3]
t = t.replace("\\href{https://doi.org/@@DOI@@}{https://doi.org/@@DOI@@}", "https://doi.org/\\{\\{DOI\\}\\}")
t = t.replace("\\url{https://doi.org/@@DOI@@}", "https://doi.org/\\{\\{DOI\\}\\}")
assert "@@" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013") + txt.count("--"))
