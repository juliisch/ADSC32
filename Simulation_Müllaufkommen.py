# -----------------------------
# ---------- Imports ----------
import random
import matplotlib.pyplot as plt
import math


# -------------------------------
# ---------- Variablen ----------

# Messung pro Woche
WEEKS = 4 # Anzahl der zu durchlaufenden Wochen

BIOABFALL_PRO_PERSON = 3.5 # L/Woche
PAPIER_PRO_PERSON = 15 # L/Woche
RESTMUELL_PRO_PERSON = 30 # L/Woche
# Quelle: https://www.awm-muenchen.de/abfall-entsorgen/muelltonnen/fuer-haushalte?utm_source=chatgpt.com

PERCENT_BESUCH = 0.30  # Wie viel Besuch in der Woche kommen in Prozenz

MAX_GAESTE = 10
# Haus mit 6 Wochnungen, in denen maximal 3 Personen (18 in Summe) wohnen können. 
# Es wird angenommen, dass mindestens eine Person pro Wohnung wohnt.  
max_Bewohner = 18
min_Bewohner = 6

# Annahme für den Haushalt gibt es jeweils nur Papiertonne und Restmülltone
# Restmülltone: 80 / 120 / 240 / 770 / 1.100 --> 177,84 / 230,88 / 382,20 / 1021,80  / 1.416,48 (14-Tägige Entsorgung)
# Papiertonne: 120 / 240 / 770 / 1.100  --> Gebührenfrei (14-Tägige Entsorgung)
# Biotonne: 120 / 240 / --> Gebührenfrei (14-Tägige Entsorgung)
# Quelle: https://www.awm-muenchen.de/abfall-entsorgen/muelltonnen/fuer-haushalte

rest_muelltone_groesse = 200 #80
papier_muelltone_groesse = 120 
bio_muelltone_groesse = 120

rest_muelltone_kosten = round(80/52,2)
bio_muelltone_kosten = 0
papier_muelltone_kosten = 0

gesamt_kosten = 0 

# Metriken zum Speichern
wochen = []
ergebnisse_abfallmenge = []
ueberfuellungsraten = []
kosten_pro_woche = []
bewohner_pro_woche = []

def berechnung_sonderkosten(tonne, abfallmenge_woche, muelltone_groesse, sonder_kosten):

    overconsumption = max(0, abfallmenge_woche - muelltone_groesse)
    #ueberfuellungsrate = max(0, overconsumption/muelltone_groesse*100)

    if overconsumption > 0:
        print(f"{tonne}tonne ist voll")
        sonder_kosten += math.ceil(overconsumption / 70) * 9 # Pro zusätzliche 70 Liter werden 9 € berechnet
        
    return sonder_kosten


def berechnung_uebefuellungsrate(abfaelle):

    summe_abfall = sum(abfallmenge for _, abfallmenge, _ in abfaelle)
    summe_kapazitaet = sum(capacity for _, _, capacity in abfaelle)

    menge_ueber = max(0, summe_abfall - summe_kapazitaet)
    uebefuellungsrate = max(0, menge_ueber / summe_kapazitaet * 100)
    uebefuellungsrate = round(uebefuellungsrate,0)
    return uebefuellungsrate

# Funktion, welche die Biomüll, Papiermüll und Restmülltone leer/auf 0 setzt
def leere_muell():
    return 0, 0, 0, 0

# Tonnen werden geleert (Simulation startet mit leeren Tonnen)
bio_abfallmenge_woche, plastik_abfallmenge_woche, rest_abfallmenge_gesamt, papier_abfallmenge_woche  = leere_muell()

# -------------------------------------
# ---------- Simulationslauf ----------
for w in range(1, WEEKS + 1):

    sonder_kosten = 0 

    print(f"Woche {w}")

    # Anzahl der Bewohner und Besucher bestimmen ---
    anzahl_bewohner = random.randint(min_Bewohner, max_Bewohner)
    print(f"Anzahl Bewohner {anzahl_bewohner}")

    # Szenario: Besuch
    anzahl_gast = 0
    if random.random() < PERCENT_BESUCH:
        anzahl_gast = random.randint(1, MAX_GAESTE)
    print(f"Anzahl Gäste {anzahl_gast}")

    anzahl_personen = anzahl_bewohner + anzahl_gast
    print(f"Anzahl Personen {anzahl_personen}")

    # Abfall bestimmen ----
    # Normaler Wochenverbrauch + Besuch-Verbrauch
    rest_abfallmenge_woche = round(anzahl_personen * RESTMUELL_PRO_PERSON ,0)
    rest_abfallmenge_gesamt = rest_abfallmenge_gesamt + rest_abfallmenge_woche
    print(f"Abfallmenge Restmüll Woche {rest_abfallmenge_woche}")
    print(f"Abfallmenge Restmüll Gesamt {rest_abfallmenge_gesamt}")

    #bio_abfallmenge_woche = bio_abfallmenge_woche + round(anzahl_personen * BIOABFALL_PRO_PERSON ,0)
    #papier_abfallmenge_woche = papier_abfallmenge_woche + round(anzahl_personen * PAPIER_PRO_PERSON ,0)
    #print(f"Abfallmenge Biomüll {bio_abfallmenge_woche}")
    #print(f"Abfallmenge Papiermüll {papier_abfallmenge_woche}")

    abfaelle = [
        #("Biomüll", bio_abfallmenge_woche, rest_muelltone_groesse),
        #("Papiermüll", papier_abfallmenge_woche, papier_muelltone_groesse),
        ("Restmüll", rest_abfallmenge_woche, rest_muelltone_groesse),
    ]

    # Kosten bestimmen ---
    for tonne, abfallmenge, tonnen_groesse in abfaelle:
        sonder_kosten = berechnung_sonderkosten(tonne, abfallmenge,tonnen_groesse,sonder_kosten)

    woche_kosten =  sonder_kosten + rest_muelltone_kosten # + papier_muelltone_kosten  + bio_muelltone_kosten 
    gesamt_kosten = gesamt_kosten + woche_kosten
    print(f"Kosten der Woche {woche_kosten} €")
    print(f"Gesamtkosten {gesamt_kosten} €")

    uebefuellungsrate = berechnung_uebefuellungsrate(abfaelle)
    print(f"Überfüllungsrate {uebefuellungsrate} %")


    # Ergebnisse speichern ---
    wochen.append(w)
    bewohner_pro_woche.append(anzahl_bewohner)
    ergebnisse_abfallmenge.append(rest_abfallmenge_woche) #ergebnisse_abfallmenge.append((rest_abfallmenge_woche, bio_abfallmenge_woche, papier_abfallmenge_woche))
    ueberfuellungsraten.append(uebefuellungsrate)
    kosten_pro_woche.append(woche_kosten)

    # Müllentleehrung (alle 2 Wochen) ---
    if w % 2 == 0:
        bio_abfallmenge_woche, plastik_abfallmenge_woche, rest_abfallmenge_gesamt, papier_abfallmenge_woche = leere_muell()
        print("\nMüll wurde geleert")

    print("")