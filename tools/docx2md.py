#!/usr/bin/env python3
"""Konvertiert die Word-Entwuerfe aus beitraege/ nach Markdown.

Aufruf:  python tools/docx2md.py [datei.docx ...] [--force]
Ohne Argumente werden alle .docx in beitraege/ verarbeitet.

Uebernommen werden Ueberschriften (Titel/Ueberschrift 1-3), Aufzaehlungen
sowie Fett- und Kursivauszeichnung. Unformatierte Dokumente nutzen fett
gesetzte Einzelabsaetze als Ueberschriften: der erste wird zum Titel, alle
weiteren zu Abschnittsueberschriften.

Eingebettete Bilder landen in beitraege/assets/<beitrag>/ und werden nach
dem Beitrag benannt und durchnummeriert (<beitrag>-01.png, -02.png, ...),
sodass die alphabetische Sortierung der Reihenfolge im Text entspricht.

Das Skript ist ein Import-Werkzeug: Nach der Konvertierung ist die
Markdown-Datei die Quelle und wird von Hand gepflegt. Bestehende .md-Dateien
werden daher uebersprungen, sofern nicht --force gesetzt ist.
"""

import glob
import os
import re
import sys
import unicodedata
import zipfile
from xml.etree import ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
WP = '{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}'
V = '{urn:schemas-microsoft-com:vml}'

ASSET_ROOT = os.path.join('beitraege', 'assets')
UMLAUTE = {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss'}
MARKDOWN_SPECIALS = '\\`*_[]'


def slugify(value):
    value = value.lower()
    for umlaut, replacement in UMLAUTE.items():
        value = value.replace(umlaut, replacement)
    value = unicodedata.normalize('NFD', value)
    value = ''.join(c for c in value if unicodedata.category(c) != 'Mn')
    value = re.sub(r'[^a-z0-9]+', '-', value)
    return value.strip('-')


def escape_markdown(text):
    """Maskiert Zeichen, die Markdown sonst als Syntax liest."""
    for char in MARKDOWN_SPECIALS:
        text = text.replace(char, '\\' + char)
    return text


def heading_level(paragraph):
    """Liefert die Ueberschriftenebene aus der Absatzformatvorlage."""
    properties = paragraph.find(W + 'pPr')
    if properties is None:
        return None

    style = properties.find(W + 'pStyle')
    if style is None:
        return None

    # Word kuerzt Umlaute in Style-IDs: "Überschrift1" -> "berschrift1".
    name = (style.get(W + 'val') or '').lower()
    if name in ('titel', 'title'):
        return 1

    match = re.match(r'(?:berschrift|uberschrift|heading)(\d)', name)
    if match:
        return min(int(match.group(1)) + 1, 6)

    return None


def is_list_item(paragraph):
    properties = paragraph.find(W + 'pPr')
    return properties is not None and properties.find(W + 'numPr') is not None


def image_reference(run):
    """Liefert (Relationship-ID, Alternativtext) eines Bildes im Textlauf."""
    for anchor in run.iter():
        if anchor.tag not in (WP + 'inline', WP + 'anchor'):
            continue

        blip = anchor.find('.//' + A + 'blip')
        if blip is None:
            continue

        embed = blip.get(R + 'embed')
        if not embed:
            continue

        properties = anchor.find(WP + 'docPr')
        alt = ''
        if properties is not None:
            alt = properties.get('descr') or properties.get('name') or ''
        return embed, alt.strip()

    # Aeltere Dokumente betten Bilder ueber VML ein.
    for image in run.iter(V + 'imagedata'):
        embed = image.get(R + 'id')
        if embed:
            return embed, (image.get('title') or '').strip()

    return None


def read_items(paragraph):
    """Zerlegt einen Absatz in Text- und Bildbausteine in Dokumentreihenfolge."""
    items = []
    for run in paragraph.iter(W + 'r'):
        reference = image_reference(run)
        if reference:
            items.append(('image', reference[0], reference[1]))
            continue

        text = ''.join(node.text or '' for node in run.iter(W + 't'))
        if not text:
            continue

        properties = run.find(W + 'rPr')
        bold = properties is not None and properties.find(W + 'b') is not None
        italic = properties is not None and properties.find(W + 'i') is not None
        items.append(('text', text, bold, italic))
    return items


def render_text(items):
    """Setzt die Textbausteine zu einer Markdown-Zeile zusammen."""
    parts = []
    for item in items:
        if item[0] != 'text':
            continue

        _, text, bold, italic = item
        rendered = escape_markdown(text)
        stripped = rendered.strip()

        # Auszeichnung eng um den Text legen, Randabstaende bleiben aussen.
        if stripped and (bold or italic):
            marker = ('**' if bold else '') + ('*' if italic else '')
            leading = rendered[:len(rendered) - len(rendered.lstrip())]
            trailing = rendered[len(rendered.rstrip()):]
            rendered = leading + marker + stripped + marker + trailing

        parts.append(rendered)

    return re.sub(r'[ \t]+', ' ', ''.join(parts)).strip()


def all_bold(items):
    texts = [item for item in items if item[0] == 'text' and item[1].strip()]
    return bool(texts) and all(item[2] for item in texts)


def read_relationships(archive):
    """Bildet Relationship-IDs auf Dateien im Archiv ab."""
    targets = {}
    root = ET.fromstring(archive.read('word/_rels/document.xml.rels'))
    for relationship in root:
        target = relationship.get('Target', '')
        if relationship.get('TargetMode') == 'External' or not target:
            continue
        targets[relationship.get('Id')] = 'word/' + target.lstrip('/')
    return targets


def read_metadata(archive):
    """Liest das Erstelldatum aus den Dokumenteigenschaften."""
    try:
        core = archive.read('docProps/core.xml').decode('utf-8')
    except KeyError:
        return {}

    created = re.search(r'<dcterms:created[^>]*>([0-9]{4}-[0-9]{2}-[0-9]{2})', core)
    return {'date': created.group(1) if created else ''}


def render_frontmatter(fields):
    lines = ['---']
    for key, value in fields.items():
        if value:
            lines.append('{}: "{}"'.format(key, str(value).replace('"', '\\"')))
    lines.append('draft: true')
    lines.append('---')
    return '\n'.join(lines)


class ImageWriter:
    """Legt Bilder eines Beitrags nummeriert im passenden Assets-Ordner ab."""

    def __init__(self, archive, slug, asset_root=ASSET_ROOT):
        self.archive = archive
        self.slug = slug
        self.directory = os.path.join(asset_root, slug)
        self.relationships = read_relationships(archive)
        self.written = {}
        self.paths = []

    def markdown(self, relationship_id, alt):
        source = self.relationships.get(relationship_id)
        if not source or source not in self.archive.namelist():
            return ''

        if source not in self.written:
            extension = os.path.splitext(source)[1].lower() or '.png'
            name = '{}-{:02d}{}'.format(self.slug, len(self.written) + 1, extension)
            path = os.path.join(self.directory, name)

            os.makedirs(self.directory, exist_ok=True)
            with open(path, 'wb') as handle:
                handle.write(self.archive.read(source))

            self.written[source] = name
            self.paths.append(path)

        # Pfad relativ zur Markdown-Datei in beitraege/.
        url = 'assets/{}/{}'.format(self.slug, self.written[source])
        return '![{}]({})'.format(escape_markdown(alt), url)


def convert(path, asset_root=ASSET_ROOT):
    slug = slugify(os.path.splitext(os.path.basename(path))[0])
    blocks = []

    with zipfile.ZipFile(path) as archive:
        document = ET.fromstring(archive.read('word/document.xml'))
        images = ImageWriter(archive, slug, asset_root)

        seen_title = False

        for paragraph in document.find(W + 'body').iter(W + 'p'):
            items = read_items(paragraph)
            if not items:
                continue

            text = render_text(items)
            pictures = [images.markdown(item[1], item[2])
                        for item in items if item[0] == 'image']
            pictures = [picture for picture in pictures if picture]

            if not text:
                blocks.extend(pictures)
                continue

            level = heading_level(paragraph)

            # Dokumente ohne Formatvorlagen: fett gesetzte Einzelabsaetze
            # sind die Ueberschriften.
            if level is None and all_bold(items) and len(text) < 120:
                level = 1 if not seen_title else 2

            if level is not None:
                seen_title = True
                blocks.append('#' * level + ' ' + text.replace('*', ''))
            elif is_list_item(paragraph):
                blocks.append('- ' + text)
            else:
                blocks.append(text)

            blocks.extend(pictures)

        metadata = read_metadata(archive)

    # Der Titel wandert ins Frontmatter, damit er im Text nicht doppelt steht.
    title = ''
    if blocks and blocks[0].startswith('# '):
        title = blocks.pop(0)[2:].strip()

    frontmatter = render_frontmatter({
        'title': title,
        'slug': slug,
        'date': metadata.get('date', ''),
    })

    return frontmatter, blocks, images.paths


def join_blocks(blocks):
    """Fuegt Bloecke zusammen; aufeinanderfolgende Listenpunkte bleiben eng."""
    lines = []
    for index, block in enumerate(blocks):
        if index and not (block.startswith('- ') and blocks[index - 1].startswith('- ')):
            lines.append('')
        lines.append(block)
    return '\n'.join(lines) + '\n'


def main(argv):
    force = '--force' in argv
    paths = [argument for argument in argv if argument != '--force']

    if not paths:
        paths = sorted(glob.glob(os.path.join('beitraege', '*.docx')))

    if not paths:
        print('Keine .docx-Dateien gefunden.')
        return 1

    for path in paths:
        target = os.path.join(os.path.dirname(path),
                              slugify(os.path.splitext(os.path.basename(path))[0]) + '.md')

        # Nach dem Import ist die Markdown-Datei die Quelle. Ein zweiter Lauf
        # wuerde spaetere Aenderungen daran ueberschreiben.
        if os.path.exists(target) and not force:
            print('{} existiert bereits - uebersprungen (--force zum Ueberschreiben)'
                  .format(target))
            continue

        frontmatter, blocks, images = convert(path)

        with open(target, 'w', encoding='utf-8', newline='\n') as handle:
            handle.write(frontmatter + '\n\n' + join_blocks(blocks))

        note = ', {} Bild(er)'.format(len(images)) if images else ''
        print('{} -> {} ({} Bloecke{})'.format(path, target, len(blocks), note))

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
