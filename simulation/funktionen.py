"""
Digital Business University of Applied Sciences 
Data Science und Management (M. Sc.) 
ADSC32 Applied Data Science III: Softwareparadigmen
Prof. Dr. Marcel Hebing
Julia Schmid (200022)


In dieser Datei sind die Hilfunktionen definiert. 
"""

# -----------------------------
# ---------- Imports ----------
import math
import holidays
import statistics as stats
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import date, timedelta
import matplotlib.image as mpimg
from pathlib import Path
# Globale Paramter importieren
from parameter import TAGE, START_JAHR,  P_ABWESEND, DEFAULT_RESTMUELL_PRO_PERSON_TAG, REST_MUELLTONE_STAFFEL, REST_MUELLTONE_KOSTEN_STAFFEL, SONDERENTLEERUNG_FUELLMENGE_PROZENT


"""
Funktion:           Berechnet die Zusatzkosten bei Überfüllung einer Restmülltonne
Input:              ueber_liter (Überfüllungsmenge in Liter)
Output:             kosten_sonderentleerung (Kosten der Überfüllung)
Funktionsweise:     Bei einer Überfüllung werden pro angefangene 70 Liter der Überfüllmenge 9 EUR berechnet.

# Quelle: Abfallwirtschaftsbetrieb München. Tonnen für Privathaushalte. Abgerufen am 12.01.2026 von https://www.awm-muenchen.de/abfall-entsorgen/muelltonnen/fuer-haushalte
"""
def sonderkosten_aus_ueberfuellung(ueber_liter):
    kosten_sonderentleerung = math.ceil(ueber_liter / 70) * 9 if ueber_liter > 0 else 0
    return kosten_sonderentleerung



"""
Funktion:           Berechnet die Überfüllungsrate der Restmülltonne in Prozent
Input:              fuellstand (Füllstand der Restmülltonne in Litern)
                    kapazitaet (Kapazität der Restmülltonne in Litern)
Output:             rate (Überfüllungsrate in Prozent)
Funktionsweise:     Es wird zunächst die Überfüllungsmenge in Liter bestimmt (Übermenge = Füllstand - Kapazität). 
                    Es gibt keine negative Überfüllungsmenge (entsteht, wenn die maximale kapazitaet nicht erreicht wurde). Negative Werte werden bei 0 gekappt.
                    Anschließend wird der Anteil der Überfüllung bestimmt (Übermenge/Kapazität) in Prozent.
"""
def ueberfuellungsrate(fuellstand, kapazitaet):
    rate = max(0.0, (fuellstand - kapazitaet) / kapazitaet * 100)
    return rate



"""
Funktion:           Bestimmung aller Feiertage, die auf den Leertag fallen.
Input:              leertag (Wochentag, an dem die Müll geleert wird)
                    tage (Anzahl der Tage, die in der Simulation betrachtet werden)
                    start_jahr (das Jahr in dem die Simulation beginnt)
Output:             leertag_feiertage (Liste der Feiertage, auf denen der Leertag fällt)
Funktionsweise:     Abhängig von der betrachteten Tage, wird der betrachtete Zeitraum bestimmt.
                    Für jedes betrachtete Jahr werden die Feiertage bestimmt. 
                    Es wird angenommen, dass das Wohnhaus in München, Bayern steht. 
                    Dadurch gelten die bayerischen Feiertage.
                    Für jeden Tag wird geprüft, ob dieser auf den Leertag fällt und es sich um einen Feiertag fällt. 
                    Jene Tage, für welche beiden Bedingungen erfüllt sind, wird das Datum in die Ausgabeliste hinzugefügt.
"""
def berechne_feiertage(leertag, tage, start_jahr):
    start_date = date(start_jahr, 1, 1) # Startdatum
    feiertage = holidays.Germany(years=start_jahr, subdiv="BY") # Liste der bayerischen Feiertage
    leertag_feiertage = set()

    for t in range(tage): # Prüfung der einzelnen Tage
        aktuelles_datum = start_date + timedelta(days=t)

        if aktuelles_datum.weekday() == leertag and aktuelles_datum in feiertage: # Tag ist Leertag und Feiertag
            leertag_feiertage.add(aktuelles_datum) # Tag wird in die Ausgabeliste hinzugefügt

    return leertag_feiertage




"""
Funktion:           Berechnung der Statistiken für die einzelnen Metriken
Input:              ergebnisse (Liste der Simulationsergebnisse)
Output:             statstiken (Statistik-Werte der einzelnen Metriken)
Funktionsweise:     Für die numerische Metriken wird der Durschnitt, der Maximalwert sowie der Minimalwert berechnet.
                    Für die Boolean Metrik wird die Anzahl der Ausfallfälle und die Quote in Prozent berechnet.
"""
def berechnung_statistiken(ergebnisse):

    statstiken = {}

    # Metriken der Simulationsergebnisse
    metriken = [k for k in ergebnisse[0].keys()] 

    for metrik in metriken:
        

        # Zusammenführung der Werte zu einer gesamten Liste
        werte = []
        for ergebnis in ergebnisse:
            werte.extend(ergebnis[metrik])

        metrik = metrik.removesuffix("_tag") # Suffix entfernen (für eine schönere Ausgabe)

        # Boolean Metrik (ausfall_tag)
        if werte and isinstance(werte[0], bool):
            statstiken[metrik] = {
                "Anzahl Ausfälle": sum(werte),
                "Quote": round((sum(werte) / len(werte)*100), 3),  
            }
            continue

        # Numerische Metrik
        statstiken[metrik] = {
            "Durchchschnitt": round(stats.mean(werte),3),
            "Minimalwert": round(min(werte),3),
            "Maximalwert": round(max(werte), 3),
        }

    return statstiken



"""
Funktion:           Erstellung eines Histogramms für die Metriken Gesamtkosten und Gesamtmüllmenge
Input:              ergebnisse (Simulationsergebnisse)
                    szenario_name (Szenarioname)
                    handlungsoption_name (Handlungsoptionsname)
Funktionsweise:     Für die beiden Metriken kosten_tag (Gesamtkosten) und muellmenge_tag (Gesamtmüllmenge) werden die gesamten Simulationswerte aggregiert.
                    Für jede Metrik wird ein Histogramm erzeugt und als PNG-Datei gespeichert
"""
def grafik_histogramme(ergebnisse, szenario_name, handlungsoption_name):
    # Aggregation der Werte
    gesamtkosten = [sum(ergebnis["kosten_tag"]) for ergebnis in ergebnisse]  #Gesamtkosten
    gesamtmuell = [sum(ergebnis["muellmenge_tag"]) for ergebnis in ergebnisse] # Gesamtmüllmenge

    list_plot_info = [
        (gesamtkosten, "Gesamtkosten", "EUR", "gesamtkosten"),
        (gesamtmuell, "Gesamtmüllmenge", "Liter", "gesamtmuell"),
    ]

    # Histogramm
    for daten, titel, xlabel, metrik in list_plot_info:
        plt.figure(figsize=(10, 6))
        plt.hist(daten, bins=40)
        plt.xlabel(xlabel)
        plt.ylabel("Häufigkeit")
        plt.title(f"{titel} \nSzenario = {szenario_name} | Handlungsoption = {handlungsoption_name}")
        plt.savefig(os.path.join("output",f"histogramm_{metrik}_{szenario_name}_{handlungsoption_name}.png")) # Bild speichern
        plt.close()



"""
Funktion:           Die Simulationsergebnisse werden in einem DataFrame formartiert.
Input:              results_summary (zusammengefasste Simulationsergebnisse)
Output:             df_out (tabellarische Simulationsergebnisse)
Funktionsweise:     Die Ergebnisstruktur wird in eine flache Struktur überführt.
                    Anschließend werden die Werte in einen DataFrame umgewandelt und in eine Pivot-Tabelle umstrukturiert.
"""
def ausgabe_csv(results_summary):
    element = []
    for (szenario, handlungsoption), stats_dict in results_summary.items():
        for metrik, kennzahlen in stats_dict.items():
            for kennzahl, wert in kennzahlen.items():
                element.append({
                        "Metrik": metrik,
                        "Kennzahl": kennzahl,
                        "Szenario": szenario,
                        "Handlungsoption": handlungsoption,
                        "Wert": wert,
            })

    df_out = pd.DataFrame(element)
    df_out = df_out.pivot_table(index=["Metrik", "Kennzahl"], columns=["Szenario", "Handlungsoption"],values="Wert")
    return df_out



"""
Funktion:           Zusammenführung der einzelnen Histogramme zu einer Gesamtgrafik
Input:              metrik_name (Name der Metrik)
Funktionsweise:     Für alle erzeugten Grafiken der Gesamtkosten und Gesamtmüllmenge werden die Kombinationen aus Szenarien und Handlungsoptionen pro Metrik geladen und in einer 3×3-Subplot-Grafik zusammengeführt und gespeichert.
"""
def gerniere_subplot(metrik_name):

    szenarien = ["Normal", "Besuch", "Ausfall"]
    handlungsoptionen = ["feste Abholintervalle","Kapazitaetsausbau", "Sonderentleerung"]

    fig, axes = plt.subplots(nrows=3, ncols=3, figsize=(20, 10))

    for z, zustand in enumerate(szenarien):
        for m, massnahme in enumerate(handlungsoptionen):
            ax = axes[z, m]

            img_path =  f"output/histogramm_{metrik_name}_{zustand}_{massnahme}.png" # Bild laden

            img = mpimg.imread(img_path)
            ax.imshow(img)
            ax.axis("off")

            # Spalten Titel
            if z == 0:
                ax.set_title(massnahme, fontsize=12)

    plt.tight_layout()
    plt.savefig(os.path.join("output",f"histogramm_{metrik_name}.png")) # Bild speichern

# --------------------------
# ---------- Ende ----------
# --------------------------