#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
render_report.py
----------------
Liest den Issue-Body (issue_body.md), baut daraus:
  - report.md  (Pandoc-Quelle für PDF, inkl. Fotos je Kategorie)
  - reports/todos.csv (To-Do-Liste der Mängel)

Voraussetzung:
  - Die Issue-Form verwendet exakt die Label-Texte aus baustellenbegehung.yml
  - Workflow schreibt zuvor den Body in 'issue_body.md'
"""

import os
import re
import csv
from datetime import date

INFILE = "issue_body.md"
OUT_MD = "report.md"
OUT_DIR = "reports"
OUT_CSV = os.path.join(OUT_DIR, "todos.csv")


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def read_issue_body() -> str:
    with open(INFILE, "r", encoding="utf-8") as f:
        return f.read()

BODY = read_issue_body()


def grab(header: str) -> str:
    """
    Nimmt die Sektion nach einer Überschrift '### <header>' bis zur nächsten '###' (oder Dateiende).
    Gibt den Inhalt (ohne Überschrift) getrimmt zurück.
    """
    m = re.search(rf"^###\s*{re.escape(header)}\s*$\n(.*?)(?=\n###|\Z)", BODY, flags=re.M | re.S)
    return m.group(1).strip() if m else ""


def clean_one_line(text: str) -> str:
    """Auf eine Zeile reduzieren; Pipes escapen (damit Pipe-Table stabil bleibt)."""
    t = (text or "").strip()
    t = re.sub(r"\s*\n\s*", " ", t)
    t = t.replace("|", r"\|")
    return t


def find_images(text: str):
    """
    Markdown-Bilder: ![alt](url)
    Gibt Liste der URLs zurück.
    """
    return re.findall(r'!\[[^\]]*]\(([^)]+)\)', text or "")


def norm(v: str) -> str:
    return (v or "").strip().lower()


# ---------------------------------------------------------------------------
# Stammdaten / Kopf
# ---------------------------------------------------------------------------

ORT   = clean_one_line(grab("Ort / Baustelle"))
DATUM = clean_one_line(grab("Datum"))
SIFA  = clean_one_line(grab("Sifa / Ersteller"))
WETTER = clean_one_line(grab("Wetterbedingungen"))

if not DATUM:
    DATUM = date.today().isoformat()


# ---------------------------------------------------------------------------
# Checkliste + Fotos
# ---------------------------------------------------------------------------

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

# Mapping Bemerkungen-/Foto-Felder (müssen exakt den Labeln aus der Vorlage entsprechen)
remark_label_of = {
    "PSA & Zutritt": "PSA & Zutritt – Bemerkungen",
    "Ordnung & Sauberkeit": "Ordnung & Sauberkeit – Bemerkungen",
    "Verkehrswege & Absperrungen": "Verkehrswege & Absperrungen – Bemerkungen",
    "Erdarbeiten / Gräben / Wasserbau": "Erdarbeiten / Gräben / Wasserbau – Bemerkungen",
    "Gerüste & Leitern": "Gerüste & Leitern – Bemerkungen",
    "Krane & Hebezeuge / Anschlagmittel": "Krane & Hebezeuge / Anschlagmittel – Bemerkungen",
    "Maschinen & Geräte (inkl. Teleskopstapler)": "Maschinen & Geräte (inkl. Teleskopstapler) – Bemerkungen",
    "Elektrik & Beleuchtung": "Elektrik & Beleuchtung – Bemerkungen",
    "Gefahrstoffe / Umweltschutz": "Gefahrstoffe / Umweltschutz – Bemerkungen",
}

photo_label_of = {
    "PSA & Zutritt": "PSA & Zutritt – Fotos/Nachweise",
    "Ordnung & Sauberkeit": "Ordnung & Sauberkeit – Fotos/Nachweise",
    "Verkehrswege & Absperrungen": "Verkehrswege & Absperrungen – Fotos/Nachweise",
    "Erdarbeiten / Gräben / Wasserbau": "Erdarbeiten / Gräben / Wasserbau – Fotos/Nachweise",
    "Gerüste & Leitern": "Gerüste & Leitern – Fotos/Nachweise",
    "Krane & Hebezeuge / Anschlagmittel": "Krane & Hebezeuge / Anschlagmittel – Fotos/Nachweise",
    "Maschinen & Geräte (inkl. Teleskopstapler)": "Maschinen & Geräte (inkl. Teleskopstapler) – Fotos/Nachweise",
    "Elektrik & Beleuchtung": "Elektrik & Beleuchtung – Fotos/Nachweise",
    "Gefahrstoffe / Umweltschutz": "Gefahrstoffe / Umweltschutz – Fotos/Nachweise",
}


def status_cell(val: str) -> str:
    """
    Gibt Zelle mit Roh-TeX zurück, damit Pandoc/LaTeX einfärben kann.
    Erwartete Synonyme:
      ok → grün
      hinweis / mittel → gelb
      mangel / hoch / kritisch → rot
      na / n.a. / nicht zutreffend / - → grau (na)
    """
    v = norm(val)
    if v in ("ok", "i.o.", "io"):
        return r"\cellcolor{ok}\textbf{OK}"
    if v in ("hinweis", "mittel", "warnung", "warn"):
        return r"\cellcolor{warn} Hinweis"
    if v in ("mangel", "hoch", "kritisch"):
        return r"\cellcolor{fail}\textbf{Mangel}"
    if v in ("na", "n.a.", "nicht zutreffend", "-", "k.a.", "ka", "keine angabe"):
        return r"\cellcolor{na} n.\,a."
    # Fallback: roher Text (ohne Farbe)
    return clean_one_line(val)


def build_checklist_table() -> str:
    """
    Erstellt die Pipe-Table (Kategorie | Status | Bemerkungen) inkl. Header.
    """
    lines = []
    lines.append("**Legende:** (\\cellcolor{ok} OK) (\\cellcolor{warn} Hinweis) (\\cellcolor{fail} Mangel) (\\cellcolor{na} n.,a.)\n")
    lines.append("### 1.1 Checkliste\n")
    lines.append("| Kategorie | Status | Bemerkungen |")
    lines.append("|---|---:|---|")

    for label in check_labels:
        status = clean_one_line(grab(label))
        remark = clean_one_line(grab(remark_label_of[label]))
        cell = status_cell(status or "")
        if not remark:
            remark = "–"
        lines.append(f"| {label} | {cell} | {remark} |")

    return "\n".join(lines)


def build_check_photos_blocks() -> str:
    """
    Fügt nach der Tabelle je Kategorie einen Fotoblock an (falls Bilder vorhanden).
    Zwei Bilder pro Zeile, skaliert auf 48% Breite.
    """
    blocks = []
    for label in check_labels:
        phototext = grab(photo_label_of[label])
        imgs = find_images(phototext)
        if not imgs:
            continue
        blocks.append(f"#### {label} – Fotos\n")
        row = []
        for i, url in enumerate(imgs, 1):
            row.append(f"![]({url}){{ width=48% }}")
            if i % 2 == 0:
                blocks.append(" ".join(row))
                row = []
        if row:
            blocks.append(" ".join(row))
        blocks.append("")  # Leerzeile
    return "\n".join(blocks)


# ---------------------------------------------------------------------------
# Mängel + ToDo-CSV
# ---------------------------------------------------------------------------

def build_maengel_and_csv() -> str:
    """
    Liest Mängel 1..10 (anpassbar) und schreibt eine Tabelle in den Bericht
    + CSV (reports/todos.csv) mit Verantwortlichen & Fristen.
    """
    os.makedirs(OUT_DIR, exist_ok=True)

    fields = [
        ("Schweregrad",   "schweregrad"),
        ("Ort/Bereich",   "ortbereich"),
        ("Beschreibung & Maßnahme", "beschreibung"),
        ("Verantwortlich", "verantwortlich"),
        ("Frist (YYYY-MM-DD)", "frist"),
    ]

    # CSV vorbereiten
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as cf:
        cw = csv.writer(cf, delimiter=";")
        cw.writerow(["Nr", "Schweregrad", "Ort/Bereich", "Beschreibung/Maßnahme", "Verantwortlich", "Frist"])

        lines = []
        lines.append("## 1.2 Mängel\n")
        lines.append("| Nr. | Schweregrad | Ort/Bereich | Beschreibung / Maßnahme | Verantwortlich | Frist |")
        lines.append("|---:|---|---|---|---|---|")

        row_added = False
        for i in range(1, 11):  # bis 10 Mängel
            # Headertexte gemäß Issue-Template:
            sv = clean_one_line(grab(f"Mangel {i} – Schweregrad"))
            ob = clean_one_line(grab(f"Mangel {i} – Ort/Bereich"))
            bm = clean_one_line(grab(f"Mangel {i} – Beschreibung & Maßnahme"))
            vf = clean_one_line(grab(f"Mangel {i} – Verantwortlich"))
            fr = clean_one_line(grab(f"Mangel {i} – Frist (YYYY-MM-DD)"))

            # Falls gar nichts gefüllt ist → überspringen
            if not any([sv, ob, bm, vf, fr]):
                continue

            row_added = True
            lines.append(f"| {i} | {sv or '–'} | {ob or '–'} | {bm or '–'} | {vf or '–'} | {fr or '–'} |")
            cw.writerow([i, sv, ob, bm, vf, fr])

        if not row_added:
            lines.append("| – | – | – | – | – | – |")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Bericht zusammenbauen
# ---------------------------------------------------------------------------

def build_markdown() -> str:
    md = []
    md.append(f"# Baustellenbegehung\n")
    md.append(f"**Ort:** {ORT or '–'}  \n**Datum:** {DATUM or '–'}  \n**Sifa/Ersteller:** {SIFA or '–'}")
    if WETTER:
        md.append(f"  \n**Wetter:** {WETTER}")
    md.append("\n")

    # Checkliste
    md.append(build_checklist_table())
    md.append("\n")
    md.append(build_check_photos_blocks())
    md.append("\n")

    # Mängel + CSV
    md.append(build_maengel_and_csv())

    return "\n".join(md)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    md = build_markdown()
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Wrote {OUT_MD} and {OUT_CSV}")


if __name__ == "__main__":
    main()



