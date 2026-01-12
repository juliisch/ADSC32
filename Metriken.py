import matplotlib.pyplot as plt

def plot_metriken(model):
    w = model.wochen

    # Kosten
    plt.figure()
    plt.plot(w, model.kosten_woche, marker="o")
    plt.title("Kosten pro Woche")
    plt.xlabel("Woche")
    plt.ylabel("Kosten [€]")
    plt.grid(True)

    # Überfüllungsrate
    plt.figure()
    plt.plot(w, model.ueberfuellungsrate_woche, marker="o")
    plt.title("Überfüllungsrate pro Woche")
    plt.xlabel("Woche")
    plt.ylabel("Überfüllungsrate [%]")
    plt.grid(True)

    # Füllstand vs Kapazität
    plt.figure()
    plt.plot(w, model.rest_abfallmenge_gesamt_woche, label="Füllstand [L]")
    plt.plot(w, model.rest_tonne_kapazitaet_woche, linestyle="--", label="Kapazität [L]")
    plt.title("Füllstand und Tonnenkapazität")
    plt.xlabel("Woche")
    plt.ylabel("Liter [L]")
    plt.legend()
    plt.grid(True)

    # Bewohner & Gäste
    plt.figure()
    plt.plot(w, model.bewohner_woche, label="Bewohner")
    plt.plot(w, model.besuch_woche, label="Gäste")
    plt.title("Bewohner und Gäste")
    plt.xlabel("Woche")
    plt.ylabel("Anzahl")
    plt.legend()
    plt.grid(True)

    # Sonderentleerungskosten
    plt.figure()
    plt.bar(w, model.sonderentleerung_kosten_woche)
    plt.title("Sonderentleerungskosten")
    plt.xlabel("Woche")
    plt.ylabel("Kosten [€]")
    plt.grid(True, axis="y")

    plt.show()
