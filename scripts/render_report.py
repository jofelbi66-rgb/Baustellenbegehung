import re, csv, os
from datetime import date

# ---------- Helpers ----------
def read_issue_body() -> str:
    with open('issue_body.md', 'r', encoding='utf-8') as f:
        return f.read()

BODY = read_issue_body()

def grab(header: str) -> str:
    # Abschnitt nach "### <Header>" holen
    m = re.search(rf"^###\s*{re.escape(header)}\s*$\n(.*?)(?:\n###|\Z)", BODY, flags=re.M|re.S)
    return (m.group(1).strip() if m else "")

def clean(v: str) -> str:
    return re.sub(r"\n+", " ", (v or "")).strip()

# ---------- Formular-Felder ----------
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

# ---------- Status-Mapping ----------
def normalize_status(raw: str) -> str:
    s = (raw or "").strip().lower()
    if s in ["ok","i. o.","i.o.","io","in ordnung"]: return "ok"
    if s in ["hinweis","auflage","mittel"]: return "warn"
    if s in ["mangel","nicht i. o.","nicht i.o.","nicht io","hoch","kritisch"]: return "fail"
    if s in ["n. a.","n.a.","na","nicht zutreffend","-","–",""]: return "na"
    return "na"

def status_cell(raw: str) -> str:
    st   = normalize_status(raw)
    text = {"ok":"OK","warn":"Hinweis","fail":"Mangel","na":"n.\\,a."}[st]
    col  = {"ok":"ok","warn":"warn","fail":"fail","na":"na"}[st]
    return rf"\cellcolor{{{col}}}\textbf{{{text}}}"

# ---------- Checkliste ----------
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
for L in check_labels:
    s = clean(grab(L))
    n = clean(grab(L + " – Bemerkungen"))
    check_rows.append(f"| {L} | {status_cell(s)} | {n or '–'} |")

# ---------- Mängel (ToDo-CSV) ----------
def defect(n: int):
    sev = clean(grab(f"Mangel {n} – Schweregrad"))
    loc = clean(grab(f"Mangel {n} – Ort/Bereich"))
    desc= clean(grab(f"Mangel {n} – Beschreibung & Maßnahme"))
    owner=clean(grab(f"Mangel {n} – Verantwortlich"))
    due = clean(grab(f"Mangel {n} – Frist \\(YYYY-MM-DD\\)"))
    if any([sev, loc, desc, owner, due]):
        return (sev, loc, desc, owner, due)
    return None

defects = []
for i in range(1, 6):   # bei Bedarf erhöhen
    d = defect(i)
    if d: defects.append(d)

os.makedirs("reports", exist_ok=True)
with open("reports/todos.csv","w",newline="",encoding="utf-8") as f:
    w = csv.writer(f, delimiter=';')
    w.writerow(["Baustelle","Schweregrad","Ort/Bereich","Beschreibung/Maßnahme","Verantwortlich","Frist"])
    for sev,loc,desc,owner,due in defects:
        w.writerow([site or "", sev or "", loc or "", desc or "", owner or "", due or ""])

# ---------- Markdown-Bericht ----------
md = []
md.append("# Begehungsbericht\n")

# Lage/Kopf
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

# Legende schlicht (keine LaTeX-Boxen -> 100% sicher)
md.append("> **Legende:** ✅ OK · ⚠️ Hinweis · ❌ Mangel · ☐ n. a.")

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
    sev_map = {
        "gering":  r"\cellcolor{ok}\textbf{gering}",
        "mittel":  r"\cellcolor{warn}\textbf{mittel}",
        "hoch":    r"\cellcolor{fail}\textbf{hoch}",
        "kritisch":r"\cellcolor{fail}\textbf{kritisch}",
    }
    for sev, loc, desc, owner, due in defects:
        sev_cell = sev_map.get((sev or "").lower(), sev or "–")
        md.append(f"| {sev_cell} | {loc or '–'} | {desc or '–'} | {owner or '–'} | {due or '–'} |")
else:
    md.append("_Keine Mängel erfasst._")

# Abschluss
md.append("\n## Abschluss")
md.append(f"**Gesamtbewertung:** {overall or '–'}  \n**Prüfer:** {sign or '–'}")

front = f"---\ntitle: Baustellenbegehung – {site or 'unbenannt'}\ndate: {date.today().isoformat()}\n---\n\n"
with open('report.md','w',encoding='utf-8') as f:
    f.write(front + "\n".join(md))

print("report.md und reports/todos.csv geschrieben.")



