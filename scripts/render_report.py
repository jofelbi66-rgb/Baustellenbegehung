import re
from datetime import date

# --- Util ---------------------------------------------------------------
def read_issue_body():
    with open('issue_body.md', 'r', encoding='utf-8') as f:
        return f.read()

BODY = read_issue_body()

def grab(h):
    m = re.search(rf"^###\s*{re.escape(h)}\s*$\n(.*?)(?:\n###|\Z)", BODY, flags=re.M|re.S)
    return (m.group(1).strip() if m else "")

def clean(v):
    return re.sub(r"\n+", " ", (v or "")).strip()

# Normierter Status (für Ampel-Logik)
def normalize_status(raw: str) -> str:
    s = (raw or "").strip().lower()
    if s in ["ok", "i. o.", "i.o.", "io", "in ordnung"]:
        return "ok"
    if s in ["mangel", "nicht i. o.", "nicht i.o.", "nicht io", "hoch", "kritisch"]:
        return "fail"
    if s in ["hinweis", "auflage", "mittel"]:
        return "warn"
    if s in ["n. a.", "n.a.", "na", "nicht zutreffend"]:
        return "na"
    return "na"

# farbige Zelle für Tabellen
def status_cell(raw: str) -> str:
    st = normalize_status(raw)
    text = {"ok":"OK","warn":"Hinweis","fail":"Mangel","na":"n.\\,a."}[st]
    color = {"ok":"ok","warn":"warn","fail":"fail","na":"na"}[st]
    return rf"\cellcolor{{{color}}}\textbf{{{text}}}"

# --- Felder -------------------------------------------------------------
site    = clean(grab("Baustelle / Standort"))
project = clean(grab("Projekt / Bauvorhaben"))
section = clean(grab("Abschnitt/Bereich"))
coords  = clean(grab("GPS \\(optional\\)"))
kind    = clean(grab("Begehungsart"))
dt      = clean(grab("Datum & Uhrzeit"))
team    = clean(grab("Beteiligte"))
weather = clean(grab("Witterung \\(optional\\)"))
overall = clean(grab("Gesamtbewertung"))
sign    = clean(grab("Unterschrift/Name Prüfer"))

# --- Checkliste ---------------------------------------------------------
check_labels = [
    "PSA & Zutritt",
    "Ordnung & Sauberkeit",
    "Verkehrswege & Absperrungen",
    "Erdarbeiten / Gräben / Wasserbau",
    "Gerüste & Leitern",
    "Krane & Hebezeuge / Anschlagmittel",
    "Maschinen & Geräte (inkl. Teleskopstapler)",
    "Elektrik & Beleuchtung",
    "Gefahrstoffe / Umweltschutz",
]

status_list = []   # für Ampel
check_rows = []

for lbl in check_labels:
    s_raw = clean(grab(lbl))
    n     = clean(grab(lbl + " – Bemerkungen"))
    status_list.append(normalize_status(s_raw))
    check_rows.append(f"| {lbl} | {status_cell(s_raw)} | {n or '–'} |")

# --- Mängel (optional in Ampel berücksichtigen) -------------------------
defect_rows = []
def worst_with_defect(st_current: str, sev: str) -> str:
    """sehr grob: hoch/kritisch => fail, mittel => warn, gering => ok/warn bleibt"""
    sev = (sev or "").strip().lower()
    if sev in ["hoch", "kritisch"]:
        return "fail"
    if sev in ["mittel"]:
        return "warn" if st_current != "fail" else "fail"
    return st_current

for i in (1, 2):
    sev = clean(grab(f"Mangel {i} – Schweregrad"))
    loc = clean(grab(f"Mangel {i} – Ort/Bereich"))
    desc= clean(grab(f"Mangel {i} – Beschreibung & Maßnahme"))
    owner=clean(grab(f"Mangel {i} – Verantwortlich"))
    due = clean(grab(f"Mangel {i} – Frist \\(YYYY-MM-DD\\)"))
    if any([sev, loc, desc, owner, due]):
        sev_map = {
            "gering":  r"\cellcolor{ok}\textbf{gering}",
            "mittel":  r"\cellcolor{warn}\textbf{mittel}",
            "hoch":    r"\cellcolor{fail}\textbf{hoch}",
            "kritisch":r"\cellcolor{fail}\textbf{kritisch}",
        }
        sev_cell = sev_map.get(sev.lower(), sev or "–")
        defect_rows.append(f"| {sev_cell} | {loc or '–'} | {desc or '–'} | {owner or '–'} | {due or '–'} |")
        # Ampel verschärfen
        status_list.append(worst_with_defect("ok", sev))

# --- Ampel „Status Gesamt“ ---------------------------------------------
# Reihenfolge: fail > warn > ok ; 'na' zählt nicht
rank = {"fail":3, "warn":2, "ok":1, "na":0}
worst = "ok"
for st in status_list:
    if rank.get(st,0) > rank.get(worst,0):
        worst = st

bar_text = {
    "fail": "GESAMT: MANGEL",
    "warn": "GESAMT: HINWEIS/AUFLAGEN",
    "ok":   "GESAMT: I. O.",
    "na":   "GESAMT: n. a.",
}[worst]
bar_color = {"fail":"fail", "warn":"warn", "ok":"ok", "na":"na"}[worst]
status_bar = rf"\begin{{center}}\colorbox{{{bar_color}}}{{\rule{{0pt}}{{14pt}}\hspace{{8pt}}\textbf{{{bar_text}}}\hspace{{8pt}}}}\end{{center}}"

# --- Bericht aufbauen ---------------------------------------------------
md = []
md.append("# Begehungsbericht\n")
md.append(status_bar + "\n")  # Ampel unter den Titel

md.append(
    f"**Baustelle:** {site or '–'}  \n"
    f"**Projekt:** {project or '–'}  \n"
    f"**Bereich:** {section or '–'}  \n"
    f"**GPS:** {coords or '–'}  \n"
    f"**Begehungsart:** {kind or '–'}  \n"
    f"**Datum & Uhrzeit:** {dt or '–'}  \n"
    f"**Beteiligte:** {team or '–'}  \n"
    f"**Witterung:** {weather or '–'}\n"
)

# Legende
md.append("> **Legende:** \\(\\cellcolor{ok} OK\\)  \\(\\cellcolor{warn} Hinweis\\)  \\(\\cellcolor{fail} Mangel\\)  \\(\\cellcolor{na} n.\\,a.\\)")

# Checkliste
md.append("\n## Checkliste")
md.append("| Kategorie | Status | Bemerkungen |")
md.append("|---|---|---|")
md.extend(check_rows)

# Mängel
md.append("\n## Mängel")
if defect_rows:
    md.append("| Schweregrad | Ort/Bereich | Beschreibung & Maßnahme | Verantwortlich | Frist |")
    md.append("|---|---|---|---|---|")
    md.extend(defect_rows)
else:
    md.append("_Keine Mängel erfasst._")

# Abschluss
overall_line = f"**Gesamtbewertung (Form):** {overall or '–'}"
md.append("\n## Abschluss")
md.append(f"{overall_line}  \n**Prüfer:** {sign or '–'}")

# Frontmatter
front = f"---\ntitle: Baustellenbegehung – {site or 'unbenannt'}\ndate: {date.today().isoformat()}\n---\n\n"
with open('report.md', 'w', encoding='utf-8') as f:
    f.write(front + "\n".join(md))

print("report.md geschrieben.")

