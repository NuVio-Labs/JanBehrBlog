#!/usr/bin/env python3
"""Baut aus den Markdown-Beitraegen die Artikelseiten und den Suchindex.

Aufruf:  python tools/build.py

Erzeugt wird:
  beitrag/<slug>.html   je Beitrag, im Layout aus assets/blog.css
  assets/posts.js       Suchindex fuer assets/search.js
  index.html            Beitragslisten zwischen den Marker-Kommentaren

Beitraege mit "draft: true" im Frontmatter werden uebersprungen. Die
Reihenfolge ergibt sich aus dem Datum, aelteste zuerst.
"""

import glob
import html
import os
import re
import sys

SITE = 'https://www.behr.blog'
AUTHOR = 'Jan Behr'
SOURCE_DIR = 'beitraege'
OUTPUT_DIR = 'beitrag'

CSP = ("default-src 'self'; img-src 'self' data:; font-src 'self'; "
       "style-src 'self'; script-src 'self'; connect-src 'self'; "
       "object-src 'none'; base-uri 'self'; form-action 'self'; frame-src 'none';")

MONATE = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
          'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']

# Bedingungen fuer den Anreisser-Absatz mit Initiale (siehe render_body).
INTRO_MAX_LENGTH = 200
INTRO_BAD_INITIALS = ('I', 'J', 'L')

# Panel-Marker in index.html: Kategorie -> Markername
PANELS = {
    'Projekttagebuch': 'projekttagebuch',
    'Smart Home': 'smart-home',
}

# Kategorie -> Reiter-ID auf der Startseite, fuer den Ruecksprung.
CATEGORY_TABS = {
    'Projekttagebuch': 'tab-projects',
    'Ideen & Gedanken': 'tab-ideas',
    'Smart Home': 'tab-smart-home',
    'Sonstiges': 'tab-misc',
}


# --------------------------------------------------------------------- Lesen

def parse_post(path):
    """Liest eine Markdown-Datei als (Metadaten, Zeilen des Rumpfs)."""
    with open(path, encoding='utf-8') as handle:
        text = handle.read()

    match = re.match(r'^---\n(.*?)\n---\n?(.*)$', text, re.S)
    if not match:
        raise ValueError('{}: kein Frontmatter gefunden'.format(path))

    meta = {}
    for line in match.group(1).split('\n'):
        if ':' not in line:
            continue
        key, _, value = line.partition(':')
        meta[key.strip()] = value.strip().strip('"')

    meta['source'] = path
    return meta, match.group(2).strip().split('\n')


# ------------------------------------------------------------- Markdown -> HTML

def render_inline(text):
    """Wandelt Auszeichnung innerhalb einer Zeile in HTML."""
    stash = []

    def keep(match):
        stash.append(match.group(1))
        return '\x00{}\x00'.format(len(stash) - 1)

    # Maskierte Zeichen aus der Konvertierung herausnehmen, damit sie
    # nicht erneut als Auszeichnung gelesen werden.
    text = re.sub(r'\\(.)', keep, text)
    text = html.escape(text, quote=False)

    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)',
                  lambda m: '<img src="{}" alt="{}" loading="lazy" decoding="async">'
                  .format(html.escape(m.group(2), quote=True), html.escape(m.group(1), quote=True)),
                  text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
                  lambda m: '<a href="{}">{}</a>'
                  .format(html.escape(m.group(2), quote=True), m.group(1)),
                  text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)

    return re.sub(r'\x00(\d+)\x00',
                  lambda m: html.escape(stash[int(m.group(1))], quote=False), text)


def slug_for_heading(text, used):
    plain = re.sub(r'<[^>]+>', '', text)
    base = plain.lower()
    for umlaut, replacement in (('ä', 'ae'), ('ö', 'oe'), ('ü', 'ue'), ('ß', 'ss')):
        base = base.replace(umlaut, replacement)
    base = re.sub(r'[^a-z0-9]+', '-', base).strip('-') or 'abschnitt'

    candidate = base
    suffix = 2
    while candidate in used:
        candidate = '{}-{}'.format(base, suffix)
        suffix += 1
    used.add(candidate)
    return candidate


def render_list(lines, start):
    """Rendert eine zusammenhaengende Aufzaehlung ab lines[start]."""
    items = []
    index = start

    while index < len(lines):
        match = re.match(r'^(\s*)- (.*)$', lines[index])
        if not match:
            break
        items.append((len(match.group(1)), match.group(2)))
        index += 1

    def build(position, level):
        parts = ['<ul>']
        while position < len(items):
            indent, content = items[position]
            if indent < level:
                break
            if indent > level:
                nested, position = build(position, indent)
                parts[-1] = parts[-1][:-len('</li>')] + nested + '</li>'
                continue
            parts.append('<li>' + render_inline(content) + '</li>')
            position += 1
        parts.append('</ul>')
        return '\n'.join(parts), position

    markup, _ = build(0, items[0][0])
    return markup, index


def render_body(lines):
    """Baut den Artikelrumpf und sammelt die Abschnitte fuer das Inhaltsverzeichnis."""
    parts = []
    toc = []
    used = set()
    intro_done = False
    index = 0

    while index < len(lines):
        line = lines[index].rstrip()

        if not line:
            index += 1
            continue

        heading = re.match(r'^(#{2,3}) (.*)$', line)
        if heading:
            level = len(heading.group(1))
            label = render_inline(heading.group(2))
            anchor = slug_for_heading(label, used)
            parts.append('<h{0} id="{1}">{2}</h{0}>'.format(level, anchor, label))
            if level == 2:
                toc.append((anchor, re.sub(r'<[^>]+>', '', label)))
            index += 1
            continue

        if re.match(r'^\s*- ', line):
            markup, index = render_list(lines, index)
            parts.append(markup)
            continue

        # Ein alleinstehendes Bild bekommt eine eigene Abbildung.
        picture = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)$', line)
        if picture:
            figure = '<figure class="article-figure">' + render_inline(line)
            if picture.group(1):
                figure += '<figcaption>{}</figcaption>'.format(
                    html.escape(picture.group(1), quote=False))
            parts.append(figure + '</figure>')
            index += 1
            continue

        # Der erste Absatz bekommt die Initiale. Nur ein kurzer Anreisser
        # wird zusaetzlich in Displaygroesse gesetzt - ein langer Absatz
        # erschlaegt in dieser Groesse die ganze Seite. Schmale
        # Grossbuchstaben wie I, J oder L bleiben aussen vor, weil sie als
        # Initiale wie ein versehentlicher senkrechter Strich aussehen.
        css_class = ''
        if not intro_done:
            plain = re.sub(r'\\(.)|[*_`]', lambda m: m.group(1) or '', line).strip()
            if plain[:1] in INTRO_BAD_INITIALS:
                css_class = ''
            elif len(plain) <= INTRO_MAX_LENGTH:
                css_class = ' class="intro"'
            else:
                css_class = ' class="dropcap"'
        intro_done = True

        parts.append('<p{}>{}</p>'.format(css_class, render_inline(line)))
        index += 1

    return '\n\n'.join(parts), toc


# ----------------------------------------------------------------- Bausteine

def german_date(value):
    match = re.match(r'(\d{4})-(\d{2})-(\d{2})', value or '')
    if not match:
        return ''
    year, month, day = match.groups()
    return '{}. {} {}'.format(int(day), MONATE[int(month) - 1], year)


def reading_time(lines):
    words = sum(len(re.sub(r'[#*\\_-]', ' ', line).split()) for line in lines)
    return max(1, round(words / 200))


def excerpt_of(lines):
    for line in lines:
        if line.strip() and not line.startswith(('#', '-', '!')):
            plain = re.sub(r'\\(.)', r'\1', line)
            plain = re.sub(r'\*+', '', plain).strip()
            if len(plain) <= 180:
                return plain
            cut = plain[:180].rsplit(' ', 1)[0]
            return cut + ' …'
    return ''


def title_html(title):
    """*Sternchen* im Titel werden zur farbigen Hervorhebung."""
    return re.sub(r'\*([^*]+)\*', r'<em>\1</em>', html.escape(title, quote=False))


def title_plain(title):
    return title.replace('*', '')


def display_title(post):
    """Ueberschrift fuer die Anzeige.

    Optionales Frontmatter-Feld "headline" haelt die Ueberschrift auf der
    Seite kurz, waehrend "title" den ausfuehrlichen Titel fuer Browser-Tab,
    Teilen-Vorschau und Suchmaschinen behaelt.
    """
    return post.get('headline') or post['title']


def render_toc(toc):
    if not toc:
        return ''
    items = '\n'.join(
        '                        <li><a href="#{}">{}</a></li>'.format(anchor, html.escape(label, quote=False))
        for anchor, label in toc)
    return ('                <aside class="article-toc" aria-label="Inhaltsverzeichnis">\n'
            '                    <p class="article-toc__label">Inhalt</p>\n'
            '                    <ol>\n{}\n                    </ol>\n'
            '                </aside>\n').format(items)


def render_navigation(post, previous, following):
    """Blaetternavigation innerhalb derselben Kategorie.

    Gibt es in der Kategorie keinen Nachbarn, tritt an dessen Stelle ein
    Rücksprung auf den passenden Reiter der Startseite. Steht der Beitrag
    allein, bleibt es bei einem einzigen Verweis über die volle Breite.
    """
    def link(target, label):
        return ('            <a href="{}">\n'
                '                <span class="article-navigation__label">{}</span>\n'
                '                <strong>{}</strong>\n'
                '            </a>').format(post_url(target), label,
                                           html.escape(title_plain(display_title(target)), quote=False))

    category = post.get('category', '')
    overview = ('            <a href="{}">\n'
                '                <span class="article-navigation__label">Übersicht</span>\n'
                '                <strong>Alle Beiträge in {}</strong>\n'
                '            </a>').format(category_url(category),
                                           html.escape(category, quote=False))

    # Linke Haelfte zurueck, rechte vor - das CSS richtet die zweite
    # Spalte rechtsbuendig aus. Die fehlende Seite fuellt die Uebersicht.
    if not previous and not following:
        sides = [overview]
    else:
        sides = [link(previous, 'Vorheriger Beitrag') if previous else overview,
                 link(following, 'Nächster Beitrag') if following else overview]

    modifier = ' article-navigation--single' if len(sides) == 1 else ''
    return ('        <nav class="article-navigation{}" aria-label="Weitere Beiträge">\n'
            .format(modifier) + '\n'.join(sides) + '\n        </nav>')


def post_url(post):
    return '/{}/{}.html'.format(OUTPUT_DIR, post['slug'])


def category_url(category):
    """Verweis auf den Reiter der Startseite, der diese Kategorie zeigt."""
    tab = CATEGORY_TABS.get(category)
    return '/#{}'.format(tab) if tab else '/#projekttagebuch'


# ------------------------------------------------------------------- Seiten

PAGE = '''<!doctype html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{description}">
    <meta name="author" content="{author}">
    <meta name="referrer" content="no-referrer">
    <meta http-equiv="Content-Security-Policy" content="{csp}">
    <meta name="theme-color" content="#eff0e9">
    <meta property="og:type" content="article">
    <meta property="og:title" content="{og_title}">
    <meta property="og:description" content="{description}">
    <meta property="og:url" content="{url}">
    <link rel="canonical" href="{url}">
    <link rel="preload" href="/assets/fonts/dm-sans-variable.woff2" as="font" type="font/woff2" crossorigin>
    <link rel="preload" href="/assets/fonts/manrope-variable.woff2" as="font" type="font/woff2" crossorigin>
    <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
    <link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
    <link rel="manifest" href="/site.webmanifest">
    <title>{page_title} | {author}</title>
    <link rel="stylesheet" href="/assets/blog.css">
    <link rel="stylesheet" href="/assets/tailwind.css">
</head>

<body>
    <a class="skip-link" href="#main-content">Zum Inhalt springen</a>
    <div class="reading-progress" aria-hidden="true"><span></span></div>

    <header class="site-header">
        <div class="site-header__inner shell">
            <a class="brand" href="/#start" aria-label="{author}, Startseite">
                <span class="brand__mark" aria-hidden="true">JB</span>
                <span>{author}</span>
            </a>
            <a class="back-link" href="/#projekttagebuch"><span aria-hidden="true">&#8592;</span> Alle Beiträge</a>
        </div>
    </header>

    <main id="main-content" tabindex="-1">
        <article>
            <section class="article-hero" aria-labelledby="article-title">
                <div class="article-hero__grid shell">
                    <div>
                        <p class="article-kicker">{category}</p>
                        <h1 id="article-title">{heading}</h1>
                        <p class="article-hero__lead">{lead}</p>
                        <div class="article-meta">
                            <span>{date}</span>
                            <span>{minutes} Min. Lesezeit</span>
                        </div>
                    </div>
                    <span class="article-number" aria-hidden="true">{number}</span>
                </div>
            </section>

            <section class="article-body">
                <div class="article-layout shell">
{toc}                    <div class="article-copy">
{body}

                        <button class="share-button" type="button" data-share-button>Beitrag teilen <span aria-hidden="true">&#8599;</span></button>

                        <div class="article-signoff">
                            <p>Geschrieben von {author}. Fragen oder Anmerkungen? Ich freue mich über den Austausch.</p>
                        </div>
                    </div>
                </div>
            </section>
        </article>

{navigation}
    </main>

    <footer class="site-footer">
        <div class="site-footer__inner shell">
            <span>&copy; 2026 {author}</span>
            <nav aria-label="Rechtliches">
                <a href="/">Startseite</a>
                <a href="/impressum.html">Impressum</a>
                <a href="/datenschutz.html">Datenschutz</a>
            </nav>
        </div>
    </footer>

    <script src="/assets/blog.js" defer></script>
    <!-- Vercel Web Analytics: cookiefrei, wird von Vercel selbst ausgeliefert. -->
    <script src="/_vercel/insights/script.js" defer></script>
</body>
</html>
'''


def render_page(post, previous, following):
    body, toc = render_body(post['lines'])
    body = '\n'.join('                        ' + line if line else ''
                     for line in body.split('\n'))

    return PAGE.format(
        author=AUTHOR,
        csp=CSP,
        category=html.escape(post.get('category', ''), quote=True),
        heading=title_html(display_title(post)),
        page_title=html.escape(title_plain(post['title']), quote=False),
        og_title=html.escape(title_plain(post['title']), quote=True),
        description=html.escape(post['lead'], quote=True),
        lead=html.escape(post['lead'], quote=False),
        date=post['date_de'],
        minutes=post['minutes'],
        number=post['number'],
        url=SITE + post_url(post),
        toc=render_toc(toc),
        body=body,
        navigation=render_navigation(post, previous, following),
    )


# -------------------------------------------------------------- Startseite

def render_cards(posts):
    cards = []
    for position, post in enumerate(posts, start=1):
        cards.append(
            '                            <article class="idea-card">\n'
            '                                <span class="idea-card__index">{index:02d}</span>\n'
            '                                <div>\n'
            '                                    <h3><a href="{url}">{title}</a></h3>\n'
            '                                    <p>{excerpt}</p>\n'
            '                                    <p class="idea-card__meta">{date} · {minutes} Min. Lesezeit</p>\n'
            '                                </div>\n'
            '                            </article>'.format(
                index=position,
                url=post_url(post),
                title=html.escape(title_plain(display_title(post)), quote=False),
                excerpt=html.escape(post['excerpt'], quote=False),
                date=post['date_de'],
                minutes=post['minutes']))
    return '\n'.join(cards)


def update_index(posts):
    path = 'index.html'
    with open(path, encoding='utf-8') as handle:
        page = handle.read()

    for category, marker in PANELS.items():
        selected = [post for post in posts if post.get('category') == category]
        if not selected:
            continue

        pattern = re.compile(
            r'(<!-- beitraege:{0} -->).*?(<!-- /beitraege:{0} -->)'.format(re.escape(marker)),
            re.S)
        if not pattern.search(page):
            print('  Hinweis: Marker "beitraege:{}" fehlt in index.html'.format(marker))
            continue

        block = '\\1\n' + render_cards(selected).replace('\\', '\\\\') + '\n                            \\2'
        page = pattern.sub(block, page)

    with open(path, 'w', encoding='utf-8', newline='\n') as handle:
        handle.write(page)


def write_search_index(posts):
    entries = []
    for post in posts:
        entries.append(
            '    {{\n'
            '        title: {title},\n'
            '        url: {url},\n'
            '        category: {category},\n'
            '        meta: {meta},\n'
            '        excerpt: {excerpt},\n'
            '        tags: [{tags}]\n'
            '    }}'.format(
                title=js_string(title_plain(display_title(post))),
                url=js_string(post_url(post)),
                category=js_string(post.get('category', '')),
                meta=js_string(post['date_de']),
                excerpt=js_string(post['excerpt']),
                tags=', '.join(js_string(tag) for tag in post['tags'])))

    content = ('/* Suchindex der veroeffentlichten Beitraege.\n'
               '   Erzeugt von tools/build.py - nicht von Hand bearbeiten. */\n'
               'window.BLOG_POSTS = [\n' + ',\n'.join(entries) + '\n];\n')

    with open(os.path.join('assets', 'posts.js'), 'w', encoding='utf-8', newline='\n') as handle:
        handle.write(content)


def js_string(value):
    return "'" + value.replace('\\', '\\\\').replace("'", "\\'") + "'"


def write_sitemap(posts):
    """Schreibt sitemap.xml aus Startseite, Beitraegen und Rechtsseiten."""
    entries = [(SITE + '/', max(post['date'] for post in posts), '1.0')]
    entries += [(SITE + post_url(post), post['date'], '0.8') for post in posts]
    entries += [(SITE + '/impressum.html', '', '0.2'),
                (SITE + '/datenschutz.html', '', '0.2')]

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, changed, priority in entries:
        lines.append('    <url>')
        lines.append('        <loc>{}</loc>'.format(url))
        if changed:
            lines.append('        <lastmod>{}</lastmod>'.format(changed))
        lines.append('        <priority>{}</priority>'.format(priority))
        lines.append('    </url>')
    lines.append('</urlset>')

    with open('sitemap.xml', 'w', encoding='utf-8', newline='\n') as handle:
        handle.write('\n'.join(lines) + '\n')


# ---------------------------------------------------------------------- Lauf

def main():
    posts = []

    for path in sorted(glob.glob(os.path.join(SOURCE_DIR, '*.md'))):
        meta, lines = parse_post(path)

        if meta.get('draft', '').lower() == 'true':
            print('uebersprungen (Entwurf): {}'.format(path))
            continue

        for field in ('title', 'slug', 'date', 'category', 'lead'):
            if not meta.get(field):
                raise ValueError('{}: Feld "{}" fehlt im Frontmatter'.format(path, field))

        meta['lines'] = lines
        meta['date_de'] = german_date(meta['date'])
        meta['minutes'] = reading_time(lines)
        meta['excerpt'] = excerpt_of(lines)
        meta['tags'] = [tag.strip() for tag in meta.get('tags', '').split(',') if tag.strip()]
        posts.append(meta)

    if not posts:
        print('Keine veroeffentlichten Beitraege gefunden.')
        return 1

    posts.sort(key=lambda post: (post['date'], post['slug']))
    for position, post in enumerate(posts, start=1):
        post['number'] = '{:02d}'.format(position)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for post in posts:
        # Geblaettert wird innerhalb der Kategorie, nicht ueber alle Beitraege.
        siblings = [other for other in posts if other.get('category') == post.get('category')]
        position = siblings.index(post)

        previous = siblings[position - 1] if position else None
        following = siblings[position + 1] if position + 1 < len(siblings) else None

        target = os.path.join(OUTPUT_DIR, post['slug'] + '.html')
        with open(target, 'w', encoding='utf-8', newline='\n') as handle:
            handle.write(render_page(post, previous, following))
        print('{} -> {} ({} Min., {} in {})'.format(
            post['source'], target, post['minutes'],
            '{}/{}'.format(position + 1, len(siblings)), post.get('category', '')))

    write_search_index(posts)
    update_index(posts)
    write_sitemap(posts)
    print('\nassets/posts.js, index.html und sitemap.xml aktualisiert '
          '({} Beitraege).'.format(len(posts)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
