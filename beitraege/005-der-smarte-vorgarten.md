---
title: "Der *smarte* Vorgarten"
slug: "005-der-smarte-vorgarten"
date: "2026-08-27"
category: "Smart Home"
lead: "Dunkle Ankunft, eine störanfällige Türklingel und ein Vorbeet mit ungebetenen Gästen – wie eine neue Video-Türklingel, ein Shelly und eine Standort-Automation in Home Assistant den Eingangsbereich smarter machen."
tags: "Smart Home, Home Assistant, Automatisierung, Reolink, Shelly"
draft: false
---

„Smarter Vorgarten“ ist ehrlicherweise ein wenig irreführend, denn es geht dabei nicht um einen Garten im klassischen Sinne. Vielmehr dreht sich alles um den Bereich vor der Haustür – und die Probleme, die dort gelöst werden wollten.

## Ausgangslage

In diesem Bereich gibt es eigentlich nur wenige Komponenten: eine smarte Türklingel, die Fassadenbeleuchtung und eine beleuchtete Hausnummer. Letztere beide wurden bislang über denselben Schalter bedient. Wichtig zu wissen: Die Haustür liegt von nachmittags bis Sonnenuntergang in der prallen Sonne, und vor dem Haus parken zwei PKW.

## Die Probleme

Jeder kennt es: Man kommt vom Einkaufen zurück, hat die Hände voll und muss trotzdem noch die Tür aufschließen. Oder man kommt abends beziehungsweise nachts nach Hause und tastet im Dunkeln nach Schlüssel und Schlüsselloch. Darüber hinaus war mir wichtig, mitzubekommen, wer an der Haustür klingelt oder sich auf dem Grundstück aufhält – vor allem in der Zeit, als regelmäßig ins Vorbeet gekotet wurde. All das waren Punkte, die mich störten und die ich angehen wollte.

## Meine Lösung

Die klassische Türklingel tauschte ich während der Sanierung gegen eine Ring-Türklingel aus, da der vorhandene Unterputz-Gong ohnehin überbrückt werden musste. Diese hatte allerdings regelmäßig Verbindungsprobleme und ließ sich nur schwer zuverlässig in Automationen einbinden – die Einbindung selbst funktionierte zwar, in der praktischen Ausführung gab es aber immer wieder Aussetzer. Deshalb ersetzte ich sie vor Kurzem durch eine Reolink Video Doorbell inklusive Chime. Als positiver Nebeneffekt kann ich die Aufzeichnungen nun lokal speichern und bin nicht mehr auf ein Abo angewiesen.

Auf der Hardwareseite habe ich zudem – beziehungsweise der Elektriker der Familie – einen Shelly 1 Mini Gen3 vor die Außenbeleuchtung geschaltet und den physischen Schalter stillgelegt.

Deutlich spannender sind aber die Lösungen über Automationen. Für das Problem mit der Dunkelheit beim Nachhausekommen habe ich eine Lösung gefunden, die ich selbst richtig clever finde: In Home Assistant habe ich einen Umkreis um unseren Wohnort definiert und diesen mit dem Standort meines iPhones verknüpft, das seine Position ebenfalls an Home Assistant sendet. So entstand eine Automation, die erkennt, wenn ich diesen Umkreis nach Sonnenuntergang betrete, und daraufhin automatisch die Außenbeleuchtung einschaltet. Das erleichtert sowohl das Einparken als auch die Schlüsselsuche. Ausgeschaltet wird das Licht anschließend per Sprachbefehl.

Um auch nachts zu sehen, wer das Grundstück betritt, könnte ich natürlich einfach die integrierte Nachtsicht der Reolink Video Doorbell nutzen – das wäre mir aber zu einfach gewesen. Stattdessen habe ich eine Automation gebaut, die bei erkannter Bewegung das Licht einschaltet. Dafür verwende ich keinen separaten Bewegungsmelder, sondern die Bewegungserkennung der Türklingel selbst. Nach dem Einschalten wartet die Automation zwei Minuten, bevor das Licht wieder ausgeht. Tückisch dabei: Die Türklingel reagierte so empfindlich, dass sie das Ausschalten des Lichts selbst wieder als Bewegung interpretierte und die Automation erneut auslöste. Aktuell umgehe ich das, indem die Automation erst reagiert, wenn eine Bewegung länger als fünf Sekunden anhält.

## Pläne für die Zukunft

Wer aufmerksam gelesen hat, wird bemerkt haben, dass das „Einkaufs-Szenario“ bislang ungelöst bleibt. Der Grund: Dafür wäre ein smartes Türschloss nötig, meine Frau ist von dieser Idee aber noch nicht ganz überzeugt. Im Auge habe ich bereits das Nuki Smart Lock Pro (Gen. 5).

Außerdem möchte ich prüfen, ob sich Fassadenbeleuchtung und Hausnummer künftig separat schalten lassen, da wir nicht immer beides gleichzeitig benötigen. Sollte dafür die Wand geöffnet und ein neues Kabel verlegt werden müssen, würde ich direkt auch ein LAN-Kabel für die Reolink mitverlegen, um ein weiteres Gerät vom WLAN unabhängig zu machen.

## Fazit

Es braucht nicht immer viel Hardware, um Alltagsprobleme zu lösen. Möglich waren meine herstellerübergreifenden Automationen natürlich nur dank Home Assistant – ich gehe aber davon aus, dass so etwas künftig dank Matter over Thread auch für deutlich mehr Menschen erreichbar wird, selbst wenn sie auf die Home-App oder vergleichbare Systeme setzen.

Ich bin schon gespannt, ob ich irgendwann ein Smart Lock montieren darf und welche neuen Möglichkeiten sich dadurch eröffnen.
