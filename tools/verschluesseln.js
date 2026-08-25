#!/usr/bin/env node
/**
 * Verschluesselt die aufbereiteten Bewerbungsunterlagen fuer das Repository.
 *
 * Aufruf:  node tools/verschluesseln.js
 *
 * Quelle:  api/_quelle/klar/   (lokal, in der .gitignore)
 * Ziel:    api/_quelle/*.bin   (im Repository)
 *
 * Das Repository ist oeffentlich. Die Unterlagen enthalten Anschrift,
 * Telefonnummer und Foto, sie duerfen dort nicht im Klartext liegen.
 * Verschluesselt wird mit AES-256-GCM; den Schluessel liest die Funktion
 * api/cv.js aus CV_DATEN_SCHLUESSEL.
 *
 * Aufbau einer .bin-Datei:  [12 Byte IV][16 Byte Auth-Tag][Chiffrat]
 */

const crypto = require("node:crypto")
const fs = require("node:fs")
const path = require("node:path")

const WURZEL = path.join(__dirname, "..")
const KLAR = path.join(WURZEL, "api", "_quelle", "klar")
const ZIEL = path.join(WURZEL, "api", "_quelle")

function schluesselLesen() {
    const datei = path.join(WURZEL, ".env.local")
    let wert = process.env.CV_DATEN_SCHLUESSEL
    if (!wert && fs.existsSync(datei)) {
        for (const zeile of fs.readFileSync(datei, "utf8").split(/\r?\n/)) {
            const treffer = zeile.match(/^CV_DATEN_SCHLUESSEL=(.+)$/)
            if (treffer) wert = treffer[1].trim()
        }
    }
    if (!wert) {
        console.error("CV_DATEN_SCHLUESSEL fehlt, weder in der Umgebung noch in .env.local")
        process.exit(1)
    }
    const roh = Buffer.from(wert, "base64")
    if (roh.length !== 32) {
        console.error("CV_DATEN_SCHLUESSEL muss 32 Byte lang sein, base64 kodiert")
        process.exit(1)
    }
    return roh
}

function main() {
    if (!fs.existsSync(KLAR)) {
        console.error("Klartext fehlt. Zuerst python tools/bewerbung.py aufrufen.")
        process.exit(1)
    }
    const schluessel = schluesselLesen()

    for (const name of fs.readdirSync(KLAR).sort()) {
        const quelle = path.join(KLAR, name)
        if (!fs.statSync(quelle).isFile()) continue

        const inhalt = fs.readFileSync(quelle)
        const iv = crypto.randomBytes(12)
        const chiffre = crypto.createCipheriv("aes-256-gcm", schluessel, iv)
        const daten = Buffer.concat([chiffre.update(inhalt), chiffre.final()])
        const paket = Buffer.concat([iv, chiffre.getAuthTag(), daten])

        const ziel = path.join(ZIEL, name + ".bin")
        fs.writeFileSync(ziel, paket)
        console.log(
            `  ${name.padEnd(26)} ${String(Math.round(inhalt.length / 1024)).padStart(4)} KB` +
            ` -> ${path.basename(ziel).padEnd(30)} ${String(Math.round(paket.length / 1024)).padStart(4)} KB`,
        )
    }
    console.log("\nDie Klartextdateien bleiben lokal, im Repository liegt nur das Chiffrat.")
}

main()
