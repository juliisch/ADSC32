"""
Digital Business University of Applied Sciences 
Data Science und Management (M. Sc.) 
ADSC32 Applied Data Science III: Softwareparadigmen
Prof. Dr. Marcel Hebing
Julia Schmid (200022)


In dieser Datei werden die globalen Paramter definiert. 
"""

TAGE = 500  # Anzahl der zu durchlaufenden Tagen
START_JAHR = 2026 # Jahr in dem die Simulation startet. Davon sind die Feiertage abhängig.

# Haus mit 6 Wohnungen, in denen maximal 3 Personen (18 in Summe) wohnen können.
# Es wird angenommen, dass mindestens eine Person pro Wohnung wohnt.
MAX_BEWOHNER = 18
MIN_BEWOHNER = 6

# Szenario: Besuch
# Maximale Anzahl an Gästen
DEFAULT_MAX_GAESTE = 10
# Schwellenwert für Besuch 
DEFAULT_P_BESUCH = 0.30

# Szenario: Entsorgungsausfall
# Schwellenwert für Ausfall
DEFAULT_P_AUSFALL = 0.005

# Szenario: Normales Müllaufkommen
# Durchschnittler Verbrauch pro Tag
DEFAULT_RESTMUELL_PRO_PERSON_TAG = 30/7  # Liter/Tag
# Quelle: https://www.awm-muenchen.de/abfall-entsorgen/muelltonnen/fuer-haushalte

# Handlungsoption: Kapazitätsausbau
REST_MUELLTONE_STAFFEL = [80, 120, 240, 770, 1100] # Mülltonnenkapazitaeten
REST_MUELLTONE_KOSTEN_STAFFEL = { # Kosten pro Tag für die verschiedenen kapazitaeten
    80: round(177.84 / 52 / 7, 4),
    120: round(230.88 / 52 / 7, 4),
    240: round(382.20 / 52 / 7, 4),
    770: round(1021.80 / 52 / 7, 4),
    1100: round(1416.48 / 52 / 7, 4),
}

# Handlungsoption: Sonderentleerung
SONDERENTLEERUNG_UEBERFUELLUNGSPROZENT = 90 # Bei Überfüllung von über 90% wird eine Sonderentleerung veranlasst
SONDERENTLEERUNG_KOSTEN = 50 # Kosten der Sonderentleerung

# --------------------------
# ---------- Ende ----------
# --------------------------