"""
Digital Business University of Applied Sciences 
Data Science und Management (M. Sc.) 
ADSC32 Applied Data Science III: Softwareparadigmen
Prof. Dr. Marcel Hebing
Julia Schmid (200022)


In dieser Datei wird der Start der Simulation ausgeführt.
"""

# -----------------------------
# ---------- Imports ----------
import os
# Globale Paramter importieren
from parameter import TAGE, START_JAHR, MIN_BEWOHNER, MAX_BEWOHNER,  DEFAULT_RESTMUELL_PRO_PERSON_TAG, REST_MUELLTONE_STAFFEL, REST_MUELLTONE_KOSTEN_STAFFEL, SONDERENTLEERUNG_UEBERFUELLUNGSPROZENT, SONDERENTLEERUNG_KOSTEN
from funktionen import summary_to_dataframe
from simulation import simulationslauf

ANZAHL_DURCHLAEUFE = 100

# ----------------------------------------------------
# ---------- Szenarien und Handlungsptionen ----------
# Szenarien: Normales Müllaufkommen, Besuch, Entsorgungsausfall
SZENARIEN = {
    "Normal": {"P_BESUCH": 0.30, "MAX_GAESTE": 10, "P_AUSFALL": 0.005},
    "Besuch": {"P_BESUCH": 0.55, "MAX_GAESTE": 10, "P_AUSFALL": 0.005},
    "Ausfall": {"P_BESUCH": 0.30, "MAX_GAESTE": 10, "P_AUSFALL": 0.02},
}

# Handlungsptionen: Keine Sondermaßnahmen, Sonderentleerung, Kapazitätsausbau
HANDLUNGSOPTIONEN = {
    "Keine Sondermaßnahmen": {"kapazitaet_ausbau": False, "sonderentleerung": False},
    "Kapazitaetsausbau": {"kapazitaet_ausbau": True, "sonderentleerung": False},
    "Sonderentleerung": {"kapazitaet_ausbau": False, "sonderentleerung": True},
}

if __name__ == "__main__": # Wird nur beim direkten Ausführen der Datei ausgeführt
    os.makedirs("output", exist_ok=True)
    print("[Info] Simulation gestartet.")
    summary = simulationslauf(SZENARIEN, HANDLUNGSOPTIONEN, durchlaeufe=10)
    df_results = summary_to_dataframe(summary)
    df_results.to_csv("output/simulation_ergebnisse.csv")
    print("[Info] Simulation beendet.")

# --------------------------
# ---------- Ende ----------
# --------------------------