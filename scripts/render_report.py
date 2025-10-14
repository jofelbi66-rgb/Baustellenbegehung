import re
from datetime import date

with open('issue_body.md', 'r', encoding='utf-8') as f:
    body = f.read()

def grab(h):
    m = re.search(rf"^###\s*{re.escape(h)}\s*$\n(.*?)(?:\n###|\Z)", body, flags=re.M|re.S)
    return (m.group(1).strip() if m else "").strip()

def clean(v):
    return re.sub(r"\n+", " ", v).strip()

site    = clean(grab("Baustelle / Standort"))
project = clean(grab("Projekt / Bauvorhaben"))
section = clean(grab("Abschnitt/Bereich"))
coords  = clean(grab("GPS \\(optional\\)"))
kind    = clean(grab("Begehungsart"))
dt      = clean(grab("Datum & Uhrzeit"))
team    = clean(grab("Beteiligte"))
weather = clean(grab("Witterung \\(optional\\)"))

def status_and_notes(base):
    s = clean(grab(base)) or "-"
    n = clean(grab(base + " – Bemerkungen")) or "-"
    return s, n

check_items = [
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
for label in check_items:
    s, n = status_and_notes(label)
    check_rows.append(f"| {label} | {s} | {n} |")

def defect(n):
    sev = clean(grab(f"Mangel {n} – Schweregrad"))
    loc = clean(grab(f"Mangel {n} – Ort/Bereich"))
    desc = clean(grab(f"Mangel {n} – Beschreibung & Maßnahme"))
    owner = clean(grab(f"Mangel {n} – Verantwortlich"))
    due = clean(grab(f"Mangel {n} – Frist \\(YYYY-MM-DD\\)"))
    if any([sev, loc, desc, owner, due]):
        return f"| {sev or '-'} | {loc or '-'} | {desc or '-'} | {owner or '-'} | {due or '-'} |"
    return ""

defects = [d for d in [defect(1), defect(2)] if d]

overall = clean(grab("Gesamtbewertung"))
sign    = clean(grab("Unterschrift/Name Prüfer"))

md = []
md.append(f"# Begehungsbericht\n")
md.append(
    f"**Baustelle:** {site or '-'}  \n"
    f"**Projekt:** {project or '-'}  \n"
    f"**Bereich:** {section or '-'}  \n"
    f"**GPS:** {coords or '-'}  \n"
    f"**Datum & Uhrzeit:** {dt or '-'}  \n"
    f"**Beteiligte:** {team or '-'}  \n"
    f"**Witterung:** {weather or '-'}\n"
)

md.append("## Checkliste")
md.append("| Kategorie | Status | Bemerkungen |")
md.append("|---|---|---|")
md.extend(check_rows)

md.append("\n## Mängel")
if defects:
    md.append("| Schweregrad | Ort/Bereich | Beschreibung & Maßnahme | Verantwortlich | Frist |")
    md.append("|---|---|---|---|---|")
    md.extend(defects)
else:
    md.append("_Keine Mängel erfasst._")

md.append("\n## Abschluss")
md.append(f"**Gesamtbewertung:** {overall or '-'}  \n**Prüfer:** {sign or '-'}")

front = f"---\ntitle: Baustellenbegehung – {site or 'unbenannt'}\ndate: {date.today().isoformat()}\n---\n\n"
with open('report.md', 'w', encoding='utf-8') as f:
    f.write(front + "\n".join(md))

print("report.md geschrieben.")
