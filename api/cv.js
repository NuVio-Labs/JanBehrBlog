const crypto = require("node:crypto")
const { readFile } = require("node:fs/promises")
const path = require("node:path")
const fontkit = require("@pdf-lib/fontkit")
const { PDFDocument, rgb } = require("pdf-lib")

/**
 * Liefert die Bewerbungsseite und die Unterlagen aus.
 *
 * Erreichbar ist alles nur unter dem Schluessel aus CV_SCHLUESSEL. Damit
 * steht die Adresse nirgends im Repository, das oeffentlich ist.
 *
 *   /cv/<schluessel>                  Seite
 *   /cv/<schluessel>/<datei>.pdf      Unterlage
 *
 * Anschreiben und Gesamtbewerbung bekommen beim Abruf das Datum des Tages.
 * Die Basisdateien unter api/_quelle tragen keine Datumszeile. Die im PDF
 * eingebettete Calibri-Italic taugt zum Nachsetzen nicht, ihr fehlen die
 * Ziffern 3, 4, 8 und 9 - deshalb liegt Carlito-Italic bei, das metrisch
 * mit Calibri uebereinstimmt. Fuer das Anschreiben reicht der Aptos-Subset
 * aus dem Originaldokument.
 *
 * Die Unterlagen liegen im Repository nur verschluesselt (AES-256-GCM,
 * Schluessel in CV_DATEN_SCHLUESSEL), weil das Repository oeffentlich ist.
 * Entschluesselt wird erst hier, im Arbeitsspeicher.
 *
 * Uebergangsweise gibt es einen zweiten Schluessel, CV_DATEN_SCHLUESSEL_2.
 * Mit ihm ist der Lebenslauf vom Oktober 2026 verschluesselt, waehrend
 * Anschreiben, Bescheinigung, Gesamtdatei und Seite noch am ersten haengen.
 * Bis alles neu erzeugt ist, setzt die Funktion den neuen Lebenslauf in die
 * Gesamtdatei ein und die Angaben aus aktualisierung.json in die Seite.
 */

const QUELLE = path.join(__dirname, "_quelle")

function schluessel() {
    const liste = ["CV_DATEN_SCHLUESSEL", "CV_DATEN_SCHLUESSEL_2"]
        .map((name) => Buffer.from(process.env[name] || "", "base64"))
        .filter((wert) => wert.length === 32)
    if (liste.length === 0) {
        throw new Error("CV_DATEN_SCHLUESSEL fehlt oder hat die falsche Laenge")
    }
    return liste
}

/** Liest eine verschluesselte Datei: [12 Byte IV][16 Byte Tag][Chiffrat].
    Probiert jeden Schluessel; GCM verwirft den falschen am Tag. */
async function lesen(name) {
    const paket = await readFile(path.join(QUELLE, name + ".bin"))
    for (const wert of schluessel()) {
        try {
            const entschluessler = crypto.createDecipheriv(
                "aes-256-gcm",
                wert,
                paket.subarray(0, 12),
            )
            entschluessler.setAuthTag(paket.subarray(12, 28))
            return Buffer.concat([
                entschluessler.update(paket.subarray(28)),
                entschluessler.final(),
            ])
        } catch {
            /* naechster Schluessel */
        }
    }
    throw new Error(`${name}: keiner der Schluessel passt`)
}

async function vorhanden(name) {
    try {
        await readFile(path.join(QUELLE, name + ".bin"))
        return true
    } catch {
        return false
    }
}

/* Stempelstellen, ausgemessen an den Originaldokumenten.
   Die Grundlinien zaehlen von der Oberkante der MediaBox. */
const STEMPEL = {
    anschreiben: {
        seite: 0,
        text: (datum) => `Gladbeck, ${datum}`,
        schrift: "aptos-datum.ttf",
        groesse: 12,
        x: 526.58,
        grundlinie: 82.1,
        ausrichtung: "rechts",
        farbe: [0, 0, 0],
    },
    lebenslauf: {
        seite: 1,
        text: (datum) => `Gladbeck, ${datum}`,
        schrift: "carlito-italic-datum.ttf",
        groesse: 9,
        x: 202.61,
        grundlinie: 679.9,
        ausrichtung: "links",
        /* Das Original steht in Grau, nicht in Schwarz. */
        farbe: [0.3529, 0.3529, 0.3529],
    },
}

const DOKUMENTE = {
    "bewerbung-komplett.pdf": {
        datei: "bewerbung-komplett.pdf",
        name: "Jan-Behr-Bewerbung-komplett.pdf",
        stempel: ["anschreiben", "lebenslauf"],
        /* Seite 2 ist der Lebenslauf; er kommt aus lebenslauf.pdf. */
        ersetzen: { seite: 1, aus: "lebenslauf.pdf" },
    },
    "anschreiben.pdf": {
        datei: "anschreiben.pdf",
        name: "Jan-Behr-Anschreiben.pdf",
        stempel: ["anschreiben"],
    },
    "lebenslauf.pdf": {
        datei: "lebenslauf.pdf",
        name: "Jan-Behr-Lebenslauf.pdf",
        stempel: [{ ...STEMPEL.lebenslauf, seite: 0 }],
    },
    "bescheinigung.pdf": {
        datei: "bescheinigung.pdf",
        name: "BFW-Bescheinigung-Praktikumsgeber.pdf",
        stempel: [],
    },
}

const CSP = "default-src 'self'; img-src 'self' data:; font-src 'self'; " +
    "style-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; " +
    "base-uri 'self'; form-action 'self'; frame-src 'none';"

function heute() {
    return new Intl.DateTimeFormat("de-DE", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        timeZone: "Europe/Berlin",
    }).format(new Date())
}

/** Setzt eine Datumszeile an die Stelle, an der im Original eine stand. */
async function stempeln(pdf, vorgabe, datum) {
    const schrift = await pdf.embedFont(
        await readFile(path.join(QUELLE, "schriften", vorgabe.schrift)),
        { subset: true },
    )
    const zeile = vorgabe.text(datum)
    const breite = schrift.widthOfTextAtSize(zeile, vorgabe.groesse)
    const seite = pdf.getPage(vorgabe.seite)
    const rahmen = seite.getMediaBox()

    seite.drawText(zeile, {
        x: vorgabe.ausrichtung === "rechts" ? vorgabe.x - breite : vorgabe.x,
        y: rahmen.y + rahmen.height - vorgabe.grundlinie,
        size: vorgabe.groesse,
        font: schrift,
        color: rgb(...vorgabe.farbe),
    })
}

/** Tauscht eine Seite gegen die erste Seite einer anderen Unterlage. */
async function seiteErsetzen(pdf, vorgabe) {
    const quelle = await PDFDocument.load(await lesen(vorgabe.aus))
    const [neu] = await pdf.copyPages(quelle, [0])
    pdf.removePage(vorgabe.seite)
    pdf.insertPage(vorgabe.seite, neu)
}

async function unterlage(dokument) {
    const basis = await lesen(dokument.datei)
    if (dokument.stempel.length === 0 && !dokument.ersetzen) {
        return basis
    }

    const pdf = await PDFDocument.load(basis)
    pdf.registerFontkit(fontkit)
    if (dokument.ersetzen) {
        await seiteErsetzen(pdf, dokument.ersetzen)
    }
    const datum = heute()
    for (const eintrag of dokument.stempel) {
        await stempeln(pdf, typeof eintrag === "string" ? STEMPEL[eintrag] : eintrag, datum)
    }
    return Buffer.from(await pdf.save())
}

function maskieren(text) {
    return String(text)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
}

/** Text der letzten Ueberschrift vor einer Stelle, ohne Tags. */
function ueberschriftVor(html, stelle) {
    const muster = /<(h[1-6]|p)\b[^>]*class="[^"]*(?:cv-section__title|cv-subhead)[^"]*"[^>]*>([\s\S]*?)<\/\1>|<(h[1-6])\b[^>]*>([\s\S]*?)<\/\3>/g
    let text = ""
    for (const treffer of html.slice(0, stelle).matchAll(muster)) {
        text = (treffer[2] ?? treffer[4]).replace(/<[^>]+>/g, "")
    }
    return text
}

/**
 * Fuellt die Listen mit der Klasse `klasse` neu. Welche Liste welche Daten
 * bekommt, entscheidet die Ueberschrift davor (`zuordnung`: Regex -> Eintraege).
 * Das erste <li> dient als Muster, damit Elemente und Klassen der Vorlage
 * erhalten bleiben. Passt etwas nicht, bleibt die Liste, wie sie ist.
 */
function listenErsetzen(html, klasse, zuordnung, eintragBauen) {
    const muster = new RegExp(
        `(<(ul|ol)\\b[^>]*class="[^"]*\\b${klasse}\\b[^"]*"[^>]*>)([\\s\\S]*?)(</\\2>)`,
        "g",
    )
    return html.replace(muster, (ganz, auf, _typ, inhalt, zu, stelle) => {
        const titel = ueberschriftVor(html, stelle)
        const passend = zuordnung.find(([regel]) => regel.test(titel))
        const vorbild = inhalt.match(/<li\b[^>]*>[\s\S]*?<\/li>/)
        if (!passend || !vorbild) {
            console.warn(`cv: ${klasse} unter "${titel}" nicht ersetzt`)
            return ganz
        }
        const einzug = (inhalt.match(/^\s*/) || [""])[0]
        const ende = (inhalt.match(/\s*$/) || [""])[0]
        const neu = passend[1].map((e) => einzug + eintragBauen(vorbild[0], e))
        return auf + neu.join("") + ende + zu
    })
}

/** Ersetzt den Inhalt eines Elements mit der Klasse; fehlt es, faellt es weg. */
function feldSetzen(li, klasse, wert) {
    const muster = new RegExp(
        `\\s*<(\\w+)\\b([^>]*class="[^"]*\\b${klasse}\\b[^"]*"[^>]*)>[\\s\\S]*?</\\1>`,
    )
    return li.replace(muster, (ganz, tag, attribute) => wert
        ? ganz.slice(0, ganz.indexOf("<")) + `<${tag}${attribute}>${maskieren(wert)}</${tag}>`
        : "")
}

async function aktualisieren(html) {
    if (!(await vorhanden("aktualisierung.json"))) {
        return html
    }
    const daten = JSON.parse((await lesen("aktualisierung.json")).toString("utf8"))

    const marke = (li, e) => li.replace(
        /(<li\b[^>]*>)[\s\S]*?(<\/li>)/, (_, auf, zu) => auf + maskieren(e) + zu)
    html = listenErsetzen(html, "cv-tags", [
        [/[Kk]enntnis|[Tt]echnik|[Ss]oftware|[Ff](ä|ae)higkeit|\bIT\b/, daten.kenntnisse],
    ], marke)

    const station = (li, e) => ["period", "role", "place"].reduce(
        (stand, feld) => feldSetzen(stand, `cv-timeline__${feld}`, e[feld]), li)
    return listenErsetzen(html, "cv-timeline", [
        [/bildung|ausbildung|schul/i, daten.bildung],
        [/beruf|erfahrung|werdegang|station|lauf/i, daten.beruf],
    ], station)
}

async function seite(pfad) {
    const vorlage = await aktualisieren((await lesen("seite.html")).toString("utf8"))
    const groessen = {}
    for (const [schluessel, dokument] of Object.entries(DOKUMENTE)) {
        const daten = await unterlage(dokument)
        groessen[schluessel] = Math.round(daten.length / 1024)
    }

    return vorlage
        .replaceAll("{{DATUM}}", heute())
        .replaceAll("{{PFAD}}", pfad)
        .replaceAll("{{GROESSE_KOMPLETT}}", groessen["bewerbung-komplett.pdf"])
        .replaceAll("{{GROESSE_ANSCHREIBEN}}", groessen["anschreiben.pdf"])
        .replaceAll("{{GROESSE_LEBENSLAUF}}", groessen["lebenslauf.pdf"])
        .replaceAll("{{GROESSE_BESCHEINIGUNG}}", groessen["bescheinigung.pdf"])
}

function nichtGefunden(antwort) {
    antwort.status(404)
    antwort.setHeader("Content-Type", "text/plain; charset=utf-8")
    antwort.end("Nicht gefunden")
}

module.exports = async function handler(anfrage, antwort) {
    const erwartet = (process.env.CV_SCHLUESSEL || "").trim()
    const url = new URL(anfrage.url, "https://www.behr.blog")
    const schluessel = (url.searchParams.get("k") || "").trim()
    const datei = url.searchParams.get("d")

    if (!erwartet || schluessel !== erwartet) {
        return nichtGefunden(antwort)
    }

    antwort.setHeader("Content-Security-Policy", CSP)
    antwort.setHeader("X-Robots-Tag", "noindex, nofollow, noarchive")
    antwort.setHeader("Referrer-Policy", "no-referrer")
    antwort.setHeader("Cache-Control", "no-store, max-age=0, must-revalidate")

    /* Ohne Datei: die Seite. */
    if (!datei) {
        antwort.setHeader("Content-Type", "text/html; charset=utf-8")
        return antwort.end(await seite(`/cv/${encodeURIComponent(schluessel)}`))
    }

    const dokument = DOKUMENTE[datei]
    if (!dokument) {
        return nichtGefunden(antwort)
    }

    const daten = await unterlage(dokument)
    antwort.setHeader("Content-Type", "application/pdf")
    antwort.setHeader("Content-Disposition", `attachment; filename="${dokument.name}"`)
    antwort.setHeader("Content-Length", String(daten.length))
    antwort.end(daten)
}
