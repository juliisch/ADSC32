"""
Digital Business University of Applied Sciences 
Data Science und Management (M. Sc.) 
ADSC32 Applied Data Science III: Softwareparadigmen
Prof. Dr. Marcel Hebing
Julia Schmid (200022)


In dieser Datei werden die globalen Paramter definiert. 
"""

TAGE = 500  # Anzahl der Tage, die in der Simulation betrachtet werden
START_JAHR = 2026 # Startjahr der Simulation --> Feiertage sind davon abhängig

# Haus mit 6 Wohnungen und insgesamt 18 Bewohner und Bewohnerinnen
ANZAHL_BEWOHNER = 18
P_ABWESEND = 0.05 # Wahrscheinlichkeit, dass ein Bewohner oder Bewohnerin nicht im Haus ist

# Szenario: Normales Müllaufkommen
# Durchschnittler Restmüllaufkommen pro Person und Tag
# Quelle: Abfallwirtschaftsbetrieb München. Tonnen für Privathaushalte. Abgerufen am 12.01.2026 von https://www.awm-muenchen.de/abfall-entsorgen/muelltonnen/fuer-haushalte
DEFAULT_RESTMUELL_PRO_PERSON_TAG = 30/7  # Liter/Tag und Person

# Handlungsoption: Kapazitätsausbau
# Verfügbare Tonnenkapazitäten (in Liter) und Tonnenkosten pro Tag
# Quelle: Abfallwirtschaftsbetrieb München. Tonnen für Privathaushalte. Abgerufen am 12.01.2026 von https://www.awm-muenchen.de/abfall-entsorgen/muelltonnen/fuer-haushalte
REST_MUELLTONE_STAFFEL = [80, 120, 240, 770, 1100] # Liste der verschiedenen Mülltonnenkapazitaeten
REST_MUELLTONE_KOSTEN_STAFFEL = { # Tageskosten je Tonnengröße 
    80: round(177.84 / 52 * 2 , 4), 
    120: round(230.88 / 52 * 2, 4), 
    240: round(382.20 / 52 * 2, 4), 
    770: round(1021.80 / 52 * 2, 4), 
    1100: round(1416.48 / 52 * 2, 4)}

# Handlungsoption: Sonderentleerung
SONDERENTLEERUNG_FUELLMENGE_PROZENT = 80 # (Schwellenwert) Beim Erreichen eines Füllwerten von 80% wird eine Sonderentleerung veranlasst

# --------------------------
# ---------- Ende ----------
# --------------------------