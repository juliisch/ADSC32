import matplotlib.pyplot as plt
import math
import simpy
import statistics as stats
from Simulation import run_single_sim



def run_monte_carlo(n_runs: int = 1000, base_seed: int = 12345, weeks: int = WEEKS):
    results = []
    for i in range(n_runs):
        seed = base_seed + i
        results.append(run_single_sim(seed=seed, weeks=weeks))
    return results



def summarize(results):
    total_costs = [r["total_cost"] for r in results]
    weekly_costs = [r["avg_weekly_cost"] for r in results]
    specials = [r["num_special_empties"] for r in results]
    max_overfills = [r["max_overfill_rate"] for r in results]

    summary = {
        "n_runs": len(results),
        "total_cost_mean": stats.mean(total_costs),
        "total_cost_stdev": stats.pstdev(total_costs),
        "avg_weekly_cost_mean": stats.mean(weekly_costs),
        "special_empties_mean": stats.mean(specials),
        "p_special_empties_ge_1": sum(1 for x in specials if x >= 1) / len(specials),

        "max_overfill_rate_mean": stats.mean(max_overfills),
        "p_max_overfill_rate_gt_0": sum(1 for x in max_overfills if x > 0) / len(max_overfills),
    }
    return summary


def plot_distributions(results):
    total_costs = [r["total_cost"] for r in results]
    weekly_costs = [r["avg_weekly_cost"] for r in results]
    specials = [r["num_special_empties"] for r in results]
    max_overfills = [r["max_overfill_rate"] for r in results]

    # Histogramm: Gesamtkosten
    plt.figure()
    plt.hist(total_costs, bins=40)
    plt.title("Monte-Carlo: Verteilung der Gesamtkosten")
    plt.xlabel("Gesamtkosten über den Simulationszeitraum [€]")
    plt.ylabel("Häufigkeit")
    plt.show()

    # Boxplot: Vergleich mehrerer Kennzahlen (skaliere sinnvoll getrennt)
    plt.figure()
    plt.boxplot([total_costs, weekly_costs, specials, max_overfills],
                labels=["Total €", "€/Woche", "Sonderentl.", "Max %"])
    plt.title("Monte-Carlo: Boxplots ausgewählter Kennzahlen")
    plt.ylabel("Wert (unterschiedliche Skalen)")
    plt.show()