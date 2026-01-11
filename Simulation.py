# -----------------------------
# ---------- Imports ----------
import random
import math
import simpy
import matplotlib.pyplot as plt
import holidays

# -------------------------------
# ---------- Parameter ----------

WEEKS = 20  # Anzahl der zu durchlaufenden Wochen
START_YEAR = 2026 # Jahr in dem die Simulation startet. Davon sind die Feiertage abhängig.

# Haus mit 6 Wohnungen, in denen maximal 3 Personen (18 in Summe) wohnen können.
# Es wird angenommen, dass mindestens eine Person pro Wohnung wohnt.
MAX_BEWOHNER = 18
MIN_BEWOHNER = 6

# Szenario: Besuch
# Maximale Anzahl an Gästen
MAX_GAESTE = 10
# Schwellenwert für Besuch 
P_BESUCH = 0.30  

# Szenario: Entsorgungsausfall
# Schwellenwert für Ausfall
P_AUSFALL = 0.005 

# Szenario: Normales Müllaufkommen
# Durchschnittler Verbrauch pro Woche
RESTMUELL_PRO_PERSON = 30    # L/Woche
# Quelle: https://www.awm-muenchen.de/abfall-entsorgen/muelltonnen/fuer-haushalte

# Handlungsoption: Kapazitätsausbau 
REST_MUELLTONE_STAFFEL = [80, 120, 240, 770, 1100] # Mülltonnenkapazitaeten
REST_MUELLTONE_KOSTEN_STAFFEL = { # Kosten pro Woche für die verschiedenen kapazitaeten
    80: round(177.84 / 52, 2),
    120: round(230.88 / 52, 2),
    240: round(382.20 / 52, 2),
    770: round(1021.80 / 52, 2),
    1100: round(1416.48 / 52, 2),
}  

# Handlungsoption: Sonderentleerung
SONDERENTLEERUNG_UEBERFUELLUNGSPROZENT = 200  # Bei Überfüllung von über 200% wird eine Sonderentleerung veranlasst
SONDERENTLEERUNG_KOSTEN = 50 # Kosten der Sonderentleerung

# -------------------------------------
# ---------- Hilfsfunktionen ----------
"""
Funktion:           Bestimmung der Kosten bei Überfüllung
Input:              ueber_liter (Überfüllungsmenge in Liter)
Output:             sonderkosten (berechnete Sonderkosten)
Funktionsweise:     Bei einer Überfüllung wird pro 70 Liter der Überfüllmenge 9 EUR berechnet.
"""
def sonderkosten_aus_ueberfuellung(ueber_liter):
    sonderkosten = math.ceil(ueber_liter / 70) * 9
    return sonderkosten


"""
Funktion:           Bestimmung der Überfüllungsrate
Input:              abfallmenge (angefallene Abfallmenge in Liter), kapazitaet (maximale kapazitaet der Mülltonne)
Output:             rate (berechnete Überfüllungsrate in Prozent)
Funktionsweise:     Es wird Überfüllungsmenge in Liter bestimmt. 
                    Es gibt keine negative Überfüllungsmenge (wenn maximale kapazitaet nicht erreicht wurde).
                    Anschließend wird der Anteil der Überfüllung bestimmt (Übermenge/kapazitaet) in Prozent.

"""
def ueberfuellungsrate(abfallmenge, kapazitaet):
    ueber = max(0, abfallmenge - kapazitaet)
    rate = round((ueber / kapazitaet) * 100, 0)
    return rate


"""
Funktion:           Bestimmung der Feiertage, auf denen der Leertag fällt.
Input:              leertag (Wochentag in dem die Mülltonnenleerung staatfindet), WEEKS (Anzahl der Wochen, die in der Simulation betrachtet werden), START_YEAR (das Jahr in dem die Simulation beginnt)
Output:             feiertage (Liste der Feiertage auf denen der Leertag fällt)
Funktionsweise:     Abhängig von der betrachteten Wochen, wird die anzahl der betrachetetn Jahre bestimmt.
                    Für jedes betrachtete Jahr werden die Feiertage bestimmt. Es wird angenommen, dass das Wohnhaus in München, Bayern steht. Dadurch gelten die bayerischen Feiertage.
                    Bei den einzelnen Feiertagen wird geprüft ob dieser auf den Wochentag des Leertages fällt. Nur jene Feiertage die auf den Leertag fällt, wird der Feiertagsliste hinzugefügt.
"""
def berechne_feiertage(leertag, WEEKS, START_YEAR):
    feiertage = set() # Initialisierung der Feiertagsliste 
    years = math.ceil(WEEKS / 52) # Anzahl der Jahre
    for year in range(START_YEAR, START_YEAR + years): 
        bayerische_feiertage = holidays.Germany(years=year, subdiv="BY") # Bestimmung bayerischen Feiertage
        for d in bayerische_feiertage.keys(): 
            if d.weekday() == leertag: # Prüfung ob Feiertag auf Leertag fällt
                feiertage.add((year, d.isocalendar().week))
    return feiertage

# -----------------------------------
# ---------- Klassenmodell ----------
class MuellentsorgungsSystem:
    def __init__(self, env: simpy.Environment):
        self.env = env

        # Leertag der Mülltonne
        self.leertag = random.randint(0, 4) # Montag=0/Dienstag=1/Mittwoch=2/Donnerstag=3/Freitag=4
        # Feiertage, die auf den Leertag fallen
        self.feiertage = berechne_feiertage(self.leertag, WEEKS, START_YEAR)

        # Füllstand der Tonne in L (Liter)
        self.rest_abfallmenge_gesamt = 0

        # Metriken (pro Woche)
        self.wochen = [] # Wochenanzahl
        self.rest_abfall_woche = [] # Abfallmenge
        self.bewohner_woche = [] # Anzahl der Bewohner 
        self.besuch_woche = [] # Anzahl der Besucher
        self.ausfall_woche = [] # Ausfall bei der Leerung
        self.kosten_woche = [] # Kosten
        self.ueberfuellungsrate_woche = [] # Überfüllungsrate
        self.rest_abfallmenge_gesamt_woche = [] # Gesamte Abfallmenge (inkl. Menge der Vorwoche)
        self.sonderentleerung_kosten_woche = []  # Kosten für die Sonderentleerung
        self.ueberfuellung_kosten_woche = [] # Kosten bei Überfüllung # TODO einbauen
        self.rest_tonne_kapazitaet_woche = [] # Kapazität der Tonne

        # Mülltonnen Start-Kapazität und wöchentliche Kosten
        self.rest_tonne_kapazitaet = 80 # L
        self.rest_tonne_kosten_woche = REST_MUELLTONE_KOSTEN_STAFFEL[self.rest_tonne_kapazitaet] # Koste abhängig von der Größe

        # Handlungsoption: Kapazitätsausbau 
        self.ueberfüllungs_zaehler = 0 # Zähler für die Anzahl der Wochen mit Überfüllung (nach 4 Wochen wird Kapazität erhöht)
        
        # Prozess Starten
        self.proc = env.process(self.wochenlauf())

    # wöchentlicher Lauf
    def wochenlauf(self):
        for w in range(1, WEEKS + 1): # Durchlauf der einzelnenen Wochen
            aktuelles_jahr = START_YEAR + (w - 1) // 52 # Bestimmung des aktuellen Jahres (abhängig von der aktuellen Woche)
            kalenderwoche = ((w - 1) % 52) + 1  # Bestimmung der Kalenderwoche (für die Bestimmung des Feiertagsausfalls)

            # Personen
            # Bewohneranzahl
            anzahl_bewohner = random.randint(MIN_BEWOHNER, MAX_BEWOHNER)
            # Szenario: Besuch
            # Besuchanzahl (Wahrscheinlichkeitsbasiert)
            anzahl_besuch = 0
            if random.random() < P_BESUCH:
                anzahl_besuch = random.randint(1, MAX_GAESTE)

            # ---- Abfallmenge pro Woche (abhängig von der Personenanzahl) ----
            rest_abfallmenge_bewohner_woche = round(anzahl_bewohner * RESTMUELL_PRO_PERSON, 0)
            rest_abfallmenge_besuch_woche = round(anzahl_bewohner * RESTMUELL_PRO_PERSON * 0.15, 0) # Annahme: Besuch verbraucht nur ein Anteil des wöchentlichen Müllverbrauchs
            rest_abfallmenge_woche = rest_abfallmenge_bewohner_woche + rest_abfallmenge_besuch_woche
            self.rest_abfallmenge_gesamt += rest_abfallmenge_woche

            # ---- Überfüllungsrate (auf Basis aktuellem Füllstands und Mülltonnenkapazität) ----
            uebefuellungsrate = ueberfuellungsrate(self.rest_abfallmenge_gesamt, self.rest_tonne_kapazitaet)
            ist_ueberfuellt = (self.rest_abfallmenge_gesamt > self.rest_tonne_kapazitaet)

            # ---- Handlungsoption: Kapazitätsausbau  ----
            # Bei Überfüllung wird der Überfüllungszähler hochgezählt. Nach 4 Wochen wird Mülltonnenkapazität erhöht.
            if ist_ueberfuellt:
                self.ueberfüllungs_zaehler += 1
            else:
                self.ueberfüllungs_zaehler = 0

            if self.ueberfüllungs_zaehler >= 4: # Kapazitätsausbau
                alte_kap = self.rest_tonne_kapazitaet
                rest_groesse = [c for c in REST_MUELLTONE_STAFFEL if c > alte_kap]
                if rest_groesse:
                    neue_kap = min(rest_groesse)
                    self.rest_tonne_kapazitaet = neue_kap
                    self.rest_tonne_kosten_woche = REST_MUELLTONE_KOSTEN_STAFFEL[neue_kap]
                self.ueberfüllungs_zaehler = 0

            # ---- Szenario: Entsorgungsausfall und Feiertag ----
            ausfall = random.random() < P_AUSFALL # Wenn die bestimmte Wahrscheinlichkeit unterhalb des Schwellenwerts liegt, findet Ausfall staat.

            regulaere_leerung_moeglich = (w % 2 == 0) # Alle zwei Wochen finde Leerung statt
            regulaere_leerung_findet_statt = False # Bestimmung ob reguläre Leerung stattfindet
            if regulaere_leerung_moeglich:
                if (not ausfall) and ((aktuelles_jahr, kalenderwoche) not in self.feiertage):
                    regulaere_leerung_findet_statt = True

            # --- Handlungsoption: Sonderentleerung ---
            sonderentleerung = False # Sonderentleerung findet statt oder nicht
            sonderentleerung_kosten = 0 # Sonderentleeerungskosten
            if (uebefuellungsrate > SONDERENTLEERUNG_UEBERFUELLUNGSPROZENT) and (not regulaere_leerung_findet_statt):
                sonderentleerung = True
                sonderentleerung_kosten = SONDERENTLEERUNG_KOSTEN
                self.rest_abfallmenge_gesamt = 0 # Tonne wird geleert

            # --- Überfüllungskosten ---
            ueber_liter = max(0.0, self.rest_abfallmenge_gesamt - self.rest_tonne_kapazitaet) # Überfüllungsmenge (L) bestimmen
            ueberfuellung_kosten = sonderkosten_aus_ueberfuellung(ueber_liter) # Überfüllungskosten

            # --- Reguläre Leerung ausführen ---
            geleert = False # Normaleleerung findet statt oder nicht
            if regulaere_leerung_findet_statt:
                self.rest_abfallmenge_gesamt = 0 # Tonne wird geleert
                geleert = True

            # --- wöchentliche Kosten ---
            woche_kosten = self.rest_tonne_kosten_woche + ueberfuellung_kosten +  sonderentleerung_kosten # normale Entleerungskostenn + Überfüllungskosten + Sonderentleerungskosten

            # --- Metriken ---
            self.wochen.append(w)
            self.bewohner_woche.append(anzahl_bewohner)
            self.besuch_woche.append(anzahl_besuch)
            self.rest_abfall_woche.append(rest_abfallmenge_woche)
            self.rest_tonne_kapazitaet_woche.append(self.rest_tonne_kapazitaet)
            self.rest_abfallmenge_gesamt_woche.append(self.rest_abfallmenge_gesamt)
            self.ueberfuellungsrate_woche.append(uebefuellungsrate)
            self.ausfall_woche.append(ausfall)
            self.sonderentleerung_kosten_woche.append(sonderentleerung_kosten)
            self.kosten_woche.append(woche_kosten)

            print(
                f"Woche: {w}\n"
                f"Gäste: {anzahl_besuch}\n"
                f"Bewohner: {anzahl_bewohner}\n"
                f"Tonnenkapazität: {self.rest_tonne_kapazitaet} L\n"
                f"wöchentliche Müllmenge: {rest_abfallmenge_woche} L\n"
                f"Gesamte Müllmenge: {self.rest_abfallmenge_gesamt} L\n"
                f"Überfüllungsrate: {uebefuellungsrate} %\n"
                f"Ausfall: {ausfall}\n"
                f"Reguläreleerung: {regulaere_leerung_findet_statt}\n"
                f"Sonderentleerung: {sonderentleerung}\n"
                f"Kosten Woche: {woche_kosten:.2f} €\n"
                f"Geleert: {geleert}\n"
            )


            # Zeitfortschritt (1 Zeiteinheit = 1 Woche)
            yield self.env.timeout(1)

# -------------------------------
# ---------- Simulation ----------
env = simpy.Environment()
model = MuellentsorgungsSystem(env)
env.run(until=WEEKS + 1)  # Beginnend bei 1 und nicht 0
