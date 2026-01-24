"""
Digital Business University of Applied Sciences 
Data Science und Management (M. Sc.) 
ADSC32 Applied Data Science III: Softwareparadigmen
Prof. Dr. Marcel Hebing
Julia Schmid (200022)


In dieser Datei werden die globalen Paramter definiert. 
"""

TAGE = 500  # Anzahl der zu durchlaufenden Tagen
START_JAHR = 2026 # Jahr in dem die Simulation startet --> Feiertage sind davon abhängig

# Haus mit 6 Wohnungen, in denen insgesamt 18 Personen wohnen
ANZAHL_BEWOHNER = 18
P_ABWESEND = 0.05 # Wahrscheinlichkeit, dass Bewohnerinnen und Bewohner außer Haus sind


# Szenario: Normales Müllaufkommen
# Durchschnittler Verbrauch pro Tag
# Quelle: Abfallwirtschaftsbetrieb München. Tonnen für Privathaushalte. Abgerufen am 12.01.2026 von https://www.awm-muenchen.de/abfall-entsorgen/muelltonnen/fuer-haushalte
DEFAULT_RESTMUELL_PRO_PERSON_TAG = 30/7  # Liter/Tag

# Handlungsoption: Kapazitätsausbau
# Quelle: Abfallwirtschaftsbetrieb München. Tonnen für Privathaushalte. Abgerufen am 12.01.2026 von https://www.awm-muenchen.de/abfall-entsorgen/muelltonnen/fuer-haushalte
REST_MUELLTONE_STAFFEL = [80, 120, 240, 770, 1100] # Mülltonnenkapazitaeten
REST_MUELLTONE_KOSTEN_STAFFEL = { # Kosten pro Tag für die verschiedenen kapazitaeten 
    80: round(177.84 / 52 / 7, 4), 
    120: round(230.88 / 52 / 7, 4), 
    240: round(382.20 / 52 / 7, 4), 
    770: round(1021.80 / 52 / 7, 4), 
    1100: round(1416.48 / 52 / 7, 4), }

# Handlungsoption: Sonderentleerung
SONDERENTLEERUNG_UEBERFUELLUNGSPROZENT = 80 # Bei Überfüllung von über 80% wird eine Sonderentleerung veranlasst

# --------------------------
# ---------- Ende ----------
# --------------------------