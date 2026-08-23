---
title: "Projekt *Netzwerkschrank*"
slug: "001-projektdokumentation-netzwerkschrank"
date: "2026-08-21"
category: "Projekttagebuch"
lead: "Von der Montage bis zur Fehlersuche: die vollständige Dokumentation, wie 16 CAT7-Leitungen aus dem Keller in einen 19-Zoll-Schrank gewandert sind."
tags: "Netzwerkschrank, Patchpanel, CAT7, Dokumentation, Home Assistant"
draft: false
---

## Einleitung

Im Rahmen einer Sanierung des Erdgeschosses meines Eigenheims im Jahr 2022 wurden alle Räume des Erd- und Obergeschosses mit Cat7-Netzwerkkabel ausgestattet (insgesamt 16 Leitungen). Die Kabel des Erdgeschosses wurden schon während der Sanierung an Netwerkdosen angeschlossen, die für das Obergeschoss liegen, in einem Kabelkanal versteckt, auf der Etage und werden angeschlossen, sobald das Obergeschoss saniert wird. Die Enden der anderen Seite lagen bis Anfang 2025 offen in einem Kellerraum, was sich mit diesem Projekt geändert hat.

## Verwendete Komponenten

- Netzwerkschrank: HMF 66409-02, 19 Zoll, 9 HE, 450mm tiefe
- Switch: Netgear ProSafe JGS524, 24 Ports
- Patchpanel: deleyCON CAT6a, 24 Ports
- Router: Zu Beginn Telekom Speedport Smart 4, aktuell FRITZ!Box 7590
- Netzwerkkabel: deleyCON 0,25m CAT7 Netzwerkkabel
- Steckerleiste: kwmobile 19 Zoll PDU Steckdosenleiste, 7-fach, Überlastungsschutz
- Home Assistant:
  - Home Assistant Green
  - Home Assistant ZBT-1
  - Home Assistant Sky Connect
- Sonstiges:
  - LogiLink Professional LSA Auflegewerkzeug
  - Mcbazel Netzwerk RJ45 Tester
  - JOKARI T30150 Vielzweckisoliermesser

## Ablauf

### Vorbereitung

Da mir jegliches Vorwissen fehlte, schaute ich mir einige Videos auf der Plattform Youtube an und informierte mich zu gängigen Standards. Zum Lieferumfang des Patch-Panels gehörte auch eine Anleitung, welche ich während der Umsetzung kontinuierlich zur Hand hatte. Ein Elektriker legte mir zudem eine separate Stromleitung inklusive Steckdose, welche im Sicherungskasten mit einer eigenen Sicherung angeschlossen wurde. Zuletzt hielt ich Rücksprache mit dem Monteur der Netzwerkdosen, um den verwendeten Standard zu erfragen.

### Montage des Netzwerkschranks

Die Bohrlochmarkierungen habe ich mit Hilfe der mitgelieferten Montageschablone an die Wand gezeichnet, mit einem 9er Bohrer gebohrt und mit 10er Dübel befüllt. Im nächsten Schritt mussten die Kabelzugänge mit einem Seitenschneider geöffnet werden. Um eine Beschädigung der Kabel durch scharfe Kanten vorzubeugen, schnitt ich vier flexible Kabelrohre auf ein passendes Maß, öffnete sie an einer Seite und stülpte sie über die Längsseite der Kabelzugänge. Im letzten Schritt montierte ich den Netzwerkschrank mit passenden Schrauben an der Wand und demontierte die Seitenwände und die Glastür, um den Arbeitsbereich zu vergrößern. Dieser erste Teil ging mir leicht von der Hand und verlief ohne Probleme.

### Auflegung der Netzwerkkabel auf das Patchpanel

Zu Beginn erstelle ich eine Exsl-Datei, um die genaue Belegung der Kabel zu dokumentieren. Dabei half die Beschriftung, welche schon während der Sanierung vorgenommen wurde, ungemein. Im zweiten Schritt kürzte ich die Kabel ein, achtete aber darauf genug Kabellänge in der Reserve zu haben, um nicht in Bedrängnis zu geraten und auch in der Zukunft Änderungen vornehmen zu können. Anschließend führte ich die Kabel dem Netzwerkschrank hinzu und bildete Kabelschlaufen, um Ordnung zu schaffen und Platz zu sparen. Im dritten Schritt entmantelte ich ein Kabel mit dem JOKARI (ca. 5cm), legte die Ader offen ohne die Schirmung zu beschädigen und legte die Adern nach europäischem Standard (TIA-568B) mit dem LSA-Werkzeug auf. Des Weiteren kürzte ich die Schirmung so weit ein, dass ich sie über die Adern legen konnte und befestigte das Kabel zusätzlich zur Klemme mit einem Kabelbinder, um Zugbewegungen entgegenzuwirken. Dies wiederholte ich mit den verbliebenen 15 Kabeln und notierte die Belegung in der Dokumentation. Anfänglich hatte ich Schwierigkeiten im Umgang mit dem LSA-Werkzeug, dies legte sich allerdings mit Einsetzen der Routine. Diese Routine führte gelegentlich dazu, dass ich Fehler in der Farbreihenfolge gemacht, aber stets sofort bemerkt und behoben habe.

### Kontrolle der Netzverbindung

In diesem Schritt habe ich die Verbindung vom Patchpanel zur Dose mithilfe des Netzwerktesters von Mcbazel getestet. Jeder Port zeigte bei der Messung einen Fehler an, was mich ehrlicherweise sehr wunderte. Nachdem ich mich versichert habe, dass ich das Test-Gerät richtig verwendet habe und auch die Belegung auf dem Patchpanel keine Fehler aufwies, wurde mir das Problem schnell klar. Der Monteur der Netzwerkdosen teilte mir auf Nachfrage mit, dass er die Dosen nach C-Standard aufgelegt hat. Zu dem Zeitpunkt des Gesprächs hielt ich die Antwort für einen Spaß, musste aber feststellen, dass die Adern tatsächlich nach einem erfundenen C-Standard aufgelegt waren (der Monteur war kein Fachmann). Dies bedeutete für mich, dass ich jede Netzwerkdose neu auflegen musste, was sich aufgrund von fehlender Kabellänge als schwierig darstellte. Dennoch gelang es mir und ich konnte anschließend fast alle Verbindungen testen ohne Fehler zu erhalten. Einzig eine einzige Leitung zeigte einen Fehler. Laut Gebrauchsanleitung des Geräts handelte es sich um eine Art Kurzschluss. Es folgten zwei Stunden Fehlersuche bis ich herausfand, dass der Kurzschluss nur gemessen wurde, wenn die Metalloberfläche der Dose montiert war. Mit dieser Erkenntnis und Vorwissen aus der Schulzeit fand ich schnell heraus, dass ich eine Ader am Patchpanel nicht richtig eingekürzt habe und diese Ader Kontakt zum Gehäuse des Patchpanels hatte. Nachdem dies ebenfalls behoben war, konnte ich alle Verbindungen fehlerlos testen und das Patchpanel im Netzwerkschrank einbauen. Dieser Teilschritt war der herausforderndste, da ich hier keine Anleitung hatte, sondern durch Try & Error auf Fehlersuche gehen musste. Diese Herausforderung legte allerdings auch den Grundstein dafür, dass ich mir heute vorstellen kann diese und ähnliche Tätigkeiten beruflich auszuüben.

### Einbau der weiteren Komponenten

Nachdem das Patchpanel montiert war, montierte ich den Switch unterhalb des Patchpanels, verband beide Geräte Port für Port und schloss die Netzwerkkabel für den Router und den Home Assistant an. Mit einem Abstand von zwei Höheneinheiten folgte die Steckdosenleiste mit Überlastungsschutz. An diese schloss ich den Switch, den Router und den Home Assistant an um die Geräte in Betrieb zu nehmen. Zudem schloss ich den Home Assistant samt Sky Connect und ZBT-1 an das Netzwerkabel an und stellte die Verbindung von TAE-Dose zum Router und von Router zu Switch her. Dieser letzte Schritt war für mich ein angenehmer Abschluss für dieses Projekt, weil auch dies ohne Probleme ablief. Da der Home Assistant schon seit einiger Zeit in Betrieb war, musste ich diesen nicht mehr einrichten.

### Aktueller Stand

Prinzipiell ist der Netzwerkschrank noch genauso bestückt wie nach der Inbetriebnahme mit Ausnahme des Routers. Die Telekom Speedport Smart 4 wurde mittlerweile durch eine FRITZ!Box 7590 ersetzt. Derzeit plane ich den Netzwerkschrank umzurüsten, da ich mein Netzwerk sicherer gestalten möchte und der aktuelle Router sowie der Switch nicht zu meinen Ansprüchen passen. Darüber berichte ich in einem der nächsten Projektdokumentationen.
