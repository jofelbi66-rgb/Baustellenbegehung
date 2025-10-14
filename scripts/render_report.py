import re
from datetime import date

# Issue-Markdown laden
with open('issue_body.md', 'r', encoding='utf-8') as f:
    body = f.read()

def grab(h):
    m = re.search(rf"^###\s*{re.escape(h)}\s*$\n(.*?)(?:\n###|\Z)", body, flags=re.M|re.S)
    return (m.group(1).strip() if m else "")

def clean(v):
    return re.sub(r"\n+", " ", (v or "")).strip()

# Formular-Felder
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

# Status-Mapping (OK / Mangel / n. a. / Hinweis)
def status_cell(raw: str) -> str:
    s = (raw or "").strip().lower()
    if s in ["ok", "i. o.", "i.o.", "io"]:
        return r"\cellcolor{ok}\textbf{OK}"
    if s in ["mangel", "nicht i. o.", "nicht i.o.", "nicht io", "kritisch"]:
        return r"\cellcolor{fail}\textbf{Mangel}"
    if s in ["hinweis", "auflage"]:
        return r"\cellcolor{warn}\textbf{Hinweis}"
    if s in ["n. a.", "n.a.", "na", "nicht zutreffend"]:
        return r"\cellcolor{na}\textbf{n.\,a.}"
    # Fallback (unbekannt)
    return r"\cellcolor{na}–"

def pair_status_notes(base_label: str):
    s = clean(grab(base_label))
    n = clean(grab(base_label + " – Bemerkungen"))
    return status_cell(s), (n if n else "–")

# Checkliste
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
check_rows = []
for lbl in check_labels:
    sc, notes = pair_status_notes(lbl)
    # Markdown-Tabelle – Status-Feld enthält LaTeX (\cellcolor ...)
    check_rows.append(f"| {lbl} | {sc} | {notes} |")

# Mängel-Tabelle (wie gehabt; optional farbige Schweregrade)
def defect(n):
    sev = clean(grab(f"Mangel {n} – Schweregrad"))
    loc = clean(grab(f"Mangel {n} – Ort/Bereich"))
    desc = clean(grab(f"Mangel {n} – Beschreibung & Maßnahme"))
    owner = clean(grab(f"Mangel {n} – Verantwortlich"))
    due = clean(grab(f"Mangel {n} – Frist \\(YYYY-MM-DD\\)"))
    if not any([sev, loc, desc, owner, due]):
        return ""
    sev_map = {
        "gering": r"\cellcolor{ok}\textbf{gering}",
        "mittel": r"\cellcolor{warn}\textbf{mittel}",
        "hoch": r"\cellcolor{fail}\textbf{hoch}",
        "kritisch": r"\cellcolor{fail}\textbf{kritisch}",
    }
    sev_cell = sev_map.get(sev.lower(), sev or "–")
    return f"| {sev_cell} | {loc or '–'} | {desc or '–'} | {owner or '–'} | {due or '–'} |"

defects = [d for d in (defect(1), defect(2)) if d]

# Bericht zusammenbauen
md = []
md.append("# Begehungsbericht\n")
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
if defects:
    md.append("| Schweregrad | Ort/Bereich | Beschreibung & Maßnahme | Verantwortlich | Frist |")
    md.append("|---|---|---|---|---|")
    md.extend(defects)
else:
    md.append("_Keine Mängel erfasst._")

# Abschluss
md.append("\n## Abschluss")
md.append(f"**Gesamtbewertung:** {overall or '–'}  \n**Prüfer:** {sign or '–'}")

# Pandoc-Frontmatter
front = f"---\ntitle: Baustellenbegehung – {site or 'unbenannt'}\ndate: {date.today().isoformat()}\n---\n\n"
with open('report.md', 'w', encoding='utf-8') as f:
    f.write(front + "\n".join(md))

print("report.md geschrieben.")

