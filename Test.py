# -----------------------------
# ---------- Imports ----------
import random
import math
import simpy
import holidays
from dataclasses import dataclass, asdict
from datetime import date, timedelta
from typing import List, Dict, Any, Optional, Tuple

# Optional: falls vorhanden
# from Metriken import plot_metriken


# -------------------------------
# ---------- Parameter ----------
WEEKS = 56*2                 # Anzahl der zu durchlaufenden Wochen
START_YEAR = 2026          # Jahr in dem die Simulation startet. Davon sind die Feiertage abhängig.
START_DATE = date(START_YEAR, 1, 1)  # Startdatum der Simulation (Tagesauflösung)

# Haus mit 6 Wohnungen, in denen maximal 3 Personen (18 in Summe) wohnen können.
# Es wird angenommen, dass mindestens eine Person pro Wohnung wohnt.
MAX_BEWOHNER = 18
MIN_BEWOHNER = 6

# Szenario: Besuch
MAX_GAESTE = 10
P_BESUCH = 0.30

# Szenario: Entsorgungsausfall (nur am geplanten Leerungstag relevant)
P_AUSFALL = 0.005

# Szenario: Normales Müllaufkommen
RESTMUELL_PRO_PERSON = 30    # L/Woche

# Handlungsoption: Kapazitätsausbau
REST_MUELLTONE_STAFFEL = [80, 120, 240, 770, 1100]  # L
REST_MUELLTONE_KOSTEN_STAFFEL = {
    80: round(177.84 / 52, 2),
    120: round(230.88 / 52, 2),
    240: round(382.20 / 52, 2),
    770: round(1021.80 / 52, 2),
    1100: round(1416.48 / 52, 2),
}

# Handlungsoption: Sonderentleerung
SONDERENTLEERUNG_UEBERFUELLUNGSPROZENT = 200  # Überfüllung (über/cap)*100 > 200
SONDERENTLEERUNG_KOSTEN = 50

# Policy: Kapazitätsausbau nach 4 Wochen mit Überfüllung
UPGRADE_NACH_UEBERFUELLUNG_WOCHEN = 4

# Monte-Carlo Runs (für Punkt 9)
N_RUNS = 250

# Seed / Reproduzierbarkeit (Punkt 7)
BASE_SEED = 42


# -------------------------------------
# ---------- Hilfsfunktionen ----------
def sonderkosten_aus_ueberfuellung(ueber_liter: float) -> float:
    """
    Bei einer Überfüllung wird pro 70 Liter der Überfüllmenge 9 EUR berechnet.
    """
    if ueber_liter <= 0:
        return 0.0
    return float(math.ceil(ueber_liter / 70.0) * 9)


def ueberfuellungsrate(abfallmenge: float, kapazitaet: float) -> float:
    """
    rate = (Übermenge / Kapazität) * 100
    """
    ueber = max(0.0, abfallmenge - kapazitaet)
    return round((ueber / kapazitaet) * 100.0, 0)


def build_bavarian_holidays(years: List[int]) -> set:
    """
    Liefert Feiertage in Bayern als Set von datetime.date.
    """
    h = set()
    for y in years:
        by = holidays.Germany(years=y, subdiv="BY")
        for d in by.keys():
            h.add(d)
    return h


# -----------------------------------
# ---------- Tonnenmodell (Punkt 6) ----------
class RestmuellTonne:
    def __init__(self, kapazitaet_l: float):
        self.kapazitaet_l = float(kapazitaet_l)
        self.fuellstand_l = 0.0

    def add_waste(self, liters: float) -> None:
        self.fuellstand_l += float(liters)

    def empty(self) -> None:
        self.fuellstand_l = 0.0

    def overflow_liters(self) -> float:
        return max(0.0, self.fuellstand_l - self.kapazitaet_l)

    def overflow_rate_pct(self) -> float:
        return ueberfuellungsrate(self.fuellstand_l, self.kapazitaet_l)

    def is_overfilled(self) -> bool:
        return self.fuellstand_l > self.kapazitaet_l


# -----------------------------------
# ---------- Event Log (Punkt 8) ----------
@dataclass
class EventLogEntry:
    day_index: int
    sim_date: str
    week_index: int
    event_type: str

    # Zustände
    residents: int
    guests: int
    weekly_waste_l: float
    bin_capacity_l: float
    bin_fill_l: float
    overflow_rate_pct: float

    # Ereignisflags
    holiday: bool
    outage: bool
    regular_collection_planned: bool
    regular_collection_done: bool
    special_collection_done: bool
    capacity_upgraded: bool

    # Kosten
    fixed_cost_week: float
    overflow_cost: float
    special_collection_cost: float
    total_cost_event: float

    # Zusatz
    notes: str = ""


# -----------------------------------
# ---------- Simulationsmodell ----------
class MuellentsorgungsSystem:
    """
    Änderungen umgesetzt:
    1) Tagesauflösung (env.now in Tagen; Feiertage per Datum)
    2) Bewohnerzahl als Zustand (einmalig gezogen)
    5) Kosten ereignis-/periodebasiert (wöchentlich fix + wöchentlich overflow + ggf. Sonderentleerung)
    6) Tonnenzustand kapseln (RestmuellTonne)
    7) Seed/Reproduzierbarkeit (random.Random pro Instanz)
    8) Strukturiertes Logging
    9) Monte-Carlo Läufe (siehe run_monte_carlo)
    """

    def __init__(self, env: simpy.Environment, rng: random.Random, weeks: int, start_date: date):
        self.env = env
        self.rng = rng
        self.weeks = weeks
        self.days = weeks * 7
        self.start_date = start_date

        # Jahre, die in der Simulationsspanne vorkommen (für Feiertage)
        end_date = start_date + timedelta(days=self.days - 1)
        years = list(range(start_date.year, end_date.year + 1))
        self.by_holidays = build_bavarian_holidays(years)

        # Leertag der Mülltonne: Montag=0 ... Sonntag=6 (hier nur Mo-Fr)
        self.collection_weekday = self.rng.randint(0, 4)

        # Bewohnerzahl als Zustand (Punkt 2)
        self.residents = self.rng.randint(MIN_BEWOHNER, MAX_BEWOHNER)

        # Tonne + Kosten
        self.bin = RestmuellTonne(kapazitaet_l=80)
        self.fixed_cost_week = REST_MUELLTONE_KOSTEN_STAFFEL[int(self.bin.kapazitaet_l)]

        # Policy: Kapazitätsausbau nach N Wochen Überfüllung
        self.overfill_week_streak = 0

        # Monitoring für “nächster regulärer Leertermin”
        self.next_regular_collection_day_index: Optional[int] = None

        # Logs
        self.event_log: List[EventLogEntry] = []

        # Prozessstart
        self.proc_waste = env.process(self.waste_generation_weekly())
        self.proc_regular = env.process(self.regular_collection_process())

    def sim_date(self, day_index: int) -> date:
        return self.start_date + timedelta(days=day_index)

    def week_index(self, day_index: int) -> int:
        # Woche 1 startet am Tag 0..6
        return (day_index // 7) + 1

    def is_holiday(self, d: date) -> bool:
        return d in self.by_holidays

    def current_cost_weekly_fixed(self) -> float:
        return self.fixed_cost_week

    def upgrade_capacity_if_needed(self) -> bool:
        """
        Kapazitätsupgrade bei Überfüllung über mehrere Wochen.
        Returns: True wenn Upgrade erfolgte.
        """
        if self.overfill_week_streak < UPGRADE_NACH_UEBERFUELLUNG_WOCHEN:
            return False

        current = int(self.bin.kapazitaet_l)
        bigger = [c for c in REST_MUELLTONE_STAFFEL if c > current]
        if not bigger:
            self.overfill_week_streak = 0
            return False

        new_cap = min(bigger)
        self.bin.kapazitaet_l = float(new_cap)
        self.fixed_cost_week = REST_MUELLTONE_KOSTEN_STAFFEL[new_cap]
        self.overfill_week_streak = 0
        return True

    def log_event(
        self,
        day_index: int,
        event_type: str,
        guests: int,
        weekly_waste_l: float,
        holiday: bool,
        outage: bool,
        regular_planned: bool,
        regular_done: bool,
        special_done: bool,
        capacity_upgraded: bool,
        fixed_cost_week: float,
        overflow_cost: float,
        special_cost: float,
        total_cost_event: float,
        notes: str = "",
    ) -> None:
        d = self.sim_date(day_index)
        entry = EventLogEntry(
            day_index=day_index,
            sim_date=str(d),
            week_index=self.week_index(day_index),
            event_type=event_type,
            residents=self.residents,
            guests=guests,
            weekly_waste_l=float(weekly_waste_l),
            bin_capacity_l=float(self.bin.kapazitaet_l),
            bin_fill_l=float(self.bin.fuellstand_l),
            overflow_rate_pct=float(self.bin.overflow_rate_pct()),
            holiday=bool(holiday),
            outage=bool(outage),
            regular_collection_planned=bool(regular_planned),
            regular_collection_done=bool(regular_done),
            special_collection_done=bool(special_done),
            capacity_upgraded=bool(capacity_upgraded),
            fixed_cost_week=float(fixed_cost_week),
            overflow_cost=float(overflow_cost),
            special_collection_cost=float(special_cost),
            total_cost_event=float(total_cost_event),
            notes=notes,
        )
        self.event_log.append(entry)

    # -----------------------------
    # Prozess 1: wöchentliche Abfallerzeugung
    def waste_generation_weekly(self):
        """
        Jede Woche (am Wochenanfang: day_index % 7 == 0) fällt wöchentlicher Müll an.
        Kosten:
          - wöchentliche Fixkosten der Tonne
          - wöchentliche Überfüllungskosten (einmal pro Woche, auf Basis Füllstand nach Zuwachs und nach ggf. Leerungen des gleichen Tages)
          - Sonderentleerungskosten ggf. sofort
        """
        for day_index in range(0, self.days, 7):
            d = self.sim_date(day_index)
            holiday = self.is_holiday(d)

            # Besuch nur wöchentlich
            guests = 0
            if self.rng.random() < P_BESUCH:
                guests = self.rng.randint(1, MAX_GAESTE)

            # Abfall pro Woche (Bewohner konstant; Gäste anteilig)
            waste_residents = round(self.residents * RESTMUELL_PRO_PERSON, 0)
            waste_guests = round(guests * RESTMUELL_PRO_PERSON * 0.15, 0)
            weekly_waste_l = float(waste_residents + waste_guests)

            # Müll hinzufügen
            self.bin.add_waste(weekly_waste_l)

            # Policy: Überfüllungsstreak zählen (wöchentlich)
            if self.bin.is_overfilled():
                self.overfill_week_streak += 1
            else:
                self.overfill_week_streak = 0

            # ggf. Kapazität upgraden (Punkt 2/Policy bleibt, aber sauber gekapselt)
            capacity_upgraded = self.upgrade_capacity_if_needed()

            # --- Sonderentleerung Trigger (Punkt 5: ereignisbasiert) ---
            # Regel: wenn Überfüllungsrate > 200% und keine reguläre Leerung am/seit dem Trigger zu erwarten ist,
            # dispatch sofort Sonderentleerung (vereinfachte, aber kausal klare Implementierung).
            overflow_rate = self.bin.overflow_rate_pct()
            regular_planned = self.next_regular_collection_day_index is not None
            next_reg = self.next_regular_collection_day_index if regular_planned else None

            special_done = False
            special_cost = 0.0
            notes = ""

            # "Keine reguläre Leerung findet statt" interpretieren wir hier als:
            # nächste reguläre Leerung ist nicht am gleichen Tag (day_index), sondern später.
            if overflow_rate > SONDERENTLEERUNG_UEBERFUELLUNGSPROZENT:
                if (next_reg is None) or (next_reg > day_index):
                    special_done = True
                    special_cost = float(SONDERENTLEERUNG_KOSTEN)
                    self.bin.empty()
                    notes = "Sonderentleerung ausgelöst (Überfüllungsrate > 200%, keine reguläre Leerung am selben Tag)."

            # Wöchentliche Fixkosten
            fixed_cost = self.current_cost_weekly_fixed()

            # Wöchentliche Überfüllungskosten (nach Sonderentleerung ggf. 0)
            overflow_l = self.bin.overflow_liters()
            overflow_cost = sonderkosten_aus_ueberfuellung(overflow_l)

            total_cost = fixed_cost + overflow_cost + special_cost

            self.log_event(
                day_index=day_index,
                event_type="weekly_waste",
                guests=guests,
                weekly_waste_l=weekly_waste_l,
                holiday=holiday,              # Wochenanfang kann Feiertag sein; für Waste selbst ohne Effekt, aber geloggt
                outage=False,
                regular_planned=regular_planned,
                regular_done=False,
                special_done=special_done,
                capacity_upgraded=capacity_upgraded,
                fixed_cost_week=fixed_cost,
                overflow_cost=overflow_cost,
                special_cost=special_cost,
                total_cost_event=total_cost,
                notes=notes,
            )

            yield self.env.timeout(7)

    # -----------------------------
    # Prozess 2: reguläre Leerung (alle 2 Wochen, am festgelegten Wochentag)
    def regular_collection_process(self):
        """
        Reguläre Leerung findet alle 2 Wochen statt, am festgelegten Wochentag (Mo-Fr).
        Feiertag: keine Leerung (wie im Original; aber korrekt per Datum).
        Ausfall: probabilistisch am Leerungstag.
        """
        # Wir definieren die erste mögliche Leerung:
        # day 0 ist START_DATE; wir suchen den ersten Tag mit gewünschtem weekday.
        day0_weekday = self.start_date.weekday()
        offset_days = (self.collection_weekday - day0_weekday) % 7
        first_collection_day = offset_days  # day-index der ersten Leerung

        # danach alle 14 Tage
        day_index = first_collection_day
        while day_index < self.days:
            self.next_regular_collection_day_index = day_index  # für Sonderentleerungslogik sichtbar

            # Bis zum Leerungstag warten (SimPy)
            now = int(self.env.now)
            wait = day_index - now
            if wait > 0:
                yield self.env.timeout(wait)

            d = self.sim_date(day_index)
            holiday = self.is_holiday(d)
            outage = (self.rng.random() < P_AUSFALL)

            regular_planned = True
            regular_done = False

            if (not holiday) and (not outage):
                self.bin.empty()
                regular_done = True

            # Log: reguläre Leerung als eigenes Event (Punkt 5/8)
            self.log_event(
                day_index=day_index,
                event_type="regular_collection",
                guests=0,
                weekly_waste_l=0.0,
                holiday=holiday,
                outage=outage,
                regular_planned=regular_planned,
                regular_done=regular_done,
                special_done=False,
                capacity_upgraded=False,
                fixed_cost_week=0.0,         # Fixkosten werden im Wochen-Event erfasst
                overflow_cost=0.0,           # Overflow-Kosten werden im Wochen-Event erfasst
                special_cost=0.0,
                total_cost_event=0.0,
                notes=("Reguläre Leerung durchgeführt." if regular_done else "Reguläre Leerung ausgefallen (Feiertag oder Ausfall)."),
            )

            # nächster Termin
            day_index += 14
            # nach Erreichen des Termins, wird der "next" beim nächsten Schleifendurchlauf neu gesetzt


# -----------------------------------
# ---------- Auswertung / Monte-Carlo (Punkt 9) ----------
def summarize_run(event_log: List[EventLogEntry]) -> Dict[str, Any]:
    total_cost = sum(e.total_cost_event for e in event_log)
    special_count = sum(1 for e in event_log if e.special_collection_done)
    regular_fail_count = sum(1 for e in event_log if (e.event_type == "regular_collection" and not e.regular_collection_done))
    overfilled_weeks = sum(1 for e in event_log if (e.event_type == "weekly_waste" and e.overflow_rate_pct > 0))
    max_overflow_rate = max((e.overflow_rate_pct for e in event_log if e.event_type == "weekly_waste"), default=0.0)
    return {
        "total_cost": total_cost,
        "special_collections": special_count,
        "regular_failures": regular_fail_count,
        "overfilled_weeks": overfilled_weeks,
        "max_overflow_rate_pct": max_overflow_rate,
        "weeks": max((e.week_index for e in event_log), default=0),
        "residents": next((e.residents for e in event_log), None),
    }


def run_single_simulation(seed: int, weeks: int = WEEKS, start_date: date = START_DATE) -> Tuple[Dict[str, Any], List[EventLogEntry]]:
    rng = random.Random(seed)
    env = simpy.Environment()
    model = MuellentsorgungsSystem(env=env, rng=rng, weeks=weeks, start_date=start_date)
    env.run(until=model.days + 1)  # +1 als Sicherheitsmarge
    summary = summarize_run(model.event_log)
    summary["seed"] = seed
    summary["collection_weekday"] = model.collection_weekday
    summary["bin_start_capacity_l"] = 80
    return summary, model.event_log


def percentile(sorted_vals: List[float], p: float) -> float:
    """
    Einfacher Perzentilrechner (p in [0,1]).
    """
    if not sorted_vals:
        return 0.0
    if p <= 0:
        return float(sorted_vals[0])
    if p >= 1:
        return float(sorted_vals[-1])
    k = (len(sorted_vals) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(sorted_vals[int(k)])
    d0 = sorted_vals[f] * (c - k)
    d1 = sorted_vals[c] * (k - f)
    return float(d0 + d1)


def run_monte_carlo(n_runs: int = N_RUNS, base_seed: int = BASE_SEED) -> Dict[str, Any]:
    summaries: List[Dict[str, Any]] = []
    for i in range(n_runs):
        seed = base_seed + i
        s, _ = run_single_simulation(seed=seed, weeks=WEEKS, start_date=START_DATE)
        summaries.append(s)

    costs = sorted([s["total_cost"] for s in summaries])
    specials = sorted([s["special_collections"] for s in summaries])
    overfilled = sorted([s["overfilled_weeks"] for s in summaries])
    max_over = sorted([s["max_overflow_rate_pct"] for s in summaries])

    report = {
        "n_runs": n_runs,
        "weeks": WEEKS,
        "cost_mean": sum(costs) / len(costs),
        #"cost_p05": percentile(costs, 0.05),
        "cost_p50": percentile(costs, 0.50),
        #"cost_p95": percentile(costs, 0.95),
        "specials_mean": sum(specials) / len(specials),
        "overfilled_weeks_mean": sum(overfilled) / len(overfilled),
        "max_overflow_rate_p95": percentile(max_over, 0.95),
        "raw_summaries": summaries,  # optional: Detaildaten
    }
    return report


# -----------------------------------
# ---------- Main ----------
if __name__ == "__main__":
    # Einzelrun (deterministisch durch Seed)
    summary, event_log = run_single_simulation(seed=BASE_SEED, weeks=WEEKS, start_date=START_DATE)

    print("=== Einzelrun Summary ===")
    for k, v in summary.items():
        print(f"{k}: {v}")

    print("\n=== Beispiel: erste 10 Events (strukturiert) ===")
    for e in event_log[:10]:
        print(asdict(e))

    # Monte-Carlo (Punkt 9)
    mc = run_monte_carlo(n_runs=N_RUNS, base_seed=BASE_SEED)

    print("\n=== Monte-Carlo Report ===")
    print(f"Runs: {mc['n_runs']}, Weeks: {mc['weeks']}")
    print(f"Kosten Mittel: {mc['cost_mean']:.2f} €")
    #print(f"Kosten Mitte: {mc['cost_p50']:.2f} €")
    print(f"Sonderentleerungen Mittel: {mc['specials_mean']:.2f}")
    print(f"Überfüllte Wochen Mittel: {mc['overfilled_weeks_mean']:.2f}")
    print(f"Max Überfüllungsrate P95: {mc['max_overflow_rate_p95']:.1f} %")

    # Optional: Plotting (falls Sie es anpassen wollen: plot_metriken erwartet i.d.R. Wochenarrays)
    # plot_metriken(...)  # hierfür müssten Sie aus event_log Wochenmetriken aggregieren.



# import pandas as pd

# df = pd.DataFrame({
#     "Woche": model.wochen,
#     "Datum_Leertag": model.datum_leertag_woche,              # falls vorhanden
#     "Bewohner": model.bewohner_woche,
#     "Gaeste": model.besuch_woche,
#     "Restabfall_Woche_L": model.rest_abfall_woche,
#     "Kapazitaet_L": model.rest_tonne_kapazitaet_woche,
#     "Ueberfuellung_%": model.ueberfuellungsrate_woche,
#     "Ausfall": model.ausfall_woche,
#     "RegulaereLeerung": model.regulaere_leerung_woche,       # falls vorhanden
#     "Sonderentleerung": model.sonderentleerung_woche,        # falls vorhanden
#     "Sonderentleerung_Kosten": model.sonderentleerung_kosten_woche,
#     "Fuellstand_Wochenende_L": model.rest_abfallmenge_gesamt_woche,
#     "Kosten_EUR": model.kosten_woche,
# })

# print(df.head())
