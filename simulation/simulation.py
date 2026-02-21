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
from parameter import TAGE, START_JAHR, ANZAHL_BEWOHNER,  P_ABWESEND, DEFAULT_RESTMUELL_PRO_PERSON_TAG, REST_MUELLTONE_STAFFEL, REST_MUELLTONE_KOSTEN_STAFFEL, SONDERENTLEERUNG_FUELLMENGE_PROZENT
# Importiere alle Hilfsfunktionen
from funktionen import *


# --------------------------------
# ---------- Funktionen ----------
"""
Funktion:       Durchführung eines einzelnen Simulationslaufs      
Input:          seed (Reproduzierbarkeitswert) 
                szenario (betrachteten Szenario)   
                handlungsoption (betrachtete Handlungsoption)  
Output:         simulation_ergebnisse_metrik (Werte der erfassten Metriken)
Funktionsweise: Zunächst wird eine SimPy-Umgebung initialisiert.
                Anschließend wird das Müllentsorgungssystem-Modell erzeugt. 
                Weiter wird die Simulation über den gesamten Betrachtungszeitraum ausgeführt.
                Die erfassten Metriken werden im Dictionary gespeichert und zurückgegeben.
"""
def simulation_einzeln(seed, szenario, handlungsoption):
    env = simpy.Environment() # Initialisierung der SimPy-Umgebung
    model = MuellentsorgungsSystem(env, szenario, handlungsoption, seed) # Müllentsorgungssystem-Modell 
    env.run(until=TAGE)  # Ausführung Simulation

    # Metriken
    simulation_ergebnisse_metrik = {
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

    return simulation_ergebnisse_metrik



"""
Funktion:       Durchführung der Monte-Carlo Simulation      
Input:          durchlaeufe (Anzahl der Simulationsdurchläufe)
                szenario (betrachteten Szenario)   
                handlungsoption (betrachtete Handlungsoption)  
Output:         simulation_ergebnisse_metrik (Werte der erfassten Metriken)
Funktionsweise: Pro Anzahl der Simulationsdurchläufe wird ein Simulationslauf mit unterschiedlichen Zufallsstartwerten ausgeführt.
                Die erfassten Metriken werden gemessen und zurückgegeben.

"""
def monte_carlo(durchlaeufe, szenario, handlungsoption):
    simulation_ergebnisse_metrik = [simulation_einzeln(1000 + i, szenario, handlungsoption) for i in range(durchlaeufe)]
    return simulation_ergebnisse_metrik



"""
Funktion:       Durchführung der Simulation mit den definierten Szenarien und Handlungsoptionen. 
Input:          durchlaeufe (Anzahl der Simulationsdurchläufe)
                szenario (betrachteten Szenario)   
                handlungsoption (betrachtete Handlungsoption)  
Output:         simulation_ergebnisse_metrik (Werte der erfassten Metriken)
Funktionsweise: Für jede Szenario-Handlungsoption-Kombination wird eine Monte-Carlo Simulation mit der Anzahl an Durchläufen durchgeführt.
                Für die erfassten Metriken werden Histogramme erstellt und Statistiken bestimmt und zurückgegeben. 
"""
def simulationslauf(szenarien, handlungsoptionen, durchlaeufe):
    simulation_ergebnisse_metrik = {}

    # Jedes Szenario-Handlungsoption Kombination wird mit durchlaeufe-mal durchgeführt
    for szenario_key, szenario_value in szenarien.items():
        for handlungsoption_key, handlungsoption_value in handlungsoptionen.items():
            print( f"   Szenario = {szenario_key} \tHandlungsoption = {handlungsoption_key}" )
            # Simulation
            ergebnisse = monte_carlo(durchlaeufe, szenario_value, handlungsoption_value) # Anwendung der Funktion monte_carlo
            # Histogramme der Metriken
            grafik_histogramme(ergebnisse, szenario_key, handlungsoption_key) # Anwendung der Funktion grafik_histogramme
            # Statistische Auswertung der Metriken
            simulation_ergebnisse_metrik[(szenario_key, handlungsoption_key)] = (berechnung_statistiken(ergebnisse)) # Anwendung der Funktion berechnung_statistiken

    return simulation_ergebnisse_metrik

# ------------------------------------------------------
# ---------- Klassenmodell (Simulationslogik) ----------
"""
Jeder Simulationsschritt entspricht einen Kalendertag.  
Jeden Tag wird Müll durch die Bewohner und ggf. den Gästen erzeugt. Die Anzahl der Besucher wird per Zufall betsimmt. 
Der Müll wird in die Mülltonne geschmissen (Füllstand hinzugefügt).
Der Leertag der Mülltage wird zu Beginn der Simulation per Zufall gefällt.
Alle 14 Tage erfolgt eine reguläre Leerung, solange der Leertag nicht auf einen Feiertag oder Ausfalltag fällt.
Kommt es zu einer Überfüllung (Müllmenge > Kapazität), so entstehen Überfüllungszusatzkosten bei der Abhlung.
Bei mehrfacher Überfüllung kann (wenn die Kapazitäten es hergeben) die Tonnenkapazität erhöht werden. 
Bei der Handlungsoption Sonderentleerung wird beim Erreichen eines bestimmten Füllstands die Leerung ausgelöst. Diese verusacht zusätzliche Kosten.
"""
class MuellentsorgungsSystem:
    def __init__(self, env, szenario, handlungsoption, seed):
        self.env = env
        self.rng = random.Random(seed)
        self.szenario = szenario
        self.handlungsoption = handlungsoption

        # Wochentag der Leertag der Mülltonne
        self.leertag = self.rng.randint(0, 4) # Montag=0/Dienstag=1/Mittwoch=2/Donnerstag=3/Freitag=4
        # Feiertage, die auf den Leertag fallen
        self.feiertage = berechne_feiertage(self.leertag, TAGE, START_JAHR)
        # Zähler seit letzter Leerung
        self.tage_seit_letzter_leerung = 0

        # Mülltonnen Startwerte
        self.kapazitaet = 80 # Kapazität
        self.fuellstand = 0.0 # Füllstand 
        self.wochen_ueberfuellt = 0 # Überfüllungsindikator

        # Metriken
        self.kosten_tag = [] # Kosten
        self.anzahl_bewohner_tag = [] # Anzahl der Bewohner
        self.anzahl_besuch_tag = [] # Anzahl der Besucher
        self.ausfall_tag = [] # Indikator, ob Ausfall stattgefunden hat
        self.fuellmenge_tag = [] # Füllmenge der Tonne
        self.kapazitaet_tag = [] # Kapazität der Tonne
        self.ueberfuellungsrate_tag = [] # Überfüllungsrate
        self.sonderentleerung_kosten_tag = [] # Kosten für die Sonderentleerung
        self.ueberfuellung_kosten_tag = [] # Kosten bei Überfüllung 

        # Prozess starten 
        self.env.process(self.muellzyklus_taeglich()) # Müllzyklus (Entstehung bis Entsorgung)

    def muellzyklus_taeglich(self):
        while True:
            tag = int(self.env.now)
            # Bestimmung des Datums des aktuellen Tages (Für Feiertag)
            tag_datum = date(START_JAHR, 1, 1) + timedelta(days=tag)
            self.tage_seit_letzter_leerung += 1

            # Indikator, ob Tag ein Leertag ist (Wenn Tag auf Wochen-Leertag fällt und zwei Wochen seit der letzten Leerung vergangen sind)
            ist_leertag = (tag_datum.weekday() == self.leertag and self.tage_seit_letzter_leerung >= 14)
            # Indikator, ob Tag ein Feiertag ist
            ist_feiertag = (tag_datum in self.feiertage)


            # -------------------------
            # Prozess: Müllproduktion  

            # Müll der Bewohner (Szenario: Normales Müllaufkommen):
            anzahl_bewohner = ANZAHL_BEWOHNER
            # Mit eines Wahrscheinlichkeit sind die Bewohner aus dem Haus
            if self.rng.random() < P_ABWESEND:
                anzahl_bewohner = self.rng.randint(0, anzahl_bewohner)
            self.fuellstand += anzahl_bewohner * DEFAULT_RESTMUELL_PRO_PERSON_TAG

            # Müll der Gäste (Szenario: erhöhter Besuch)
            anzahl_gaeste = 0
            if self.rng.random() < self.szenario["P_BESUCH"]:
                anzahl_gaeste = self.rng.randint(1, 10)  # Besucheranzahl zwischen 1 und 10
                self.fuellstand += anzahl_gaeste * DEFAULT_RESTMUELL_PRO_PERSON_TAG * 0.25 # Müllmenge der Gäste entspricht lediglich 25 Prozent des reguläten Müllaufkommen pro Person
            
            self.anzahl_bewohner_tag.append(anzahl_bewohner) # Metrik (Anzahl der Bewohner)
            self.anzahl_besuch_tag.append(anzahl_gaeste) # Metrik (Anzahl der Besucher)
            self.ueberfuellungsrate_tag.append(ueberfuellungsrate(self.fuellstand, self.kapazitaet)) # Metrik (Überfüllungsrate)
            self.fuellmenge_tag.append(self.fuellstand) # Metrik (Füllmenge der Tonne )
            self.kapazitaet_tag.append(self.kapazitaet) # Metrik (Kapazität der Tonne)

            # -------------------------
            # Prozess: reguläre Leerung (Szenario: Normales Müllaufkommen/Ausfall) - Teil 1: Indikator
            # Wenn Tag auf Leertag fällt, Tag keine Feiertag ist und an dem Tag kein Ausfall stattfindet (Szenario: Ausfall) wird geleert 
            ist_ausfall = False
            findet_regulaere_leerung_statt = False
            if ist_leertag and (not ist_feiertag):
                if self.rng.random() <= self.szenario["P_AUSFALL"]:
                    ist_ausfall = True
                else:
                    findet_regulaere_leerung_statt = True
                self.tage_seit_letzter_leerung = 0 # Zwei Wochen Zähler wird zurückgesetzte
            self.ausfall_tag.append(ist_ausfall) # Metriken (Indikator, ob Ausfall stattgefunden hat)

            # -------------------------
            # Prozess: Sonderentleerung (Handlungsoption: Sonderentleerung)
            kosten_sonderentleerung = 0
            # Wenn die Handlungsoption Sonderentleerung in der Simulation betrachtet wird, keine reguläre Leerung stattfindet und der Schwellenwert für die Sonderentleerung erreicht ist, findet eine Sonderentleerung statt
            if (not findet_regulaere_leerung_statt and self.handlungsoption["sonderentleerung"] and (self.fuellstand / self.kapazitaet * 100) >= SONDERENTLEERUNG_FUELLMENGE_PROZENT):
                self.fuellstand = 0 # Tonne wird geleert --> Füllstand wird zurückgesetzt, auf 0 
                kosten_sonderentleerung = REST_MUELLTONE_KOSTEN_STAFFEL[self.kapazitaet] * 1.4 # Sonderkosten liegen 140 Prozent über den normal Kosten
                # Quelle: Abfallwirtschaft Hohenlohekreis. Qualitätsoffensive. Abgerufen am 25.01.2026 von https://www.abfallwirtschaft-hohenlohekreis.de/leistungen-gebühren/qualitätsoffensive
            self.sonderentleerung_kosten_tag.append(kosten_sonderentleerung) # Metrik (Kosten für die Sonderentleerung)

            # -------------------------
            # Prozess: Überfuellung
            kosten_ueberfuellung = 0
            if findet_regulaere_leerung_statt:
                # Überfüllungskosten:
                ueber_liter = max(0, self.fuellstand - self.kapazitaet) # Überfüllungsmenge in Liter
                kosten_ueberfuellung = ueberfuellungskosten(ueber_liter) # Überfüllungskosten
                
                # Anzahl der Überfülllungen:
                if self.fuellstand > self.kapazitaet:
                    self.wochen_ueberfuellt += 1
                else:
                    self.wochen_ueberfuellt = 0

                # Wenn die Handlungsoption Kapazitaetsausbau in der Simulation betrachtet wird und in nach drei aufeianderfolgendenden Leerungen es zu einer Überfüllung kam, wird die Kapazität erweitert.
                if self.handlungsoption["kapazitaetsausbau"] and self.wochen_ueberfuellt >= 3:
                    # Bestimmung der möglichen Kapazitätsgrößen
                    potenzielle_tonnen_kapa = [kapa for kapa in REST_MUELLTONE_STAFFEL if kapa > self.kapazitaet]
                    if potenzielle_tonnen_kapa:
                        self.kapazitaet = min(potenzielle_tonnen_kapa) # Auswahl der nächst größeren Kapazität
                    self.wochen_ueberfuellt = 0 # Zähler für Überfüllungsanzahl auf 0 setzten
            self.ueberfuellung_kosten_tag.append(kosten_ueberfuellung) # Metrik (Kosten bei Überfüllung) 

            # -------------------------
            # Prozess: reguläre Leerung (Szenario: Normales Müllaufkommen/Ausfall) - Teil 2: Tatsächliche Leerung inkl. Kostenbestimmung
            tonnen_kosten = 0
            if findet_regulaere_leerung_statt:
                self.fuellstand = 0
                tonnen_kosten = REST_MUELLTONE_KOSTEN_STAFFEL[self.kapazitaet]

            # Gesamtkosten (Basiskosten + Überfüllung + Sonderleerung)
            self.kosten_tag.append(tonnen_kosten + kosten_ueberfuellung + kosten_sonderentleerung) # Metrik (Kosten)

            # Zeitfortschritt (1 Zeiteinheit = 1 Tag)
            yield self.env.timeout(1) 

    
# --------------------------
# ---------- Ende ----------
# --------------------------