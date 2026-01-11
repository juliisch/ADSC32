import random
import math
import simpy
import matplotlib.pyplot as plt
import holidays

# -------------------------------
# ---------- Parameter ----------

# Länge des Simulationsdurchlauf
WEEKS = 20 # Anzahl der zu durchlaufenden Wochen 

#Bestimme die Feiertage 
feiertage = []
start_year = 2026

BIOABFALL_PRO_PERSON = 3.5 # L/Woche
PAPIER_PRO_PERSON = 15 # L/Woche 
RESTMUELL_PRO_PERSON = 30 # L/Woche
# Quelle: https://www.awm-muenchen.de/abfall-entsorgen/muelltonnen/fuer-haushalte?utm_source=chatgpt.com

P_BESUCH = 0.30 # Wahrscheinlichkeit für Besuch
P_AUSFALL = 0.005 # Wahrscheinlichkeit für Ausfall

# Haus mit 6 Wochnungen, in denen maximal 3 Personen (18 in Summe) wohnen können. 
# Es wird angenommen, dass mindestens eine Person pro Wohnung wohnt.  
MAX_BEWOHNER = 18
MIN_BEWOHNER = 6
MAX_GAESTE = 10

# Mülltonnen
REST_MUELLTONE_GROESSE = 80  
PAPIER_MUELLTONE_GROESSE = 120
BIO_MUELLTONE_GROESSE = 120
REST_TONNEN_STAFFEL = [80, 120, 240, 770, 1100]

REST_MUELLTONE_KOSTEN_STAFFEL = {
        80: round(177.84/52,0),
        120: round(230.88/52,0),
        240: round(382.20/52,0),
        770: round(1021.80/52,0),
        1100: round(1416.48/52,0)
}

# Kosten pro Woche 
REST_MUELLTONE_KOSTEN = round(80/52, 2)
PAPIER_MUELLTONE_KOSTEN = 0
BIO_MUELLTONE_KOSTEN = 0


# -------------------------------------
# ---------- Hilfsfunktionen ----------
# Berechnet Sonderkosten auf Basis der Überfüllmenge (Liter)
def sonderkosten_aus_ueberfuellung(ueber_liter):
    sonderkosten = math.ceil(ueber_liter / 70) * 9 # pro zusätzliche 70 Liter werden 9 EUR berechnet
    return sonderkosten

# Überfüllungsrate in % bezogen auf die Kapazität
def ueberfuellungsrate(level, capacity):
    ueber = max(0.0, level - capacity)
    ueberfuellungsrate = round((ueber / capacity) * 100, 0)
    return ueberfuellungsrate


def berechne_feiertage(leertag, weeks, start_year):
    feiertage = set()
    years = math.ceil(weeks / 52)

    for year in range(start_year, start_year + years):
        bayerische_feiertage = holidays.Germany(years=year, subdiv="BY")
        for d in bayerische_feiertage.keys():
            if d.weekday() == leertag:
                feiertage.add((year, d.isocalendar().week))

    return feiertage



# -----------------------------------
# ---------- Klassenmodell ----------
class  MuellentsorgungsSystem:
    def __init__(self, env: simpy.Environment):
        self.env = env


        self.leertag = random.randint(0, 4) # Montag/Dienstag/Mittwoch/Donnerstag/Freitag
        self.feiertage = berechne_feiertage(self.leertag, WEEKS, start_year) # Es werden die Feiertag bestimmt, die auf den Leertag fallen

        # Füllstand der Tonnen in L (Liter)
        self.rest_abfallmenge_gesamt = 0.0
        self.bio_level = 0.0
        self.papier_level = 0.0

        # Metriken
        self.wochen = [] # Wochennummer
        self.rest_abfall_woche = [] # Wochenmenge der Restmülltone
        self.bewohner_woche = [] # Anzahl der Bewohner
        self.besuch_woche = [] # Anzahl der Besucher
        self.ausfall_woche = [] # Ausfall der Müllentleehrung
        self.kosten_woche = [] # angefallene Kosten
        self.ueberfuellung_woche = [] # Überfüllungskosten/Sonderkosten
        self.rest_abfallmenge_gesamt_woche = [] # 

        self.rest_tonne_capacity = 80 # Start Kapazität
        self.rest_tonne_kosten_woche = round(80/52, 2)  # Start Kosten




        # Kosten
        self.gesamt_kosten = 0.0

        # Start Prozess
        self.proc = env.process(self.wochenlauf())

        # Handlunsgoption: Kapazitätsausbaue (Sobald bei 2 aufeiandnerfoolgenden Wochen die Tonne überfüllt war, wird eine größere Tonne bestellt)
        self.ueberfüllungs_streak = 0

        self.ondemand_geplant_fuer_woche = None
        self.ondemand_count = 0
        self.ondemand_kosten_woche = []  # Metrik, falls gewünscht



    # wöchentlicher Lauf
    def wochenlauf(self):
        for w in range(1, WEEKS + 1):

            aktuelles_jahr = start_year + (w - 1) // 52
            kalenderwoche = ((w - 1) % 52) + 1

            # --- Personen ---
            anzahl_bewohner = random.randint(MIN_BEWOHNER, MAX_BEWOHNER)

            anzahl_gast = 0
            if random.random() < P_BESUCH:
                anzahl_gast = random.randint(1, MAX_GAESTE)

            anzahl_personen = anzahl_bewohner + anzahl_gast

            # --- Abfall pro Woche ---
            rest_abfallmenge_woche = round(anzahl_personen * RESTMUELL_PRO_PERSON, 0)

            # In die Tonne kippen (Füllstand steigt)
            self.rest_abfallmenge_gesamt += rest_abfallmenge_woche

            

            # --- Sonderkosten (Überfüllung gegen Kapazität, basierend auf aktuellem Füllstand) ---
            ueber_liter = max(0.0, self.rest_abfallmenge_gesamt - self.rest_tonne_capacity)
            sonder_kosten = sonderkosten_aus_ueberfuellung(ueber_liter)

            # Fixkosten + Sonderkosten
            woche_kosten = sonder_kosten + self.rest_tonne_kosten_woche
            self.woche_kosten = woche_kosten
            self.gesamt_kosten += woche_kosten

            # --- Überfüllungsrate ---
            uebefuellungsrate = ueberfuellungsrate(self.rest_abfallmenge_gesamt, self.rest_tonne_capacity)

            ist_ueberfuellt = (self.rest_abfallmenge_gesamt > self.rest_tonne_capacity)
            if ist_ueberfuellt:
                self.ueberfüllungs_streak += 1
            else:
                self.ueberfüllungs_streak = 0
            if self.ueberfüllungs_streak >= 4:
                alte_kap = self.rest_tonne_capacity
                rest_groesse = [c for c in REST_TONNEN_STAFFEL if c > alte_kap]
                if rest_groesse:
                    neue_kap = min(rest_groesse)
                    self.rest_tonne_capacity = neue_kap
                    self.rest_tonne_kosten_woche = REST_MUELLTONE_KOSTEN_STAFFEL[neue_kap]
                self.ueberfüllungs_streak = 0

            # --- Ausfall & Leerung (alle 2 Wochen) ---
            ausfall = random.random() < P_AUSFALL
            geleert = False

            if w % 2 == 0:
                if ausfall:
                    # keine Leerung
                    pass
                #elif w in feiertage:
                elif (aktuelles_jahr, kalenderwoche) in self.feiertage:
                    # keine Leerung (Feiertag Do/Fr in dieser ISO-Woche)
                    pass
                else:
                    # Leerung
                    self.rest_abfallmenge_gesamt = 0.0
                    self.bio_level = 0.0
                    self.papier_level = 0.0
                    geleert = True

            # --- Metriken ---
            self.wochen.append(w)
            self.bewohner_woche.append(anzahl_bewohner)
            self.besuch_woche.append(anzahl_gast)
            self.ausfall_woche.append(ausfall)
            self.rest_abfall_woche.append(rest_abfallmenge_woche)
            self.kosten_woche.append(woche_kosten)
            self.ueberfuellung_woche.append(uebefuellungsrate)
            self.rest_abfallmenge_gesamt_woche.append(self.rest_abfallmenge_gesamt)

            print(
                f"W {w:<3}\t"
                f"| Bewohner {anzahl_bewohner:>4}\t"
                f"| Gäste {anzahl_gast:>4}\t"
                f"| Restmüll {rest_abfallmenge_woche:>4} L\t"
                #f"| Füllstand {self.rest_abfallmenge_gesamt:>4} L\t"
                f"| Ü-Rate {uebefuellungsrate:>3} %\t"
                f"| Ausfall {str(ausfall):<5}\t"
                f"| Geleert {str(geleert):<5}\t"
                f"| Kosten W {woche_kosten:>7.2f} €\t"
                # f"| Kosten G {self.gesamt_kosten:>7.2f} €"
            )

            # Wochen Zeitfortschritt
            yield self.env.timeout(1)

env = simpy.Environment()
model =  MuellentsorgungsSystem(env)
env.run(until=WEEKS + 1)  # Beginnend bei 1 und nicht 0 

