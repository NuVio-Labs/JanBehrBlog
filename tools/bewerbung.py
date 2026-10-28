#!/usr/bin/env python3
"""Bereitet die Bewerbungsunterlagen fuer die Seite unter /cv auf.

Aufruf:  python tools/bewerbung.py

Quelle:  CV/Jan_Behr/Bewerbung Online/
Ziel:    api/_quelle/klar/  (lokal, nicht im Repository)

Danach verschluesselt "node tools/verschluesseln.js" die Dateien nach
api/_quelle/*.bin. Nur diese Chiffrate liegen im Repository, das oeffentlich
ist; die Funktion entschluesselt sie beim Abruf.

Was passiert:
  Anschreiben    orange SIGN-Fahne des Signierwerkzeugs entfernt
  Lebenslauf     Datumszeile entfernt
  alle           aussagekraeftige Dokumenteigenschaften
  zusaetzlich    Gesamtdatei aus den drei Seiten
  Schriften      Datumsschriften fuer die Funktion bereitgestellt

Die Datumszeilen setzt api/cv.js beim Abruf, damit heruntergeladene
Unterlagen nie veraltet wirken. Die eingebetteten Schriften taugen dafuer
nicht durchgaengig: Calibri-Italic im Lebenslauf fehlen die Ziffern 3, 4, 8
und 9. Deshalb liegt Carlito-Italic bei, das metrisch mit Calibri
uebereinstimmt. Fuer das Anschreiben reicht der Aptos-Subset aus dem PDF
selbst, er enthaelt alle Ziffern.
"""

import os
import re
import shutil
import sys
from collections import Counter

import fitz

QUELLE = "CV/Jan_Behr/Bewerbung Online"
ZIEL = "api/_quelle/klar"
SCHRIFTEN = "api/_quelle/schriften"

ANSCHREIBEN = "Anschreiben.pdf"
LEBENSLAUF = "Lebenslauf_Jan_Behr.pdf"
BESCHEINIGUNG = "Bescheinigung Praktikumsgeber IT_Pflichtpraktika.pdf"

DATUMSZEILE = "Gladbeck, 27. Oktober 2026"

EIGENSCHAFTEN = {
    "anschreiben.pdf": (
        "Bewerbungsanschreiben Umschulungspraktikum – Jan Behr",
        "Anschreiben für das Pflichtpraktikum vom 15. März bis 2. Juli 2027",
    ),
    "lebenslauf.pdf": (
        "Lebenslauf – Jan Behr",
        "Werdegang, Qualifikationen und IT-Kenntnisse",
    ),
    "bescheinigung.pdf": (
        "Bescheinigung für den Praktikumsgeber – BFW Oberhausen",
        "Rahmenbedingungen des Pflichtpraktikums im Rahmen der Umschulung",
    ),
    "bewerbung-komplett.pdf": (
        "Bewerbung Umschulungspraktikum Fachinformatiker Systemintegration – Jan Behr",
        "Anschreiben, Lebenslauf und Bescheinigung des BFW Oberhausen",
    ),
}


def eigenschaften_setzen(doc, dateiname):
    titel, thema = EIGENSCHAFTEN[dateiname]
    doc.set_metadata({
        "title": titel,
        "author": "Jan Behr",
        "subject": thema,
        "keywords": "",
        "creator": "",
        "producer": "",
    })


def band(span, groesse):
    """Schmales Band um die x-Hoehe einer Zeile.

    Ein Rechteck ueber die volle Zeilenhoehe wuerde Nachbarzeilen mitloeschen,
    weil sich deren Metrikrahmen beruehren.
    """
    grund = span["origin"][1]
    return fitz.Rect(
        span["bbox"][0] - 0.5,
        grund - 0.70 * groesse,
        span["bbox"][2] + 0.5,
        grund + 0.20 * groesse,
    )


def span_suchen(seite, text):
    for block in seite.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                if span["text"].strip() == text:
                    return span
    return None


def sign_fahne_entfernen(doc):
    """Entfernt die orange Fahne, die macOS Preview hinterlassen hat.

    Sie stammt aus einem leeren Signaturfeld (/FT /Sig mit
    AAPL:isSignatureMarker), nicht aus dem Seiteninhalt. Deshalb hilft hier
    keine Schwaerzung, sondern nur das Loeschen des Formularfeldes. Die
    Unterschrift selbst liegt als Bild im Seiteninhalt und bleibt erhalten.
    """
    seite = doc[0]
    felder = list(seite.widgets())
    if not felder:
        sys.exit("kein Signaturfeld gefunden")
    bilder_vorher = len(seite.get_images())
    for feld in felder:
        seite.delete_widget(feld)

    if "SIGN" in seite.get_text():
        sys.exit("die SIGN-Markierung steht noch im Text")
    if len(seite.get_images()) != bilder_vorher:
        sys.exit("die Unterschrift ist mit verschwunden")
    print("  Signaturfeld entfernt (%d), Unterschrift unberuehrt"
          % len(felder))


def datumszeile_entfernen(doc):
    """Nimmt die feste Datumszeile aus dem Lebenslauf."""
    seite = doc[0]
    span = span_suchen(seite, DATUMSZEILE)
    if span is None:
        sys.exit("Datumszeile nicht gefunden")

    vorher = Counter(seite.get_text().split())
    seite.add_redact_annot(band(span, span["size"]), fill=None)
    seite.apply_redactions(
        images=fitz.PDF_REDACT_IMAGE_NONE,
        graphics=fitz.PDF_REDACT_LINE_ART_NONE,
    )
    entfernt = vorher - Counter(seite.get_text().split())
    if entfernt != Counter(DATUMSZEILE.split()):
        sys.exit("es wurde mehr oder weniger entfernt: %r" % dict(entfernt))
    print("  Datumszeile entfernt:", DATUMSZEILE)
    print("  Position fuer die Funktion: x %.2f, Grundlinie %.2f, Groesse %.2f"
          % (span["origin"][0], span["origin"][1], span["size"]))


def schrift_aus_pdf(doc, name, ziel):
    """Holt einen eingebetteten Schriftsubset als Datei heraus."""
    for xref in range(1, doc.xref_length()):
        try:
            obj = doc.xref_object(xref, compressed=False)
        except Exception:
            continue
        if "/FontDescriptor" not in obj or name not in obj or "/FontFile" not in obj:
            continue
        treffer = re.search(r"/FontFile\d? (\d+) 0 R", obj)
        if not treffer:
            continue
        daten = doc.xref_stream(int(treffer.group(1)))
        pruef = fitz.Font(fontbuffer=daten)
        fehlend = [c for c in "0123456789., " if not pruef.has_glyph(ord(c))]
        if fehlend:
            continue
        with open(ziel, "wb") as datei:
            datei.write(daten)
        print("  Schrift %s: %d Bytes, alle Ziffern vorhanden" % (name, len(daten)))
        return True
    return False


def main():
    if not os.path.isdir(QUELLE):
        sys.exit("Quellordner fehlt: %s" % QUELLE)
    os.makedirs(SCHRIFTEN, exist_ok=True)

    print("Anschreiben")
    brief = fitz.open(os.path.join(QUELLE, ANSCHREIBEN))
    sign_fahne_entfernen(brief)
    if not schrift_aus_pdf(brief, "Aptos", os.path.join(SCHRIFTEN, "aptos-datum.ttf")):
        sys.exit("kein Aptos-Subset mit vollstaendigen Ziffern gefunden")
    eigenschaften_setzen(brief, "anschreiben.pdf")
    brief.save(os.path.join(ZIEL, "anschreiben.pdf"), garbage=4, deflate=True)

    print("Lebenslauf")
    lebenslauf = fitz.open(os.path.join(QUELLE, LEBENSLAUF))
    datumszeile_entfernen(lebenslauf)
    eigenschaften_setzen(lebenslauf, "lebenslauf.pdf")
    lebenslauf.save(os.path.join(ZIEL, "lebenslauf.pdf"), garbage=4, deflate=True)

    print("Bescheinigung")
    bescheinigung = fitz.open(os.path.join(QUELLE, BESCHEINIGUNG))
    eigenschaften_setzen(bescheinigung, "bescheinigung.pdf")
    bescheinigung.save(os.path.join(ZIEL, "bescheinigung.pdf"), garbage=4, deflate=True)

    print("Gesamtdatei")
    komplett = fitz.open()
    for teil in ("anschreiben.pdf", "lebenslauf.pdf", "bescheinigung.pdf"):
        komplett.insert_pdf(fitz.open(os.path.join(ZIEL, teil)))
    eigenschaften_setzen(komplett, "bewerbung-komplett.pdf")
    komplett.save(os.path.join(ZIEL, "bewerbung-komplett.pdf"), garbage=4, deflate=True)

    print()
    for datei in sorted(os.listdir(ZIEL)):
        pfad = os.path.join(ZIEL, datei)
        if os.path.isfile(pfad):
            print("  %-26s %5d KB" % (datei, round(os.path.getsize(pfad) / 1024)))


if __name__ == "__main__":
    main()
