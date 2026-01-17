"""
Digital Business University of Applied Sciences 
Data Science und Management (M. Sc.) 
ADSC32 Applied Data Science III: Softwareparadigmen
Prof. Dr. Marcel Hebing
Julia Schmid (200022)


In dieser Datei werden die Hilfunktionen definiert. 
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
# Globale Paramter importieren
from parameter import TAGE, START_JAHR, MIN_BEWOHNER, MAX_BEWOHNER,  DEFAULT_RESTMUELL_PRO_PERSON_TAG, REST_MUELLTONE_STAFFEL, REST_MUELLTONE_KOSTEN_STAFFEL, SONDERENTLEERUNG_UEBERFUELLUNGSPROZENT, SONDERENTLEERUNG_KOSTEN


"""
Funktion:           Bestimmung der Kosten bei Überfüllung
Input:              ueber_liter (Überfüllungsmenge in Liter)
Output:             kosten_sonderentleerung (berechnete Sonderkosten)
Funktionsweise:     Bei einer Überfüllung wird pro 70 Liter der Überfüllmenge 9 EUR berechnet.
"""
def sonderkosten_aus_ueberfuellung(ueber_liter):
    kosten_sonderentleerung = math.ceil(ueber_liter / 70) * 9 if ueber_liter > 0 else 0
    return kosten_sonderentleerung

"""
Funktion:           Bestimmung der Überfüllungsrate
Input:              abfallmenge (angefallene Abfallmenge in Liter), kapazitaet (maximale kapazitaet der Mülltonne)
Output:             rate (berechnete Überfüllungsrate in Prozent)
Funktionsweise:     Es wird Überfüllungsmenge in Liter bestimmt. 
                    Es gibt keine negative Überfüllungsmenge (wenn maximale kapazitaet nicht erreicht wurde).
                    Anschließend wird der Anteil der Überfüllung bestimmt (Übermenge/kapazitaet) in Prozent.
"""
def ueberfuellungsrate(fuellstand, kapazitaet):
    rate = max(0.0, (fuellstand - kapazitaet) / kapazitaet * 100)
    return rate


"""
Funktion:           Bestimmung der Feiertage, auf denen der Leertag fällt.
Input:              leertag (Wochentag in dem die Mülltonnenleerung staatfindet), tage (Anzahl der Tage, die in der Simulation betrachtet werden), START_YEAR (das Jahr in dem die Simulation beginnt)
Output:             feiertage (Liste der Feiertage auf denen der Leertag fällt)
Funktionsweise:     Abhängig von der betrachteten Tage, wird die anzahl der betrachetetn Jahre bestimmt.
                    Für jedes betrachtete Jahr werden die Feiertage bestimmt. Es wird angenommen, dass das Wohnhaus in München, Bayern steht. Dadurch gelten die bayerischen Feiertage.
                    Bei den einzelnen Feiertagen wird geprüft ob dieser auf den Wochentag des Leertages fällt. Nur jene Feiertage die auf den Leertag fällt, wird der Feiertagsliste hinzugefügt.
"""
def berechne_feiertage(leertag, tage, start_jahr):
    start_date = date(start_jahr, 1, 1)
    feiertage = holidays.Germany(years=start_jahr, subdiv="BY")
    return {
        start_date + timedelta(days=t)
        for t in range(tage)
        if (start_date + timedelta(days=t)).weekday() == leertag
        and (start_date + timedelta(days=t)) in feiertage
    }

"""
Funktion:           Berechnung der Statistiken für die Metriken
Input:              ergebnisse (Simulationsergebnisse)
Output:             statstiken (Statistik-Werte der einzelnen Metriken)
Funktionsweise:     Für die Numerischen-Metriken wird der Durschnitt, der Maximal-Wert, der Minimal-Wert sowie die Standarfabweichung bestimmt und zurückgegeben.
                    Für die Boolean Metrik wird die Anzahl der Fälle und die Quote bestimmt.
"""
def berechnung_statistiken(ergebnisse):

    statstiken = {}

    metriken = [k for k in ergebnisse[0].keys()] 

    for metrik in metriken:
        # Zusammenführung der Werte zu einer gesamten Liste
        werte = []
        for ergebnis in ergebnisse:
            werte.extend(ergebnis[metrik])

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
            "Min-Wert": round(min(werte),3),
            "Max-Wert": round(max(werte), 3),
            "Standard Abweichung": round(stats.stdev(werte), 3) if len(werte) > 1 else 0.0,
        }

    return statstiken

"""
Funktion:           Erstellung eines Histogramms für die Metriken Gesamtkosten und Müllaufkommen. 
Input:              ergebnisse (Simulationsergebnisse), szenario_name (Szenarioname), handlungsoption_name (Handlungsoptionsname)
Funktionsweise:     Für die beiden Metriken kosten_tag (Gesamtkosten) und fuellmenge_tag (Müllaufkommen) wird ein Histogramm über die gesamte Simulation erstellt und als png gespeichert.
"""
def grafik_histogramme(ergebnisse, szenario_name, handlungsoption_name):
    gesamtkosten = [sum(e["kosten_tag"]) for e in ergebnisse] # TODO: Nicht summe!!
    gesamtmuell = [sum(e["fuellmenge_tag"]) for e in ergebnisse]

    list_plot_info = [
        (gesamtkosten, "Gesamtkosten", "EUR", "gesamtkosten"),
        (gesamtmuell, "Müllaufkommen", "Liter", "gesamtmuell"),
    ]

    for daten, titel, xlabel, metrik in list_plot_info:
        plt.figure(figsize=(10, 6))
        plt.hist(daten, bins=40)
        plt.xlabel(xlabel)
        plt.ylabel("Häufigkeit")
        plt.title(f"{titel} \nSzenario = {szenario_name} | Handlungsoption = {handlungsoption_name}")
        plt.savefig(os.path.join("output",f"histogramm_{metrik}_{szenario_name}_{handlungsoption_name}.png"))
        plt.close()



"""
Funktion:           Die Ergebnisse werden in einem DataFrame formartiert und als csv gespeichert.
Input:              results_summary (Simulationsergebnisse)
Output: 
Funktionsweise:     
"""
def summary_to_dataframe(results_summary):
    records = []
    for (szenario, handlungsoption), stats_dict in results_summary.items():
        for metrik, kennzahlen in stats_dict.items():
            for kennzahl, wert in kennzahlen.items():
                records.append(
                    {
                        "Metrik": metrik,
                        "Kennzahl": kennzahl,
                        "Szenario": szenario,
                        "Handlungsoption": handlungsoption,
                        "Wert": wert,
                    }
                )

    df = pd.DataFrame(records)
    return df.pivot_table(
        index=["Metrik", "Kennzahl"],
        columns=["Szenario", "Handlungsoption"],
        values="Wert",
    )


# --------------------------
# ---------- Ende ----------
# --------------------------