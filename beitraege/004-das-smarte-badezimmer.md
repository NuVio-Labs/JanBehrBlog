---
title: "Das *smarte* Badezimmer"
slug: "004-das-smarte-badezimmer"
date: "2026-08-26"
category: "Smart Home"
lead: "Heizung, Lüfter und Licht liefen im Bad bislang unabhängig voneinander. Mit smartem Thermostat, Sensoren und ein paar Automationen wird daraus ein System, das mitdenkt."
tags: "Smart Home, Home Assistant, Zigbee, Automatisierung, SONOFF"
draft: false
---

## Einleitung

Nachdem das Erdgeschoss saniert war, hielt ich Ausschau nach Problemen, die sich mit SmartHome-Technik lösen ließen. Fündig wurde ich direkt in einem Raum mit gleich mehreren Baustellen: dem Badezimmer.

## Die Ausgangslage

Unser Badezimmer besteht aus Toilette, Waschbecken, Dusche, Handtuchheizkörper und Lüfter, dazu kommt ein Tageslichtfenster. Zu Beginn war die Heizung mit einem klassischen Heizkörperthermostat ausgestattet, der Lüfter wurde ganz herkömmlich über einen Schalter bedient.

## Das Problem

Für mich ist das Badezimmer der anspruchsvollste Raum im Haus. Er sollte bei Nutzung angenehm temperiert sein, dabei aber möglichst wenig Energie verbrauchen, wenn er gerade nicht gebraucht oder gelüftet wird. Die Luftfeuchtigkeit darf nicht zu hoch steigen, um Schimmelbildung vorzubeugen – ist aber naturgemäß höher als in anderen Räumen. Interessanterweise ist es zudem der Raum, in dem am häufigsten vergessen wird, das Licht auszuschalten, und auch der Lüfter lief bislang entweder zu kurz oder deutlich zu lang.

## Meine Lösung

Als Erstes tauschte ich das klassische Heizthermostat gegen ein smartes Modell von SONOFF (TRVZB) aus, ergänzt um einen Temperatur- und Luftfeuchtigkeitssensor (SNZB-02D). Für SONOFF entschied ich mich, weil es mir empfohlen wurde, kostengünstig ist und sich über Zigbee ansteuern lässt. Dazu installierte ich den Fenstersensor Parasoll von IKEA – hier war tatsächlich vor allem der Preis ausschlaggebend. Mit diesen drei Komponenten ließen sich bereits mehrere Probleme lösen: Zum einen richtete ich eine Automation ein, die nur heizt, sobald die Temperatur unter einen festgelegten Wert fällt. Statt direkt auf die Werte von Thermostat oder Temperatursensor zuzugreifen, nutze ich dafür den Mittelwert beider Sensoren, um ein präziseres Ergebnis zu erzielen. Zusätzlich schaltet sich die Heizung sofort ab, sobald das Fenster geöffnet wird, und wieder ein, sobald es geschlossen ist.

Das Problem mit dem falsch laufenden Lüfter löste ich mit einem Shelly 1PM Mini Gen4. Ein Familienmitglied, gelernter Elektriker, hatte diesen zunächst nur zwischengeschaltet, da meine Frau grundsätzlich alles im Haus auch analog bedienen können möchte. Da das ursprüngliche Problem dadurch aber weiterbestand, haben wir die Wippe des Lichtschalters stillgelegt, sodass der Shelly nun ausschließlich per Sprachassistent oder Automation gesteuert wird. Die Automation sorgt dafür, dass der Lüfter je nach Luftfeuchtigkeit ein- oder ausgeschaltet wird.

Auch das Thema Licht ließ sich mit einem Shelly 1PM Mini Gen3 lösen – dieser bleibt aber sowohl per Sprachassistent als auch über den klassischen Schalter bedienbar. Im Alltag nutzen wir fast ausschließlich den Schalter; nur wenn wir vergessen haben, das Licht auszuschalten, kommt die Sprachsteuerung zum Einsatz.

## Pläne für die Zukunft

Um Ressourcen zu schonen, wollte ich sämtliche Geräte mit wiederaufladbaren Batterien betreiben. Das führte allerdings dazu, dass sich diese ungewöhnlich schnell entluden und regelmäßig ausgetauscht werden mussten – was wiederum zur Folge hatte, dass das Heizthermostat immer wieder neu eingebunden werden musste. Woran das genau liegt, ist mir bis heute nicht klar. Auch bei Softwareupdates machte mir das Thermostat Probleme: Diese brachen immer wieder ohne erkennbaren Grund ab. Aus diesem Grund halte ich für künftige Heizkörper bereits nach Alternativen ausschau und betreibe alle Geräte mit normalen Batterien.

Auch das Thema Energiesparen konnte ich durch die aktuelle Automation nur bedingt lösen, da sie an die Raumtemperatur gekoppelt ist und nicht an die tatsächliche Nutzung des Badezimmers. Für die Zukunft plane ich daher den Einsatz eines Präsenzsensors – diesen möchte ich künftig auch für die Lichtsteuerung nutzen, um die Automation weiter zu optimieren.

## Fazit

Abgesehen vom noch fehlenden Präsenzsensor läuft das Setup mittlerweile stabil und sorgt dafür, dass wir spürbar weniger Energie verschwenden und die Luftfeuchtigkeit dauerhaft in einem vernünftigen Bereich bleibt. Mit dem geplanten Präsenzsensor und einem neuen Thermostat soll das Projekt in Zukunft abgerundet werden.
