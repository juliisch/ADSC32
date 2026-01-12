# -----------------------------
# ---------- Imports ----------
import random
import math
import simpy
import holidays
from Metriken import plot_metriken
import statistics as stats
import matplotlib.pyplot as plt

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
        self.ueberfuellung_kosten_woche = [] # Kosten bei Überfüllung 
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
            rest_abfallmenge_besuch_woche = round(anzahl_besuch * RESTMUELL_PRO_PERSON * 0.15, 0) # Annahme: Besuch verbraucht nur ein Anteil des wöchentlichen Müllverbrauchs
            rest_abfallmenge = rest_abfallmenge_bewohner_woche + rest_abfallmenge_besuch_woche
            self.rest_abfallmenge_gesamt += rest_abfallmenge

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
            kosten = self.rest_tonne_kosten_woche + ueberfuellung_kosten +  sonderentleerung_kosten # normale Entleerungskostenn + Überfüllungskosten + Sonderentleerungskosten

            # --- Metriken ---
            self.wochen.append(w)
            self.bewohner_woche.append(anzahl_bewohner)
            self.besuch_woche.append(anzahl_besuch)
            self.rest_abfall_woche.append(rest_abfallmenge)
            self.rest_tonne_kapazitaet_woche.append(self.rest_tonne_kapazitaet)
            self.rest_abfallmenge_gesamt_woche.append(self.rest_abfallmenge_gesamt)
            self.ueberfuellungsrate_woche.append(uebefuellungsrate)
            self.ausfall_woche.append(ausfall)
            self.sonderentleerung_kosten_woche.append(sonderentleerung_kosten)
            self.ueberfuellung_kosten_woche.append(ueberfuellung_kosten)
            self.kosten_woche.append(kosten)

            # Zeitfortschritt (1 Zeiteinheit = 1 Woche)
            yield self.env.timeout(1)

# # -------------------------------
# # ---------- Simulation ----------


def simulation_einzeln(seed):
    random.seed(seed)
    env = simpy.Environment()
    model = MuellentsorgungsSystem(env)
    env.run(until=WEEKS + 1)

    #print(model.kosten_woche)

    kosten = []
    kosten = kosten.append(model.kosten_woche)

    # Metriken
    return {
        "seed": seed,
        "wochen": model.wochen,  # [1..WEEKS]
        "kosten_woche": model.kosten_woche,
        "bewohner_woche": model.bewohner_woche,
        "besuch_woche": model.besuch_woche,
        "rest_abfall_woche": model.rest_abfall_woche,
        "rest_tonne_kapazitaet_woche": model.rest_tonne_kapazitaet_woche,
        "rest_abfallmenge_gesamt_woche": model.rest_abfallmenge_gesamt_woche,
        "ueberfuellungsrate_woche": model.ueberfuellungsrate_woche,
        "ausfall_woche": model.ausfall_woche,
        "sonderentleerung_kosten_woche": model.sonderentleerung_kosten_woche,
        "ueberfuellung_kosten_woche": model.ueberfuellung_kosten_woche,
    }

def monte_carlo(durchlaeufe = 2000, seed_start = 123):
    ergebnisse = []
    for i in range(durchlaeufe):
        ergebnisse.append(simulation_einzeln(seed=seed_start + i))
    return ergebnisse


def auswertung_gesamt(ergebnisse):
    """
    Berechnet Statistiken über ALLE Wochen UND ALLE Runs für alle Metriken,
    die in simulation_einzeln zurückgegeben werden (außer 'seed' und 'wochen').
    """

    if not ergebnisse:
        return {}

    # Alle Keys bestimmen, die ausgewertet werden sollen
    exclude = {"seed", "wochen"}
    metriken = [k for k in ergebnisse[0].keys() if k not in exclude]

    result = {}

    for metrik in metriken:
        alle_werte = []
        for run in ergebnisse:
            alle_werte.extend(run[metrik])

        # Sonderfall: Bool-Metriken (z.B. ausfall_woche)
        if alle_werte and isinstance(alle_werte[0], bool):
            true_count = sum(alle_werte)
            n = len(alle_werte)
            result[metrik] = {
                "quote_true": true_count / n,   # Anteil True
                "anzahl_true": true_count,
                "anzahl_werte": n,
            }
            continue

        # Standard: numerische Metriken
        result[metrik] = {
            "mean": stats.mean(alle_werte),
            "min": min(alle_werte),
            "max": max(alle_werte),
            "std": stats.stdev(alle_werte) if len(alle_werte) > 1 else 0.0,
            "median": stats.median(alle_werte),
            "anzahl_werte": len(alle_werte),
        }

    return result

def print_stats_gesamt(stats_gesamt):
    for metrik, werte in stats_gesamt.items():
        print(f"\n{metrik} – gesamter Simulationslauf:")
        for k, v in werte.items():
            if isinstance(v, float):
                print(f"  {k}: {v:.4f}" if "quote" in k else f"  {k}: {v:.2f}")
            else:
                print(f"  {k}: {v}")

ergebnisse = monte_carlo(durchlaeufe=2000)
stats_gesamt = auswertung_gesamt(ergebnisse)
print_stats_gesamt(stats_gesamt)





# def plot_histogramme_gesamt(ergebnisse: list[dict], bins="auto", save_dir: str | None = None):

#     if not ergebnisse:
#         print("Keine Ergebnisse vorhanden.")
#         return

#     exclude = {"seed", "wochen"}
#     metriken = [k for k in ergebnisse[0].keys() if k not in exclude]

#     if save_dir is not None:
#         os.makedirs(save_dir, exist_ok=True)

#     for metrik in metriken:
#         # Werte über alle Runs/Wochen flach sammeln
#         alle_werte = []
#         for run in ergebnisse:
#             alle_werte.extend(run[metrik])

#         if not alle_werte:
#             continue

#         plt.figure()

#         # Bool-Metrik: Balken statt Histogramm
#         if isinstance(alle_werte[0], bool):
#             true_count = sum(alle_werte)
#             false_count = len(alle_werte) - true_count
#             plt.bar(["False", "True"], [false_count, true_count])
#             plt.title(f"{metrik} – Häufigkeit (gesamt)")
#             plt.ylabel("Anzahl")
#         else:
#             plt.hist(alle_werte, bins=bins)
#             plt.title(f"{metrik} – Histogramm (gesamt)")
#             plt.xlabel(metrik)
#             plt.ylabel("Häufigkeit")

#         plt.tight_layout()

#         if save_dir is not None:
#             # Dateiname „sauber“ machen
#             fname = "".join(ch if ch.isalnum() or ch in ("_", "-", ".") else "_" for ch in metrik)
#             path = os.path.join(save_dir, f"hist_{fname}.png")
#             plt.savefig(path, dpi=150)
#             plt.close()
#         else:
#             plt.show()

# plot_histogramme_gesamt(ergebnisse, bins="auto")


