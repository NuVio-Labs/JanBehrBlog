# QR-Code zur Bewerbungsseite

Der Code zeigt auf `https://www.behr.blog/cv/<CV_SCHLUESSEL>`.

Die vollstaendige Adresse steht bewusst nicht in diesem Repository, weil es
oeffentlich ist. Den Schluessel findest du in `.env.local` (nicht eingecheckt)
und in den Vercel Environment Variables.

- `behr-cv-qr.svg` — Vektor, erste Wahl fuer den Druck
- `behr-cv-qr.png` — 1080 px, fuer Bildschirm und schnelle Einbindung

Beide Dateien sind in der `.gitignore`: Wer sie einsieht, kann den Code scannen
und kennt damit die Adresse.

## Druckeigenschaften des SVG

- gefuellte schwarze Flaechen, keine Konturen und keine Strokes
- keine Effekte, keine Filter, keine Verlaeufe, keine Transparenz
- weisse Grundflaeche als eigenes Rechteck darunter
- quadratische viewBox, Voreinstellung 40 x 40 mm, frei skalierbar
- 4 Module Weissraum ringsum, der in der Norm vorgesehene Mindestwert
- Fehlerkorrektur Level H, Version 5 mit 37 x 37 Modulen
- unter etwa 25 mm Kantenlaenge nicht drucken

## So ist die Seite geschuetzt

Ausgeliefert wird alles von `api/cv.js`. Die Funktion vergleicht den Schluessel
aus der Adresse mit `CV_SCHLUESSEL`:

| Aufruf | Ergebnis |
| --- | --- |
| `/cv/<CV_SCHLUESSEL>` | Bewerbungsseite |
| `/cv/<CV_SCHLUESSEL>/lebenslauf.pdf` | Unterlage mit Tagesdatum |
| `/cv/irgendwas` | 404 |
| `/cv` | 404 |

Dazu `noindex, nofollow` als Meta-Angabe und als `X-Robots-Tag`, kein Eintrag in
Navigation, `sitemap.xml` oder `robots.txt`. Ein Disallow-Eintrag in der
`robots.txt` waere kontraproduktiv, er wuerde den Pfad bekannt machen.

Die Quelldokumente unter `CV/` sind ueber die `.vercelignore` von der
Auslieferung ausgenommen; die aufbereiteten Fassungen liegen unter
`api/_quelle/` und sind nur ueber die Funktion erreichbar.

## Pflege der Unterlagen

Zwei Umgebungsvariablen sind noetig, lokal in `.env.local`, in Produktion in
den Vercel Environment Variables:

| Variable | Zweck |
| --- | --- |
| `CV_SCHLUESSEL` | der Teil der Adresse hinter `/cv/` |
| `CV_DATEN_SCHLUESSEL` | 32 Byte, base64, entschluesselt die Unterlagen |

Aendern sich die Quelldokumente unter `CV/Jan_Behr/Bewerbung Online/`:

```bash
python tools/bewerbung.py      # bereinigt und legt sie unter api/_quelle/klar ab
node tools/verschluesseln.js   # verschluesselt sie nach api/_quelle/*.bin
```

Nur die `.bin`-Dateien gehen ins Repository. Der Klartext unter
`api/_quelle/klar/` bleibt lokal und steht in der `.gitignore`.

## Neu erzeugen

Noetig, sobald sich der Schluessel oder die Domain aendert. Ein temporaeres
Verzeichnis reicht, `qrcode` gehoert nicht in die Projektabhaengigkeiten:

```bash
mkdir qr-tmp && cd qr-tmp && npm init -y && npm install qrcode
```

Dann mit dem Generator aus `tools/` das SVG schreiben und das PNG erzeugen.
Wichtig beim PNG: eine Kantenlaenge waehlen, die sich ganzzahlig auf die
Modulzahl aufteilt (45 Module mal 24 px ergeben 1080 px). Sonst weichen SVG und
PNG an den Modulkanten voneinander ab und der Vergleich schlaegt fehl.

Ein Wechsel des Schluessels macht alle bereits gedruckten Codes wertlos.
