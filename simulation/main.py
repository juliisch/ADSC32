"""
Digital Business University of Applied Sciences 
Data Science und Management (M. Sc.) 
ADSC32 Applied Data Science III: Softwareparadigmen
Prof. Dr. Marcel Hebing
Julia Schmid (200022)

Diese Datei beinhaltet den Simulationsstart. Zum Starten der Simulation muss die Datei ausgeführt werden.
"""

# -----------------------------
# ---------- Imports ----------
import os
# Globale Paramter importieren
from parameter import TAGE, START_JAHR, ANZAHL_BEWOHNER, P_ABWESEND,  RESTMUELL_MENGE_PRO_PERSON_TAG, REST_MUELLTONE_STAFFEL, REST_MUELLTONE_KOSTEN_STAFFEL, SONDERENTLEERUNG_FUELLMENGE_PROZENT
from funktionen import ausgabe_csv, gerniere_subplot
from simulation import simulationslauf

# ----------------------------------------------------
# ---------- Szenarien und Handlungsptionen ----------
# Szenarien: 
# - Normales Müllaufkommen (Besuch = 2 Tage im Monat = 24 Tage im Jahr --> 7 Prozent, 3 Ausfälle pro Jahr --> 0.8 Prozent)
# - erhöhter Besuch (4 Tage im Monat = 48 Tage im Jahr --> 13 Prozent)
# - erhöhte Ausfallwahrscheinlichkeit der Entsorgung (5 Ausfälle pro Jahr --> 1.4 Prozent)
SZENARIEN = {
    "Normal": {"P_BESUCH": 0.07,  "P_AUSFALL": 0.008},
    "Besuch": {"P_BESUCH": 0.13,  "P_AUSFALL": 0.008},
    "Ausfall": {"P_BESUCH": 0.07, "P_AUSFALL": 0.014},
}

# Handlungsptionen: 
# - feste Abholintervalle 
# - Sonderentleerung
# - Kapazitätsausbau
HANDLUNGSOPTIONEN = {
    "feste Abholintervalle": {"kapazitaetsausbau": False, "sonderentleerung": False},
    "Kapazitaetsausbau": {"kapazitaetsausbau": True, "sonderentleerung": False},
    "Sonderentleerung": {"kapazitaetsausbau": False, "sonderentleerung": True},
}


# --------------------------------
# ---------- Simulation ----------
ANZAHL_DURCHLAEUFE = 1000 # Anzahl der Simulationsdurchläufe


if __name__ == "__main__": 
    os.makedirs("output", exist_ok=True) # Output-Ordner anlegen (falls nicht schon vorhanden ist) zur Speicherung der Ergebnisdateien (Bilder, CSV)
    print("[Info] Simulation gestartet.")
    # Simulation
    summary = simulationslauf(SZENARIEN, HANDLUNGSOPTIONEN, ANZAHL_DURCHLAEUFE) 
    # Simulationsergebnisse
    df_results = ausgabe_csv(summary) 
    df_results.to_csv("output/simulation_ergebnisse.csv") # Speicherung der Ergebnistabelle als CSV
    print("[Info] Simulation beendet.")

    # Die einzelnen Plots der Gesamtkosten und der Gesamtfüllmenge werden in einem 3x3 Plot gespeichert
    gerniere_subplot("gesamtkosten")
    gerniere_subplot("gesamtfuellmenge")

# --------------------------
# ---------- Ende ----------
# --------------------------