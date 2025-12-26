# -----------------------------
# ---------- Imports ----------
import random
import matplotlib.pyplot as plt


# -------------------------------
# ---------- Variablen ----------

# Messung pro Woche

WEEKS = 10 # Anzahl der zu durchlaufenden Wochen
HAUSHALTSABFAELLE_PRO_PERSON = 8.3 # KG/Woche
# Quelle: https://www.destatis.de/DE/Presse/Pressemitteilungen/2024/12/PD24_475_321.html


# Haus mit 6 Wochnungen, in denen maximal 3 Personen (18 in Summe) wohnen können. 
# Es wird angenommen, dass mindestens eine Person pro Wohnung wohnt.  
max_Bewohner = 18
min_Bewohner = 6


# Annahme für den Haushalt gibt es jeweils nur Papiertonne und Restmülltone
# Restmülltone: 80 / 120 / 240 / 770 / 1.100 --> 177,84 / 230,88 / 382,20 / 1021,80  / 1.416,48 (14-Tägige Entsorgung)
# Papiertonne: 120 / 240 / 770 / 1.100  --> Gebührenfrei (14-Tägige Entsorgung)
# Quelle: https://www.awm-muenchen.de/abfall-entsorgen/muelltonnen/fuer-haushalte


restmuelltone_groesse = 80
papierttone_groesse = 120 


restmuelltone_kosten = round(80/52,2)
papierttone_kosten = 0
gesamt_kosten = 0 


# Metriken zum Speichern
wochen = []
abfallmenge = []
ueberfuellungsraten = []
kosten_pro_woche = []
bewohner_pro_woche = []


# -------------------------------------
# ---------- Somulationslauf ----------
for w in range(1, WEEKS + 1):

    overconsumtion = 0 
    sonder_kosten = 0 

    print(f"Woche {w}")

    anzahl_bewohner = random.randint(min_Bewohner, max_Bewohner)
    print(f"Anzahl Bewohner {anzahl_bewohner}")


    abfallmenge_woche = round(anzahl_bewohner * HAUSHALTSABFAELLE_PRO_PERSON,0)
    print(f"Abfallmenge {abfallmenge_woche} KG")

    overconsumtion = max(0, abfallmenge_woche - restmuelltone_groesse)
    print(f"Zuviel Abfallmenge {overconsumtion} KG")

    ueberfuellungsrate = max(0, overconsumtion/restmuelltone_groesse*100)
    print(f"Überfüllungsrate {ueberfuellungsrate} %")

    if overconsumtion > 0:
        sonder_kosten += 100
    print(f"Sonderkosten {sonder_kosten} €")

    woche_kosten =  papierttone_kosten + restmuelltone_kosten + sonder_kosten
    gesamt_kosten = gesamt_kosten + woche_kosten
    print(f"Kosten der Woche {woche_kosten} €")
    print(f"Gesamtkosten {gesamt_kosten} €")


    wochen.append(w)
    bewohner_pro_woche.append(anzahl_bewohner)
    abfallmenge.append(abfallmenge_woche)
    ueberfuellungsraten.append(ueberfuellungsrate)
    kosten_pro_woche.append(woche_kosten)

    print("")


# ------------------------------
# ---------- Grafiken ----------
# # 1) Abfallmenge pro Woche
# plt.figure()
# plt.plot(wochen, abfallmenge, marker="o")
# plt.title("Abfallmenge pro Woche")
# plt.xlabel("Woche")
# plt.ylabel("Abfallmenge (kg)")
# plt.xticks(wochen)
# plt.grid(True)
# plt.show()

# # 2) Überfüllungsrate pro Woche
# plt.figure()
# plt.plot(wochen, ueberfuellungsraten, marker="o")
# plt.title("Überfüllungsrate pro Woche")
# plt.xlabel("Woche")
# plt.ylabel("Überfüllungsrate (%)")
# plt.xticks(wochen)
# plt.grid(True)
# plt.show()

# # 3) Kosten pro Woche (nicht kumuliert)
# plt.figure()
# plt.plot(wochen, kosten_pro_woche, marker="o")
# plt.title("Kosten pro Woche")
# plt.xlabel("Woche")
# plt.ylabel("Kosten (€)")
# plt.xticks(wochen)
# plt.grid(True)
# plt.show()

# # Optional: kumulierte Kosten als extra Grafik
# plt.figure()
# plt.plot(wochen, [sum(kosten_pro_woche[:i]) for i in range(1, len(kosten_pro_woche) + 1)], marker="o")
# plt.title("Kumulierte Gesamtkosten")
# plt.xlabel("Woche")
# plt.ylabel("Gesamtkosten (€)")
# plt.xticks(wochen)
# plt.grid(True)
# plt.show()