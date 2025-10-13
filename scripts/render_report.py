import os, re
from datetime import date

with open('issue_body.md', 'r', encoding='utf-8') as f:
    body = f.read()

def section(title):
    m = re.search(rf"###\s+{re.escape(title)}\n([\s\S]*?)(?=\n###|\Z)", body)
    return (m.group(1).strip() if m else "")

report = [
    "# Begehungsbericht",
    f"**Erstellt:** {date.today().isoformat()}\n",
    "## Zusammenfassung",
    section("Baustelle / Standort"),
    section("Projekt / Bauvorhaben"),
    section("Begehungsart"),
    section("Datum & Uhrzeit"),
    section("Beteiligte"),
    "\n## Checkliste",
    section("PSA & Zutritt"),
    section("Ordnung & Sauberkeit"),
    section("Verkehrswege & Absperrungen"),
    section("Erdarbeiten / Gräben / Wasserbau"),
    section("Gerüste & Leitern"),
    section("Krane & Hebezeuge / Anschlagmittel"),
    section("Maschinen & Geräte (inkl. Teleskopstapler)"),
    section("Elektrik & Beleuchtung"),
    section("Gefahrstoffe / Umweltschutz"),
    "\n## Mängel",
    section("Mängel (Vorlagenfelder 1–5, bei Bedarf nach dem Erstellen kopieren/erweitern)"),
    "\n## Fotos",
    section("Fotos"),
    "\n## Abschluss",
    section("Gesamtbewertung"),
    section("Unterschrift/Name Prüfer"),
]

with open('report.md', 'w', encoding='utf-8') as f:
    f.write("\n\n".join(report))

print("Report markdown written.")