"""
Digital Business University of Applied Sciences 
Data Science und Management (M. Sc.) 
ADSC32 Applied Data Science III: Softwareparadigmen
Prof. Dr. Marcel Hebing
Julia Schmid (200022)


Diese Datei beinhaltet die Simulationslogik.
"""

# -----------------------------
# ---------- Imports ----------
import random
import simpy

# Globale Paramter importieren
from parameter import TAGE, START_JAHR, ANZAHL_BEWOHNER,  P_ABWESEND, DEFAULT_RESTMUELL_PRO_PERSON_TAG, REST_MUELLTONE_STAFFEL, REST_MUELLTONE_KOSTEN_STAFFEL, SONDERENTLEERUNG_UEBERFUELLUNGSPROZENT

# Importiere alle Hilfsfunktionen
from funktionen import *


# --------------------------------
# ---------- Funktionen ----------
"""
Funktion:           
Input:              
Output: 
Funktionsweise:     
"""
def simulation_einzeln(seed, szenario, handlungsoption):
    env = simpy.Environment()
    model = MuellentsorgungsSystem(env, szenario, handlungsoption, seed)
    #env.run(until=TAGE)
    env.run(until=TAGE) 
    return {
        "kosten_tag": model.kosten_tag,
        "anzahl_bewohner_tag": model.anzahl_bewohner_tag, 
        "anzahl_besuch_tag": model.anzahl_besuch_tag,
        "fuellmenge_tag": model.fuellmenge_tag,
        "kapazitaet_tag": model.kapazitaet_tag,
        "ueberfuellungsrate_tag": model.ueberfuellungsrate_tag,
        "sonderentleerung_kosten_tag": model.sonderentleerung_kosten_tag,
        "ueberfuellung_kosten_tag": model.ueberfuellung_kosten_tag,
        "ausfall_tag": model.ausfall_tag
    }

"""
Funktion:           
Input:              
Output: 
Funktionsweise:     
"""
def monte_carlo(durchlaeufe, szenario, handlungsoption):
    return [
        simulation_einzeln(1000 + i, szenario, handlungsoption)
        for i in range(durchlaeufe)
    ]

"""
Funktion:           Die Simulations wird mit den definierten Szenarien und Handlungsoptionen durchlaufen. 
Input:              szenarien (Szenarien), handlungsoptionen (Handlungsoptionen), durchlaeufe (Anzahl der Durchläufe)
Funktionsweise:     Für die beiden Metriken kosten_tag (Gesamtkosten) und fuellmenge_tag (Müllaufkommen) wird ein Histogramm über die gesamte Simulation erstellt und als png gespeichert.
"""
def simulationslauf(szenarien, handlungsoptionen, durchlaeufe):
    ergebnisse_gesamt = {}

    # Jedes Szenario-Handlungsoption Kombination wird mit durchlaeufe-oft durchgeführt
    for szenario_key, szenario_value in szenarien.items():
        for handlungsoption_key, handlungsoption_value in handlungsoptionen.items():
            print( f"   Szenario = {szenario_key} \tHandlungsoption = {handlungsoption_key}" )
            ergebnisse = monte_carlo(durchlaeufe, szenario_value, handlungsoption_value) # Anwendung der Funktion monte_carlo
            grafik_histogramme(ergebnisse, szenario_key, handlungsoption_key) # Anwendung der Funktion grafik_histogramme
            ergebnisse_gesamt[(szenario_key, handlungsoption_key)] = (berechnung_statistiken(ergebnisse)) # Anwendung der Funktion berechnung_statistiken

    return ergebnisse_gesamt

# -----------------------------------
# ---------- Klassenmodell ----------
class MuellentsorgungsSystem:
    def __init__(self, env, szenario, handlungsoption, seed):
        self.env = env
        self.rng = random.Random(seed)
        self.szenario = szenario
        self.handlungsoption = handlungsoption

        # Leertag der Mülltonne
        self.leertag = self.rng.randint(0, 4) # Montag=0/Dienstag=1/Mittwoch=2/Donnerstag=3/Freitag=4
        # Feiertage, die auf den Leertag fallen
        self.feiertage = berechne_feiertage(self.leertag, TAGE, START_JAHR)

        # Mülltonnen Start-Werte
        self.kapazitaet = 80 # Kapazität
        self.fuellstand = 0.0 # Füllstand 
        self.wochen_ueberfuellt = 0 # Überfüllungsindikator

        # Metriken
        self.kosten_tag = [] # Kosten
        self.anzahl_bewohner_tag = [] # Anzahl der Bewohner
        self.anzahl_besuch_tag = [] # Anzahl der Besucher
        self.ausfall_tag = [] # Indikator ob Ausfall stattgefunden hat
        self.fuellmenge_tag = [] # Füllmenge der Tonne
        self.kapazitaet_tag = [] # Kapazität der Tonne
        self.ueberfuellungsrate_tag = [] # Überfüllungsrate
        self.sonderentleerung_kosten_tag = [] # Kosten für die Sonderentleerung
        self.ueberfuellung_kosten_tag = [] # Kosten bei Überfüllung 

        # Prozess Starten 
        self.env.process(self.muellproduktion())
        self.env.process(self.ueberfuellung())
        self.env.process(self.leerung_regulaere())
        self.env.process(self.leerung_sonder())
        

    # Prozess: Müllzufuhr der Bewohner ---
    def muellproduktion(self):
        #for tag in range(TAGE):
        while True:
            tag = int(self.env.now)
            # Müll der Bewohner (Szenario: Normal)
            anzahl_bewohner = ANZAHL_BEWOHNER 
            # Mit eines Wahrscheinlichkeit sind die Bewohner aus dem Haus
            if self.rng.random() < P_ABWESEND:
                anzahl_bewohner = self.rng.randint(0, anzahl_bewohner)
            self.fuellstand += anzahl_bewohner * DEFAULT_RESTMUELL_PRO_PERSON_TAG

            # Müll der Gäste (Szenario: Besuch)
            if self.rng.random() < self.szenario["P_BESUCH"]: 
                anzahl_gaeste = self.rng.randint(1, 10) # Besucheranzahl zwischen 1 und 10
                self.fuellstand += anzahl_gaeste * DEFAULT_RESTMUELL_PRO_PERSON_TAG * 0.15 # Müllmenge der Gäste entspricht 15 Prozent des reguläten Müllaufkommen pro Person
                self.anzahl_besuch_tag.append(anzahl_gaeste)

            # Metriken
            self.anzahl_bewohner_tag.append(anzahl_bewohner)
            self.fuellmenge_tag.append(self.fuellstand) # Füllmenge der Tonne 
            self.kapazitaet_tag.append(self.kapazitaet) # Kapazität der Tonne
            self.ueberfuellungsrate_tag.append(ueberfuellungsrate(self.fuellstand, self.kapazitaet)) # Überfüllungsrate

            # Zeitfortschritt (1 Zeiteinheit = 1 Tag)
            yield self.env.timeout(1)
    
    # Prozess: Überfuellung
    def ueberfuellung(self):
        for tag in range(TAGE):
            tag_datum = date(START_JAHR, 1, 1) + timedelta(days=tag)

            # Wenn Tag auf Leertag fällt, Tag keine Feiertag ist und an dem Tag kein Ausfall stattfindet (Szenario: Ausfall) wird geleert --> Überfüllungskosten/Kapazitaetsausbau (Handlungsoption: Kapazitaetsausbau) findet statt
            if tag % 14 == self.leertag and tag_datum not in self.feiertage and self.rng.random() > self.szenario["P_AUSFALL"]:

                # Überfüllungskosten
                ueber_liter = max(0, self.fuellstand - self.kapazitaet) # Überfüllungsmenge in Liter
                kosten_ueberfuellung = sonderkosten_aus_ueberfuellung(ueber_liter) # Überfüllungskosten
                # Metriken
                self.ueberfuellung_kosten_tag.append(kosten_ueberfuellung) # Kosten bei Überfüllung 
                
                ueberrate = ueberfuellungsrate(self.fuellstand, self.kapazitaet)



                # Anzahl der Überfülllungen 
                if ueberrate >= 100:
                    self.wochen_ueberfuellt += 1
                else:
                    self.wochen_ueberfuellt = 0

                # # Wenn die Handlungsoption Kapazitaetsausbau in der Simulation betrachtet wird und in zwei aufeianderfolgendne Woche es zu einer Überfüllung kam, wird die Kapazität erweitert.
                if self.handlungsoption["kapazitaet_ausbau"] and self.wochen_ueberfuellt >= 2:
                    # Bestimmung der möglichen Kapazitätsgrößen
                    potenzielle_tonnen_kapa = [kapa for kapa in REST_MUELLTONE_STAFFEL if kapa > self.kapazitaet]
                    if potenzielle_tonnen_kapa:
                        self.kapazitaet = min(potenzielle_tonnen_kapa) # Auswahl der nächst größeren Kapazität
                    self.wochen_ueberfuellt = 0 # Zöhler für Überfüllungsanzahl auf 0 setzten

                # Wochenkosten summieren
                kosten = REST_MUELLTONE_KOSTEN_STAFFEL[self.kapazitaet]
                kosten_sonderentleerung = self.sonderentleerung_kosten_tag[-1] if self.sonderentleerung_kosten_tag else 0
                kosten_gesamt = kosten + kosten_sonderentleerung + kosten_ueberfuellung
                # Metriken
                self.kosten_tag.append(kosten_gesamt)  # Kosten
            else:
                # Bei Feiertagen/Ausfall fällt keine Leerung an --> keine Kosten, keine Überfüllung()
                self.ueberfuellung_kosten_tag.append(0)
                self.kosten_tag.append(0)

            yield self.env.timeout(1)

    # Prozess: Leerung (regulaer) (Szenario: Normal/Ausfall)
    def leerung_regulaere(self):
        #for tag in range(TAGE):
        while True:
            tag = int(self.env.now)
            # Bestimmung des Datums des aktuellen Tages (Für Feiertag)
            tag_datum = date(START_JAHR, 1, 1) + timedelta(days=tag)
            # Wenn Tag auf Leertag fällt, Tag keine Feiertag ist und an dem Tag kein Ausfall stattfindet (Szenario: Ausfall) wird geleert 
            ist_ausfall = False
            if tag % 14 == self.leertag and tag_datum not in self.feiertage:
                if self.rng.random() <= self.szenario["P_AUSFALL"]:
                    ist_ausfall = True
                else:
                    self.fuellstand = 0  #  Tonne wird geleert --> Füllstand wird zurückgesetzt, auf 0 
            # Metriken
            self.ausfall_tag.append(ist_ausfall) # Indikator ob Ausfall stattgefunden hat

            # Zeitfortschritt (1 Zeiteinheit = 1 Tag)
            yield self.env.timeout(1)

    # Prozess: Sonderentleerung (Handlungsoption: Sonderentleerung)
    def leerung_sonder(self):
        #for tag in range(TAGE):
        while True:
            kosten_sonderentleerung = 0
            # Wenn die Handlungsoption Sonderentleerung in der Simulation betrachtet wird, und der Schwellenwert für die Sonderentleerung erreicht ist, findet eine Sonderentleerung statt
            if (self.handlungsoption["sonderentleerung"] and ueberfuellungsrate(self.fuellstand, self.kapazitaet)>= SONDERENTLEERUNG_UEBERFUELLUNGSPROZENT):
                self.fuellstand = 0 # Tonne wird geleert --> Füllstand wird zurückgesetzt, auf 0 
                
                kosten_sonderentleerung = REST_MUELLTONE_KOSTEN_STAFFEL[self.kapazitaet] * 1.1 # Sonderkosten liegen 10 Prozent über den normal Kosten

            # Metriken
            self.sonderentleerung_kosten_tag.append(kosten_sonderentleerung) #  Kosten für die Sonderentleerung

            # Zeitfortschritt (1 Zeiteinheit = 1 Tag)
            yield self.env.timeout(1)


# --------------------------
# ---------- Ende ----------
# --------------------------