# visualization/plotting.py (Unoptimierte Datei: Hier fehlt die globale Einstellung der Größen von Diagramm und Schrift)

"""
Funktionen zur Visualisierung der Energiespeicher-Simulation.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import pandas as pd
import logging
from utils.localization import format_date_german, get_german_weekday, DE_MONTHS_SHORT
from config import CAPACITY_MWH

logger = logging.getLogger(__name__)


def format_xaxis_with_short_german_months(ax=None, interval=1):
    """Formatiert die X-Achse mit kurzen deutschen Monatsnamen"""
    if ax is None:
        ax = plt.gca()

    def short_german_month_formatter(x, pos=None):
        date = mdates.num2date(x)
        english_month = date.strftime("%b")  # Abkürzung (Jan, Feb, etc.)
        german_month = DE_MONTHS_SHORT.get(english_month, english_month)
        return f"{german_month}"  # Nur den Monat ohne Jahr zurückgeben

    ax.xaxis.set_major_formatter(plt.FuncFormatter(short_german_month_formatter))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=interval))
    plt.xticks(rotation=0, ha="center")


from config import CAPACITY_MWH


def visualize_day(
    prices_df,
    transactions_df,
    energy_history,
    date,
    output_dir="output_plots",
    save_plot=True,
    show_plot=True,
    daily_cycles=None,
):
    """
    Erstellt eine übersichtliche Visualisierung für einen einzelnen Tag mit Beschriftung.

    Parameters:
    -----------
    prices_df : DataFrame
        DataFrame mit den Preisdaten
    transactions_df : DataFrame
        DataFrame mit den Transaktionen des Tages
    energy_history : list
        Liste mit dem Energieverlauf
    date : datetime
        Datum des zu visualisierenden Tages
    output_dir : str, optional
        Verzeichnis für die Ausgabedateien
    save_plot : bool, optional
        Ob der Plot gespeichert werden soll
    show_plot : bool, optional
        Ob der Plot angezeigt werden soll
    daily_cycles : float, optional
        Anzahl der an diesem Tag abgeschlossenen Zyklen
    """
    # Deutsche Beschriftungen für das Diagramm
    labels = {
        "title": "Tagesanalyse",
        "date": format_date_german(date),
        "weekday": get_german_weekday(date),
        "price": "Strompreis",
        "neg_price": "Negative Preise",
        "buy": "Kauf",
        "sell": "Verkauf",
        "total_profit": "Gesamtgewinn",
        "trades": "Trades",
        "cycles": "Zyklen",
        "battery": "Ladezustand",
        "profit": "Gewinn",
        "time": "Uhrzeit",
    }

    # Erstelle einen Plot mit 2 Subplots
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(10, 6), gridspec_kw={"height_ratios": [2, 1]}, sharex=True
    )

    # -------------- Erster Plot: Strompreise --------------
    # Strompreise plotten
    ax1.plot(
        prices_df["datetime"],
        prices_df["price"],
        "b-",
        label=labels["price"],
    )

    # Markieren von negativen Preisen falls vorhanden
    negative_prices = prices_df[prices_df["price"] < 0]
    if not negative_prices.empty:
        ax1.scatter(
            negative_prices["datetime"],
            negative_prices["price"],
            marker="*",
            color="purple",
            s=80,
            label=labels["neg_price"],
            zorder=5,
        )

    # Prüfen, ob Transaktionen vorhanden sind
    has_transactions = not transactions_df.empty

    # Transaktionen im Plot anzeigen (nur wenn vorhanden)
    if has_transactions and "index" in transactions_df.columns:
        # Kauftransaktionen (Laden) - nur Startpunkte
        charge_markers = transactions_df[
            (transactions_df["type"] == "charge") & (transactions_df["interval"] == 0)
        ]
        if not charge_markers.empty:
            charge_times = []
            charge_prices = []

            for idx in charge_markers["index"]:
                if int(idx) < len(prices_df):
                    charge_times.append(prices_df.iloc[int(idx)]["datetime"])
                    charge_prices.append(prices_df.iloc[int(idx)]["price"])

            if charge_times:
                ax1.scatter(
                    charge_times,
                    charge_prices,
                    marker="^",
                    color="green",
                    s=80,
                    label=labels["buy"],
                    zorder=5,
                )

        # Verkaufstransaktionen (Entladen) - nur Startpunkte
        discharge_markers = transactions_df[
            (transactions_df["type"] == "discharge")
            & (transactions_df["interval"] == 0)
        ]
        if not discharge_markers.empty:
            discharge_times = []
            discharge_prices = []

            for idx in discharge_markers["index"]:
                if int(idx) < len(prices_df):
                    discharge_times.append(prices_df.iloc[int(idx)]["datetime"])
                    discharge_prices.append(prices_df.iloc[int(idx)]["price"])

            if discharge_times:
                ax1.scatter(
                    discharge_times,
                    discharge_prices,
                    marker="v",
                    color="red",
                    s=80,
                    label=labels["sell"],
                    zorder=5,
                )

    # Achsenbeschriftungen
    ax1.set_ylabel("Preis (€/MWh)")
    ax1.grid(True, linestyle="-", color="lightgray", alpha=0.7)
    ax1.legend(loc="upper right")

    # Y-Achse anpassen
    y_max = prices_df["price"].max() * 1.1
    y_min = min(prices_df["price"].min(), 0)  # Sicherstellen, dass 0 immer sichtbar ist
    0, prices_df["price"].min() * 1.1
    ax1.set_ylim(y_min, y_max)

    # -------------- Zweiter Plot: Batterieladezustand und ggf. kumulierter Gewinn --------------
    # Zweite Y-Achse für den kumulierten Gewinn erstellen
    ax3 = ax2.twinx()

    # Energiestand-Historie in DataFrame umwandeln
    energy_df = pd.DataFrame(energy_history)

    if not energy_df.empty:
        # Zeitstempel für Energiegeschichte hinzufügen
        energy_df["datetime"] = energy_df["time_index"].apply(
            lambda idx: (
                prices_df.iloc[idx]["datetime"] if idx < len(prices_df) else None
            )
        )

        # Energiestand als Prozentwert
        energy_df["energy_percent"] = energy_df["energy_level"] / CAPACITY_MWH * 100

        # Batterieladezustand als grüne Fläche
        ax2.fill_between(
            energy_df["datetime"],
            0,
            energy_df["energy_percent"],
            alpha=0.4,
            color="green",
            label=labels["battery"],
        )
        ax2.set_ylim(0, 100)  # 0-100% für Batterie
        ax2.set_ylabel("Ladezustand (%)", color="green")
        ax2.tick_params(axis="y", labelcolor="green")

        # Kumulierter Gewinn plotten (nur wenn Transaktionen vorhanden)
        if has_transactions:
            transactions_df = transactions_df.sort_values("index")
            transactions_df["cash_flow"] = 0.0

            if "cost" in transactions_df.columns:
                idx_charge = transactions_df["type"] == "charge"
                if idx_charge.any():
                    transactions_df.loc[idx_charge, "cash_flow"] = -transactions_df.loc[
                        idx_charge, "cost"
                    ]

            if "revenue" in transactions_df.columns:
                idx_discharge = transactions_df["type"] == "discharge"
                if idx_discharge.any():
                    transactions_df.loc[idx_discharge, "cash_flow"] = (
                        transactions_df.loc[idx_discharge, "revenue"]
                    )

            transactions_df["cumulative_cash"] = transactions_df["cash_flow"].cumsum()

            sorted_trans = transactions_df.sort_values("index")

            # Erstelle erweiterte Liste mit allen Zeitpunkten
            all_times = []
            cumulative_cash_values = []
            current_cash = 0

            for datetime_val in prices_df["datetime"]:
                # Finde alle Transaktionen bis zu diesem Zeitpunkt
                idx = prices_df[prices_df["datetime"] == datetime_val].index[0]
                trans_until_now = sorted_trans[sorted_trans["index"] <= idx]

                if not trans_until_now.empty:
                    current_cash = trans_until_now["cumulative_cash"].iloc[-1]

                all_times.append(datetime_val)
                cumulative_cash_values.append(current_cash)

            # Plot als Stufenfunktion
            ax3.step(
                all_times,
                cumulative_cash_values,
                where="post",
                color="blue",
                label="Kum. " + labels["profit"],
            )

        ax3.set_ylabel(labels["profit"] + " (€)", color="blue")
        ax3.tick_params(axis="y", labelcolor="blue")

    # X-Achse formatieren
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax2.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    plt.xticks(rotation=45, ha="right")
    ax2.set_xlabel(labels["time"])
    ax2.grid(True, linestyle="-", color="lightgray", alpha=0.7)

    # Legende für den unteren Plot
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax3.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

    # Formatiere Titel
    if has_transactions:
        # Statistik für den Titel berechnen
        charge_count = len(transactions_df[transactions_df["type"] == "charge"])
        discharge_count = len(transactions_df[transactions_df["type"] == "discharge"])
        daily_profit = transactions_df["cash_flow"].sum()

        # Zyklen berechnen, falls nicht übergeben
        if daily_cycles is None:
            daily_cycles = 0.0
            # Wenn discharge_amount_gross vorhanden, ist das genauer
            if (
                "amount_gross" in transactions_df.columns
                and transactions_df["type"].eq("discharge").any()
            ):
                total_discharge = transactions_df[
                    transactions_df["type"] == "discharge"
                ]["amount_gross"].sum()
                daily_cycles = total_discharge / CAPACITY_MWH
            # Sonst amount verwenden
            elif (
                "amount" in transactions_df.columns
                and transactions_df["type"].eq("discharge").any()
            ):
                total_discharge = transactions_df[
                    transactions_df["type"] == "discharge"
                ]["amount"].sum()
                daily_cycles = total_discharge / CAPACITY_MWH

        plt.suptitle(
            f'{labels["title"]}: {labels["weekday"]}, {labels["date"]}', fontsize=12
        )
        fig.text(
            0.5,
            0.91,
            f'{labels["total_profit"]}: {daily_profit:.2f} €, {labels["cycles"]}: {daily_cycles:.2f}',
            ha="center",
        )
    else:
        plt.suptitle(f'Abb_Tagesanalyse: {labels["weekday"]}, {labels["date"]}')

    plt.tight_layout()
    plt.subplots_adjust(top=0.9, hspace=0.1)

    if save_plot:
        # Verzeichnis erstellen falls es nicht existiert
        os.makedirs(output_dir, exist_ok=True)

        # Dateiname erstellen
        filename = os.path.join(output_dir, f"tag_{date.strftime('%Y%m%d')}.png")
        plt.savefig(filename, dpi=300, bbox_inches="tight")

    if show_plot:
        plt.show()
    else:
        plt.close("all")


def plot_economic_results_extended(economic_results, output_path=None):
    """
    Erstellt erweiterte Visualisierungen der wirtschaftlichen Ergebnisse.
    Korrigierte Version mit verbesserter Fehlerbehandlung und klareren Visualisierungen.
    """
    import matplotlib.pyplot as plt
    import numpy as np
    import os
    from matplotlib.ticker import FuncFormatter
    import logging
    import config

    # Simulationsjahre aus der Konfiguration übernehmen
    years = getattr(config, "SIMULATION_YEARS")

    logging.debug("Starte wirtschaftliche Visualisierung...")

    # Farbdefinitionen
    colors = {
        "capex": "#D62728",  # Rot
        "opex": "#FF9896",  # Helles Rot
        "revenue": "#2CA02C",  # Grün
        "profit": "#98DF8A",  # Helles Grün
        "cumulative": "#1F77B4",  # Blau
        "capacity": "#9467BD",  # Lila
        "npv": "#FF7F0E",  # Orange
        "breakeven": "#8C564B",  # Braun
    }

    # Daten extrahieren mit Fehlerbehandlung
    try:
        annual_revenues = economic_results["simulation"]["annual_revenues"]
        remaining_capacity = economic_results["simulation"]["remaining_capacity"]

        # Sicherstellen, dass Arrays die gleiche Länge haben wie der konfigurierte Zeitraum
        if len(annual_revenues) != years:
            logging.warning(
                f"Einnahmen-Array anpassen: {len(annual_revenues)} -> {years}"
            )
            if len(annual_revenues) < years:
                # Erweitern mit letztem Wert
                last_revenue = annual_revenues[-1] if annual_revenues else 0.0
                annual_revenues = list(annual_revenues) + [last_revenue] * (
                    years - len(annual_revenues)
                )
            else:
                # Kürzen
                annual_revenues = annual_revenues[:years]

        if len(remaining_capacity) != years:
            logging.warning(
                f"Kapazitätsarray anpassen: {len(remaining_capacity)} -> {years}"
            )
            if len(remaining_capacity) < years:
                # Erweitern mit letztem Wert
                last_capacity = remaining_capacity[-1] if remaining_capacity else 1.0
                remaining_capacity = list(remaining_capacity) + [last_capacity] * (
                    years - len(remaining_capacity)
                )
            else:
                # Kürzen
                remaining_capacity = remaining_capacity[:years]

        capex = economic_results["capex"]["total_capex"]
        annual_opex = economic_results.get("opex", {}).get("total_opex", capex * 0.02)
        discount_rate = getattr(
            config, "DISCOUNT_RATE"
        )  # Verwende den Wert aus der Konfiguration
        npv = economic_results.get("npv", {}).get("npv", 0)

    except KeyError as e:
        logging.error(f"Fehlende Daten in economic_results: {e}")
        return None

    # Figure 1: Cash-Flow-Analyse
    fig1, ax1 = plt.subplots(figsize=(10, 6))

    # Jahre für X-Achse mit Initial-Jahr
    year_labels = ["Initial"] + [f"{i+1}" for i in range(years)]
    x_positions = np.arange(len(year_labels))

    # Cash-Flow-Komponenten
    # Jahr 0: CAPEX
    ax1.bar(0, -capex, color=colors["capex"], label="CAPEX", alpha=0.8, width=0.6)

    # Jahre 1-n: OPEX, Einnahmen und Netto-Gewinn
    for i in range(years):
        if i < len(annual_revenues):
            # OPEX (negativ)
            ax1.bar(
                i + 1,
                -annual_opex,
                color=colors["opex"],
                label="OPEX" if i == 0 else "",
                alpha=0.8,
                width=0.6,
            )

            # Einnahmen (positiv, aufbauend auf OPEX)
            ax1.bar(
                i + 1,
                annual_revenues[i],
                bottom=-annual_opex,
                color=colors["revenue"],
                label="Einnahmen" if i == 0 else "",
                alpha=0.8,
                width=0.6,
            )

            # Netto-Gewinn als durchsichtiger Overlay
            net_profit = annual_revenues[i] - annual_opex
            if net_profit > 0:
                ax1.bar(
                    i + 1,
                    net_profit,
                    color=colors["profit"],
                    label="Netto-Gewinn" if i == 0 else "",
                    alpha=0.3,
                    width=0.6,
                )

    # Kumulativer Cash-Flow berechnen
    cash_flows = [-capex] + [annual_revenues[i] - annual_opex for i in range(years)]
    cumulative_undiscounted = np.cumsum(cash_flows)

    # Diskontierter Cash-Flow
    discounted_cash_flows = [-capex]
    for i in range(years):
        discounted_cf = (annual_revenues[i] - annual_opex) / (
            (1 + discount_rate) ** (i + 1)
        )
        discounted_cash_flows.append(discounted_cf)
    cumulative_discounted = np.cumsum(discounted_cash_flows)

    # Linien für kumulative Cash-Flows
    ax1.plot(
        x_positions,
        cumulative_undiscounted,
        "o-",
        color=colors["cumulative"],
        label="Kumulativer Cash-Flow",
    )
    ax1.plot(
        x_positions,
        cumulative_discounted,
        "s--",
        color=colors["npv"],
        label=f"Diskontierter Cash-Flow (NPV)",
    )

    # Break-Even-Punkt markieren
    breakeven_idx = np.where(cumulative_undiscounted > 0)[0]
    breakeven_point = None
    if len(breakeven_idx) > 0:
        be_year = breakeven_idx[0]
        breakeven_point = be_year
        ax1.axvline(x=be_year, color=colors["breakeven"], linestyle=":", alpha=0.7)
        ax1.text(
            be_year,
            ax1.get_ylim()[1] * 0.9,
            f"Break-Even\n(Jahr {be_year})",
            ha="center",
            va="top",
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
        )

    # Formatierung
    ax1.axhline(y=0, color="black", linestyle="-", alpha=0.3)
    ax1.set_title("Cash-Flow-Analyse über Projektlaufzeit")
    ax1.set_xlabel("Projektjahr")
    ax1.set_ylabel("Cash-Flow (€)")

    # Achsenbeschriftung anpassen
    ax1.set_xlim(0, years)  # X-Achse auf konfigurierte Jahre begrenzen
    ax1.set_xticks(x_positions)
    ax1.set_xticklabels(year_labels, rotation=0, ha="center")

    # Y-Achse formatieren
    def euro_formatter(x, pos):
        return f"{x/1000:,.0f} T€".replace(",", ".")

    ax1.yaxis.set_major_formatter(FuncFormatter(euro_formatter))

    # Legende optimieren
    handles, labels = ax1.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax1.legend(
        by_label.values(),
        by_label.keys(),
        loc="best",
        frameon=True,
        fancybox=True,
        shadow=True,
    )

    # Grid verbessern
    ax1.grid(True, alpha=0.3, linestyle="--")
    ax1.set_axisbelow(True)

    # Zusätzliche Informationen
    textstr = f"NPV: {npv:,.0f} €"
    props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)
    ax1.text(
        0.5,  # x-Position: 50% vom linken Rand (genau mittig)
        0.02,  # y-Position: 2% vom unteren Rand (ganz unten)
        textstr,
        transform=ax1.transAxes,
        verticalalignment="bottom",  # Textausrichtung: an der Unterkante der Box
        horizontalalignment="center",  # Textausrichtung: mittig zur x-Koordinate
        bbox=props,
    )

    plt.tight_layout()

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(
            f"{os.path.splitext(output_path)[0]}_cash_flow_improved.png",
            dpi=300,
            bbox_inches="tight",
        )
    plt.close()

    # Figure 2: Kapazitäts- und Wirtschaftsentwicklung (Verbessert)
    fig2, ax2 = plt.subplots(figsize=(14, 8))

    # Daten vorbereiten
    years_array = np.arange(1, years + 1)
    capacity_percentage = [
        (cap / remaining_capacity[0] * 100) if remaining_capacity[0] > 0 else 100
        for cap in remaining_capacity
    ]

    # Primäre Y-Achse: Finanzielle Kennzahlen
    ax2.bar(
        years_array - 0.2,
        annual_revenues,
        width=0.4,
        label="Jahreseinnahmen",
        color=colors["revenue"],
        alpha=0.7,
    )

    profits = [rev - annual_opex for rev in annual_revenues]
    ax2.bar(
        years_array + 0.2,
        profits,
        width=0.4,
        label="Jahresgewinn",
        color=colors["profit"],
        alpha=0.7,
    )

    ax2.set_xlabel("Betriebsjahr")
    ax2.set_ylabel("Jährliche Beträge (€)", color="green")
    ax2.tick_params(axis="y", labelcolor="green")

    # X-Achse anpassen
    ax2.set_xlim(0.5, years + 0.5)
    ax2.set_xticks(years_array)

    # Sekundäre Y-Achse: Kapazität
    ax3 = ax2.twinx()
    ax3.plot(
        years_array,
        capacity_percentage,
        "o-",
        color=colors["capacity"],
        label="Batteriekapazität",
    )
    ax3.set_ylabel("Verbleibende Kapazität (%)", color=colors["capacity"])
    ax3.tick_params(axis="y", labelcolor=colors["capacity"])
    ax3.set_ylim(0, 105)

    # Titel und Formatierung
    ax2.set_title("Wirtschaftliche und technische Entwicklung")
    ax2.grid(True, alpha=0.3, axis="y")
    ax2.set_axisbelow(True)

    # Kombinierte Legende
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax3.get_legend_handles_labels()
    ax2.legend(
        lines1 + lines2,
        labels1 + labels2,
        loc="best",
        frameon=True,
        fancybox=True,
        shadow=True,
    )

    plt.tight_layout()

    if output_path:
        plt.savefig(
            f"{os.path.splitext(output_path)[0]}_capacity_revenue_improved.png",
            dpi=300,
            bbox_inches="tight",
        )
    plt.close()

    # Rückgabe der Ergebnisse
    results = {
        "npv": npv,
        "breakeven_point": breakeven_point,
        "total_revenue": sum(annual_revenues),
        "total_opex": annual_opex * years,
        "final_capacity_percent": (
            capacity_percentage[-1] if capacity_percentage else 100
        ),
    }

    return results


def plot_lcos_analysis(economic_results, output_path=None):
    """
    Erstellt eine LCOS-Analyse (Levelized Cost of Storage) für den Energiespeicher.
    """
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.ticker import FuncFormatter
    import os
    import config  # Config-Import hinzufügen

    # Daten extrahieren
    capex = economic_results["capex"]["total_capex"]
    if "annual_opex" in economic_results["opex"]:
        annual_opex = economic_results["opex"]["annual_opex"]
    else:
        annual_opex = economic_results["opex"]["total_opex"]

    years = len(economic_results["simulation"]["annual_revenues"])
    annual_revenues = economic_results["simulation"]["annual_revenues"]
    annual_cycles = economic_results["simulation"].get("annual_cycles", [627] * years)
    remaining_capacity = economic_results["simulation"]["remaining_capacity"]

    # LCOS-Komponenten berechnen
    # Diskontierungsrate aus Config übernehmen
    discount_rate = config.DISCOUNT_RATE / 100  # Umrechnung von Prozent auf Dezimalwert

    # Jährliche Kosten diskontieren
    discounted_opex = [
        annual_opex / ((1 + discount_rate) ** (year + 1)) for year in range(years)
    ]
    total_discounted_opex = sum(discounted_opex)

    # Jährliche Zyklen und Kapazität
    total_cycles = sum(annual_cycles)
    avg_capacity = np.mean(remaining_capacity)

    # Gesamtenergiemenge berechnen (MWh)
    total_energy_throughput = total_cycles * avg_capacity  # Gesamt-Durchsatz in MWh

    # LCOS berechnen (€/MWh)
    lcos = (capex + total_discounted_opex) / total_energy_throughput

    # LCOS-Komponenten für Visualisierung
    capex_per_mwh = capex / total_energy_throughput
    opex_per_mwh = total_discounted_opex / total_energy_throughput

    # Vergleichswerte
    market_price_avg = np.mean(
        [
            abs(revenue / (cycle * avg_capacity))
            for revenue, cycle in zip(annual_revenues, annual_cycles)
            if cycle > 0
        ]
    )

    # Figure 1: LCOS-Komponenten
    plt.figure(figsize=(10, 6))

    plt.bar("CAPEX", capex_per_mwh, color="#D62728", alpha=0.8)
    plt.bar("OPEX", opex_per_mwh, color="#FF9896", alpha=0.8)
    plt.bar("Gesamt LCOS", lcos, color="#1F77B4", alpha=0.5)
    plt.axhline(
        y=market_price_avg,
        color="green",
        linestyle="--",
        label=f"Ø Marktpreis: {market_price_avg:.2f} €/MWh",
    )

    plt.ylabel("€/MWh", fontsize=12)
    plt.title(
        "Levelized Cost of Storage (LCOS) - Komponenten", fontsize=14, fontweight="bold"
    )
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Informationstext
    plt.figtext(
        0.02,
        0.02,
        f"Gesamt LCOS: {lcos:.2f} €/MWh\n"
        f"Gesamter Energiedurchsatz: {total_energy_throughput:.1f} MWh",
        fontsize=10,
        bbox=dict(
            facecolor="white", alpha=0.8, edgecolor="gray", boxstyle="round,pad=0.5"
        ),
    )

    # Speichern
    if output_path:
        dir_path = os.path.dirname(output_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        lcos_path = f"{os.path.splitext(output_path)[0]}_lcos_components.png"
        plt.savefig(lcos_path, dpi=300, bbox_inches="tight")

    plt.close("all")

    return {
        "lcos": lcos,
        "capex_per_mwh": capex_per_mwh,
        "opex_per_mwh": opex_per_mwh,
        "total_energy_throughput": total_energy_throughput,
    }


def plot_monthly_profit_analysis(daily_results, output_path=None):
    """
    Erstellt eine Visualisierung der monatlichen Gewinne und saisonaler Muster.
    Korrigierte Version mit robuster Datumskonvertierung.

    Parameters:
    - daily_results: Liste mit täglichen Analyseergebnissen
    - output_path: Pfad für die Ausgabedatei-Präfix
    """
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np
    import os
    import logging
    from datetime import datetime

    logger = logging.getLogger(__name__)
    logger.info("Starte korrigierte monatliche Gewinnanalyse...")

    # Sicherstellen, dass wir überhaupt Daten haben
    if not daily_results or len(daily_results) == 0:
        logger.warning("Keine Daten für monatliche Gewinnanalyse vorhanden.")
        return {}

    # Daten in DataFrame konvertieren mit expliziten Typen und robuster Datumskonvertierung
    results_data = []
    for result in daily_results:
        if result and "date" in result and "profit" in result:
            # Sichere Datumskonvertierung - das hier löst das Problem
            date_val = None
            try:
                if isinstance(result["date"], pd.Timestamp):
                    date_val = result["date"].to_pydatetime()
                elif isinstance(result["date"], np.datetime64):
                    # Explizite Konvertierung von numpy.datetime64
                    date_val = pd.Timestamp(result["date"]).to_pydatetime()
                else:
                    date_val = pd.to_datetime(result["date"]).to_pydatetime()
            except Exception as e:
                logger.debug(
                    f"Datumskonvertierung fehlgeschlagen für {result['date']}: {e}"
                )
                continue

            if date_val is None:
                continue

            results_data.append(
                {
                    "date": date_val,
                    "profit": float(result["profit"]),
                    "trades": int(
                        result.get("charge_count", 0) + result.get("discharge_count", 0)
                    ),
                    "energy_charged": float(result.get("total_charged", 0)),
                    "energy_discharged": float(result.get("total_gross_energy", 0)),
                }
            )

    if not results_data:
        logger.warning("Keine gültigen Daten nach Typkonvertierung.")
        return {}

    # DataFrame erstellen
    results_df = pd.DataFrame(results_data)
    logger.info(f"DataFrame erstellt mit {len(results_df)} Zeilen")

    # Explizite Datumsextraktionen als separate Spalten mit try/except für robuste Fehlerbehandlung
    results_df["month"] = [d.month for d in results_df["date"]]
    results_df["year"] = [d.year for d in results_df["date"]]
    results_df["day_of_week"] = [d.weekday() for d in results_df["date"]]

    # Formatierte Strings für Anzeigezwecke
    results_df["month_name"] = [d.strftime("%b") for d in results_df["date"]]
    results_df["year_month_str"] = [d.strftime("%Y-%m") for d in results_df["date"]]

    # Monatliche Aggregation - explizite Gruppierung nach Integer-Spalten
    monthly_df = (
        results_df.groupby(["year", "month"])
        .agg(
            {
                "profit": "sum",
                "trades": "sum",
                "energy_charged": "sum",
                "energy_discharged": "sum",
                "date": "min",  # Erster Tag des Monats für die Sortierung
                "month_name": "first",
                "year_month_str": "first",
            }
        )
        .reset_index()
    )

    # Ergebnis sortieren
    monthly_df = monthly_df.sort_values("date")

    # Aggregation nach Monaten (über Jahre hinweg)
    monthly_pattern = (
        results_df.groupby("month")
        .agg(
            {
                "profit": ["mean", "sum", "std"],
                "trades": ["mean", "sum"],
                "month_name": "first",
            }
        )
        .reset_index()
    )

    monthly_pattern = monthly_pattern.sort_values("month")

    # ---------------------- FIGUREN ERSTELLEN ----------------------

    # Figure 1: Monatliche Gewinne
    plt.figure(figsize=(12, 7))

    # X-Achse als reine Kategorien verwenden, nicht als Daten
    x_values = range(len(monthly_df))
    x_labels = monthly_df["year_month_str"].tolist()

    bars = plt.bar(x_values, monthly_df["profit"], color="#1F77B4", alpha=0.7)

    # Schlechte Monate rot einfärben
    for i, bar in enumerate(bars):
        if monthly_df["profit"].iloc[i] < 0:
            bar.set_color("#D62728")

    # X-Achsenbeschriftungen
    plt.xticks(x_values, x_labels, rotation=45, ha="right")

    # Bei vielen Monaten nur jeden n-ten Label zeigen
    if len(monthly_df) > 12:
        n = max(1, len(monthly_df) // 6)
        for i, tick in enumerate(plt.gca().xaxis.get_major_ticks()):
            if i % n != 0:
                tick.set_visible(False)

    # Zweite Y-Achse für kumulativen Wert
    ax2 = plt.gca().twinx()
    cumulative = np.cumsum(monthly_df["profit"])
    ax2.plot(x_values, cumulative, "r-", linewidth=2)

    # Layout anpassen
    plt.grid(True, axis="x", alpha=0.3)
    plt.grid(False, axis="y")

    plt.title("Monatliche Gewinnentwicklung", fontsize=14, fontweight="bold")
    plt.gca().set_ylabel("Monatlicher Gewinn (€)", fontsize=12)
    ax2.set_ylabel("Kumulativer Gewinn (€)", color="red", fontsize=12)

    # Speichern
    if output_path:
        dir_path = os.path.dirname(output_path)
        os.makedirs(dir_path, exist_ok=True)
        monthly_path = f"{os.path.splitext(output_path)[0]}_monthly_profit.png"
        plt.savefig(monthly_path, dpi=300, bbox_inches="tight")

    plt.close("all")

    # Figure 2: Saisonales Muster
    plt.figure(figsize=(10, 6))

    # Extrahiere die Werte korrekt
    profit_means = [x for x in monthly_pattern["profit"]["mean"]]
    profit_stds = [x for x in monthly_pattern["profit"]["std"]]

    # X-Achse als einfache Kategorien
    month_indices = range(len(monthly_pattern))
    month_names = monthly_pattern["month_name"].tolist()

    bars = plt.bar(
        month_indices,
        profit_means,
        yerr=profit_stds,
        capsize=5,
        color="#1F77B4",
        alpha=0.7,
    )

    # Saisonale Trends hervorheben
    mean_profit = np.mean(profit_means)
    for i, bar in enumerate(bars):
        if profit_means[i] < mean_profit:
            bar.set_color("#AEC7E8")
        if profit_means[i] < 0:
            bar.set_color("#D62728")
        if profit_means[i] > mean_profit * 1.5:
            bar.set_color("#2CA02C")

    plt.axhline(
        y=mean_profit,
        color="red",
        linestyle="--",
        label=f"Durchschnitt: {mean_profit:.2f} €/Tag",
    )

    plt.xticks(month_indices, month_names)

    plt.title("Saisonales Muster der täglichen Gewinne", fontsize=14, fontweight="bold")
    plt.ylabel("Durchschnittlicher täglicher Gewinn (€)", fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Speichern
    if output_path:
        seasonal_path = f"{os.path.splitext(output_path)[0]}_seasonal_pattern.png"
        plt.savefig(seasonal_path, dpi=300, bbox_inches="tight")

    plt.close("all")

    # Figure 3: Heatmap für Wochentag x Monat - Nur erstellen, wenn genug Daten
    if len(results_df) >= 30:  # Mindestens 30 Tage für eine sinnvolle Heatmap
        plt.figure(figsize=(12, 8))

        weekdays = [
            "Montag",
            "Dienstag",
            "Mittwoch",
            "Donnerstag",
            "Freitag",
            "Samstag",
            "Sonntag",
        ]

        # Manuelle Pivot-Tabelle erstellen
        heatmap_matrix = np.zeros((7, 12))
        count_matrix = np.zeros((7, 12))

        for _, row in results_df.iterrows():
            day_idx = row["day_of_week"]
            month_idx = row["month"] - 1  # 0-basierter Index für Monate
            profit = row["profit"]

            # Werte zur Matrix hinzufügen
            heatmap_matrix[day_idx, month_idx] += profit
            count_matrix[day_idx, month_idx] += 1

        # Durchschnitt berechnen mit Nulldivision-Handling
        with np.errstate(divide="ignore", invalid="ignore"):
            avg_matrix = np.divide(heatmap_matrix, count_matrix)
            avg_matrix = np.nan_to_num(avg_matrix)  # NaN durch 0 ersetzen

        # Heatmap zeichnen
        plt.imshow(avg_matrix, cmap="RdYlGn", aspect="auto", interpolation="nearest")

        # Beschriftungen
        plt.colorbar(label="Durchschnittlicher täglicher Gewinn (€)")
        months = [
            "Jan",
            "Feb",
            "Mär",
            "Apr",
            "Mai",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Okt",
            "Nov",
            "Dez",
        ]
        plt.xticks(range(12), months)
        plt.yticks(range(7), weekdays)

        # Werte in die Zellen eintragen
        for i in range(7):
            for j in range(12):
                value = avg_matrix[i, j]
                if value != 0:  # Nur Werte ungleich 0 anzeigen
                    plt.text(
                        j,
                        i,
                        f"{value:.1f}",
                        ha="center",
                        va="center",
                        color=(
                            "black"
                            if abs(value) < np.max(np.abs(avg_matrix)) / 2
                            else "white"
                        ),
                    )

        plt.title(
            "Heatmap: Durchschnittlicher Gewinn nach Wochentag und Monat",
            fontsize=14,
            fontweight="bold",
        )
        plt.tight_layout()

        # Speichern
        if output_path:
            heatmap_path = f"{os.path.splitext(output_path)[0]}_profit_heatmap.png"
            plt.savefig(heatmap_path, dpi=300, bbox_inches="tight")

        plt.close("all")

    # Beste/schlechteste Monate bestimmen
    try:
        profit_means_list = profit_means
        if profit_means_list:
            best_month_idx = np.argmax(profit_means_list)
            best_month = month_names[best_month_idx]
            worst_month_idx = np.argmin(profit_means_list)
            worst_month = month_names[worst_month_idx]
        else:
            best_month = "Nicht bestimmbar"
            worst_month = "Nicht bestimmbar"
    except Exception as e:
        logger.warning(
            f"Fehler bei der Bestimmung des besten/schlechtesten Monats: {e}"
        )
        best_month = "Nicht bestimmbar"
        worst_month = "Nicht bestimmbar"

    logger.info("Monatliche Gewinnanalyse erfolgreich abgeschlossen.")

    return {
        "monthly_profits": monthly_df["profit"].tolist(),
        "best_month": best_month,
        "worst_month": worst_month,
    }


def plot_breakeven_scenarios(economic_results, output_path=None):
    """
    Erstellt verschiedene Break-Even-Szenarien für den Energiespeicher,
    sowohl mit als auch ohne Diskontierung.
    (Version angepasst für globale rcParams-Einstellungen)
    """
    import matplotlib.pyplot as plt
    import numpy as np
    import os
    from matplotlib.ticker import FuncFormatter

    # --- Datenextraktion (unverändert) ---
    capex = economic_results["capex"]["total_capex"]
    annual_revenues = economic_results["simulation"]["annual_revenues"]
    if "annual_opex" in economic_results["opex"]:
        annual_opex = economic_results["opex"]["annual_opex"]
    else:
        annual_opex = economic_results["opex"]["total_opex"]
    discount_rate = economic_results.get("discount_rate")
    max_years = 20
    years_range = np.arange(max_years + 1)
    scenarios = {
        "Standard (100%)": 1.0,
        "Optimistisch (120%)": 1.2,
        "Sehr optimistisch (150%)": 1.5,
        "Pessimistisch (80%)": 0.8,
        "Sehr pessimistisch (50%)": 0.5,
    }
    colors = {
        "Standard (100%)": "#1F77B4",
        "Optimistisch (120%)": "#2CA02C",
        "Sehr optimistisch (150%)": "#00CC00",
        "Pessimistisch (80%)": "#FF9896",
        "Sehr pessimistisch (50%)": "#D62728",
    }
    breakeven_years_undiscounted = {}
    breakeven_years_discounted = {}

    # ---------------------- Figure 1: Break-Even-Szenarien (nicht diskontiert) ----------------------
    plt.figure(figsize=(12, 7))
    plt.axhline(
        y=capex,
        color="black",
        linestyle="-",
        linewidth=1.5,
        label=f"CAPEX: {capex:,.0f} €".replace(",", "."),
    )

    for scenario, factor in scenarios.items():
        mod_annual_revenues = [revenue * factor for revenue in annual_revenues]
        extended_revenues = mod_annual_revenues + [mod_annual_revenues[-1]] * (
            max_years - len(mod_annual_revenues)
        )
        undiscounted_profits = [revenue - annual_opex for revenue in extended_revenues]
        cumulative_cf = np.cumsum(undiscounted_profits)
        cumulative_cf = np.insert(cumulative_cf, 0, 0)
        try:
            breakeven_index = np.where(cumulative_cf >= capex)[0][0]
            if breakeven_index > 0:
                x1, x2 = breakeven_index - 1, breakeven_index
                y1, y2 = cumulative_cf[x1], cumulative_cf[x2]
                breakeven = x1 + (capex - y1) / (y2 - y1) if y2 != y1 else x1
            else:
                breakeven = 0
        except IndexError:
            breakeven = None
        breakeven_years_undiscounted[scenario] = breakeven

        plt.plot(
            years_range,
            cumulative_cf,
            "-",
            color=colors[scenario],
            alpha=0.8,
            label=(
                f"{scenario}, Break-Even: {breakeven:.1f} Jahre"
                if breakeven
                else f"{scenario}, Break-Even: > {max_years} Jahre"
            ),
        )

    plt.title("Break-Even-Szenarien (nicht diskontiert)")
    plt.xlabel("Jahr")
    plt.ylabel("Kumulativer Cash-Flow (€)")
    plt.legend(loc="upper left")

    def euro_formatter(x, pos):
        return f"{x/1000:,.0f} T€".replace(",", ".")

    plt.gca().yaxis.set_major_formatter(FuncFormatter(euro_formatter))
    plt.xlim(0, max_years)

    if output_path:
        dir_path = os.path.dirname(output_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        scenario_path = f"{os.path.splitext(output_path)[0]}_breakeven_undiscounted.png"
        plt.savefig(scenario_path, dpi=300, bbox_inches="tight")
    plt.close()

    # ---------------------- Figure 2: Break-Even-Szenarien (diskontiert) ----------------------
    plt.figure(figsize=(12, 7))
    plt.axhline(
        y=capex,
        color="black",
        linestyle="-",
        linewidth=1.5,
        label=f"CAPEX: {capex:,.0f} €".replace(",", "."),
    )

    for scenario, factor in scenarios.items():
        mod_annual_revenues = [revenue * factor for revenue in annual_revenues]
        extended_revenues = mod_annual_revenues + [mod_annual_revenues[-1]] * (
            max_years - len(mod_annual_revenues)
        )
        discounted_profits = []
        for year, revenue in enumerate(extended_revenues):
            discount_factor = (1 + discount_rate) ** (year + 1)
            discounted_profit = (revenue - annual_opex) / discount_factor
            discounted_profits.append(discounted_profit)
        cumulative_cf = np.cumsum(discounted_profits)
        cumulative_cf = np.insert(cumulative_cf, 0, 0)
        try:
            breakeven_index = np.where(cumulative_cf >= capex)[0][0]
            if breakeven_index > 0:
                x1, x2 = breakeven_index - 1, breakeven_index
                y1, y2 = cumulative_cf[x1], cumulative_cf[x2]
                breakeven = x1 + (capex - y1) / (y2 - y1) if y2 != y1 else x1
            else:
                breakeven = 0
        except IndexError:
            breakeven = None
        breakeven_years_discounted[scenario] = breakeven

        plt.plot(
            years_range,
            cumulative_cf,
            "-",
            color=colors[scenario],
            alpha=0.8,
            label=(
                f"{scenario}, Break-Even: {breakeven:.1f} Jahre"
                if breakeven
                else f"{scenario}, Break-Even: > {max_years} Jahre"
            ),
        )

    plt.title(f"Break-Even-Szenarien (diskontiert mit {discount_rate*100:.1f}%)")
    plt.xlabel("Jahr")
    plt.ylabel("Kumulativer Cash-Flow (€)")
    plt.legend(loc="upper left")

    plt.gca().yaxis.set_major_formatter(FuncFormatter(euro_formatter))
    plt.xlim(0, max_years)

    if output_path:
        scenario_path = f"{os.path.splitext(output_path)[0]}_breakeven_discounted.png"
        plt.savefig(scenario_path, dpi=300, bbox_inches="tight")
    plt.close()

    # ---------------------- Figure 3: Break-Even-Sensitivitätsanalyse (diskontiert) ----------------------
    plt.figure(figsize=(10, 6))
    revenue_factors = np.linspace(0.5, 2.0, 50)
    breakeven_sensitivity = []

    for factor in revenue_factors:
        mod_annual_revenues = [revenue * factor for revenue in annual_revenues]
        extended_revenues = mod_annual_revenues + [mod_annual_revenues[-1]] * (
            max_years - len(mod_annual_revenues)
        )
        discounted_profits = []
        for year, revenue in enumerate(extended_revenues):
            discount_factor = (1 + discount_rate) ** (year + 1)
            discounted_profit = (revenue - annual_opex) / discount_factor
            discounted_profits.append(discounted_profit)
        cumulative_cf = np.cumsum(discounted_profits)
        cumulative_cf = np.insert(cumulative_cf, 0, 0)
        try:
            breakeven_index = np.where(cumulative_cf >= capex)[0][0]
            if breakeven_index > 0:
                x1, x2 = breakeven_index - 1, breakeven_index
                y1, y2 = cumulative_cf[x1], cumulative_cf[x2]
                breakeven = x1 + (capex - y1) / (y2 - y1) if y2 != y1 else x1
            else:
                breakeven = 0
        except IndexError:
            breakeven = max_years
        breakeven_sensitivity.append(breakeven)

    capped_sensitivity = [min(x, max_years) for x in breakeven_sensitivity]
    plt.plot(revenue_factors * 100, capped_sensitivity, "b-")

    plt.axhline(
        y=10, color="red", linestyle="--", alpha=0.6, label="10-Jahres-Schwelle"
    )
    plt.axhline(y=5, color="green", linestyle=":", alpha=0.6, label="5-Jahres-Schwelle")
    plt.axhline(
        y=15, color="orange", linestyle=":", alpha=0.6, label="15-Jahres-Schwelle"
    )

    point_percentages = [80, 100, 120, 150]
    point_colors = ["blue", "red", "orange", "green"]
    point_labels = []
    for percent, color in zip(point_percentages, point_colors):
        idx = np.abs(revenue_factors * 100 - percent).argmin()
        be_years = breakeven_sensitivity[idx]
        label_text = (
            f"{percent}%: >{max_years-1} Jahre"
            if be_years >= max_years
            else f"{percent}%: {be_years:.1f} Jahre"
        )
        point_labels.append(label_text)
        plt.plot(percent, min(be_years, max_years), "o", color=color)

    legend_elements = [
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor="red",
            markersize=10,
            label=point_labels[1],
        ),
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor="blue",
            markersize=10,
            label=point_labels[0],
        ),
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor="orange",
            markersize=10,
            label=point_labels[2],
        ),
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor="green",
            markersize=10,
            label=point_labels[3],
        ),
    ]
    plt.legend(
        handles=legend_elements
        + [
            plt.Line2D(
                [0], [0], color="red", linestyle="--", label="10-Jahres-Schwelle"
            ),
            plt.Line2D(
                [0], [0], color="green", linestyle=":", label="5-Jahres-Schwelle"
            ),
            plt.Line2D(
                [0], [0], color="orange", linestyle=":", label="15-Jahres-Schwelle"
            ),
        ],
        loc="best",
    )

    plt.title(f"Break-Even-Sensitivität mit Diskontierung ({discount_rate*100:.1f}%)")
    plt.xlabel("Einnahmen (% vom Basisfall)")
    plt.ylabel("Break-Even-Zeit (Jahre)")

    plt.ylim(0, max_years)
    plt.xlim(revenue_factors[0] * 100, revenue_factors[-1] * 100)

    if output_path:
        sensitivity_path = (
            f"{os.path.splitext(output_path)[0]}_sensitivity_discounted.png"
        )
        plt.savefig(sensitivity_path, dpi=300, bbox_inches="tight")
    plt.close("all")

    return {
        "breakeven_years_undiscounted": breakeven_years_undiscounted,
        "breakeven_years_discounted": breakeven_years_discounted,
        "standard_breakeven_undiscounted": breakeven_years_undiscounted.get(
            "Standard (100%)"
        ),
        "standard_breakeven_discounted": breakeven_years_discounted.get(
            "Standard (100%)"
        ),
    }


def plot_trading_heatmap(daily_results, output_path=None):
    """
    Erstellt eine Heatmap der Handelsaktivitäten nach Stunde und Wochentag,
    basierend auf den tatsächlichen Zyklen aus den Tagesvisualisierungen.

    Parameters:
    -----------
    daily_results : list
        Liste mit den täglichen Analyseergebnissen
    output_path : str, optional
        Basispfad für die Ausgabedateien
    """
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np
    import os
    import logging

    logger = logging.getLogger(__name__)
    logger.info("Erstelle Trading-Heatmap basierend auf tatsächlichen Zyklusdaten...")

    # Sammeln der Handelsdaten aus den täglichen Ergebnissen
    trading_data = []

    for result in daily_results:
        if not result:
            continue

        # Datum aus dem Ergebnis extrahieren
        if "date" not in result:
            continue

        date = result["date"]

        # Transaktionen aus dem Ergebnis extrahieren
        if "transactions" not in result or result["transactions"].empty:
            continue

        transactions = result["transactions"]

        # Jede Transaktion mit Datum und Wochentag versehen
        for _, trans in transactions.iterrows():
            if "type" not in trans or "index" not in trans:
                continue

            # Zeitinformationen berechnen
            hour = int(trans["index"]) // 4  # 15-Minuten-Intervalle zu Stunden

            # Datum als Python datetime behandeln
            try:
                if isinstance(date, pd.Timestamp):
                    date_obj = date.to_pydatetime()
                else:
                    date_obj = pd.to_datetime(date).to_pydatetime()

                weekday = date_obj.weekday()  # 0 = Montag, 6 = Sonntag
            except:
                logger.warning(
                    f"Fehler bei der Datumsverarbeitung für Transaktion, überspringe"
                )
                continue

            # Nur Transaktionen mit interval==0 berücksichtigen (Beginn eines Lade-/Entladevorgangs)
            if "interval" in trans and trans["interval"] == 0:
                # Werte für die Heatmap
                trading_data.append(
                    {
                        "date": date_obj,
                        "hour": hour,
                        "weekday": weekday,
                        "type": trans["type"],
                        "amount": float(trans.get("amount", 0)),
                        "price": float(trans.get("price", 0)),
                    }
                )

    if not trading_data:
        logger.warning("Keine gültigen Handelsdaten für Heatmap gefunden")
        return {}

    # DataFrame erstellen
    trading_df = pd.DataFrame(trading_data)
    logger.info(f"Trading-Daten gesammelt: {len(trading_df)} Handelsereignisse")

    # Lade- und Entladeereignisse trennen
    charge_df = trading_df[trading_df["type"] == "charge"]
    discharge_df = trading_df[trading_df["type"] == "discharge"]

    # Erstellen der Heatmaps durch manuelle Zählung
    charge_heatmap = np.zeros((24, 7))  # (Stunden, Wochentage)
    discharge_heatmap = np.zeros((24, 7))

    # Laden-Heatmap füllen
    for _, row in charge_df.iterrows():
        hour = int(row["hour"])
        weekday = int(row["weekday"])
        if 0 <= hour < 24 and 0 <= weekday < 7:
            charge_heatmap[hour, weekday] += 1

    # Entladen-Heatmap füllen
    for _, row in discharge_df.iterrows():
        hour = int(row["hour"])
        weekday = int(row["weekday"])
        if 0 <= hour < 24 and 0 <= weekday < 7:
            discharge_heatmap[hour, weekday] += 1

    # Wochentags- und Stundenbezeichnungen
    weekdays = [
        "Montag",
        "Dienstag",
        "Mittwoch",
        "Donnerstag",
        "Freitag",
        "Samstag",
        "Sonntag",
    ]
    hours = [f"{h:02d}:00" for h in range(24)]

    # Figure 1: Heatmap für Ladevorgänge
    plt.figure(figsize=(10, 8))
    plt.imshow(charge_heatmap, cmap="Blues", aspect="auto", interpolation="nearest")
    plt.colorbar(label="Anzahl Ladevorgänge")
    plt.xticks(
        range(7), weekdays, rotation=0, ha="center"
    )  # 0-Grad-Rotation (horizontal)
    plt.yticks(range(24), hours)

    # Werte in die Zellen eintragen
    for i in range(24):
        for j in range(7):
            value = charge_heatmap[i, j]
            if value > 0:  # Nur Werte > 0 anzeigen
                plt.text(
                    j,
                    i,
                    f"{value:.0f}",
                    ha="center",
                    va="center",
                    color="black" if value < np.max(charge_heatmap) / 2 else "white",
                )

    plt.title(
        "Heatmap: Ladevorgänge nach Stunde und Wochentag",
        fontsize=14,
        fontweight="bold",
    )
    plt.tight_layout()  # Wichtig für die richtige Anzeige der Labels

    # Speichern
    if output_path:
        dir_path = os.path.dirname(output_path)
        os.makedirs(dir_path, exist_ok=True)
        charge_path = f"{os.path.splitext(output_path)[0]}_charge_heatmap.png"
        plt.savefig(charge_path, dpi=300, bbox_inches="tight")

    plt.close()

    # Figure 2: Heatmap für Entladevorgänge
    plt.figure(figsize=(10, 8))

    # Überprüfe, ob es überhaupt Entladevorgänge gibt
    if np.sum(discharge_heatmap) > 0:
        plt.imshow(
            discharge_heatmap, cmap="Reds", aspect="auto", interpolation="nearest"
        )
        plt.colorbar(label="Anzahl Entladevorgänge")

        # Werte in die Zellen eintragen
        for i in range(24):
            for j in range(7):
                value = discharge_heatmap[i, j]
                if value > 0:  # Nur Werte > 0 anzeigen
                    plt.text(
                        j,
                        i,
                        f"{value:.0f}",
                        ha="center",
                        va="center",
                        color=(
                            "black"
                            if value < np.max(discharge_heatmap) / 2
                            else "white"
                        ),
                    )
    else:
        # Wenn keine Entladevorgänge, zeige leere Heatmap mit Hinweis
        plt.imshow(
            discharge_heatmap,
            cmap="Reds",
            aspect="auto",
            interpolation="nearest",
            vmin=0,
            vmax=1,
        )
        plt.colorbar(label="Anzahl Entladevorgänge")
        plt.text(
            3,
            12,
            "Keine Entladevorgänge gefunden",
            ha="center",
            va="center",
            fontsize=16,
            bbox=dict(boxstyle="round,pad=0.5", facecolor="yellow", alpha=0.8),
        )

    plt.xticks(
        range(7), weekdays, rotation=0, ha="center"
    )  # 0-Grad-Rotation (horizontal)
    plt.yticks(range(24), hours)
    plt.title(
        "Heatmap: Entladevorgänge nach Stunde und Wochentag",
        fontsize=14,
        fontweight="bold",
    )
    plt.tight_layout()  # Für die richtige Anzeige der Labels

    # Speichern
    if output_path:
        discharge_path = f"{os.path.splitext(output_path)[0]}_discharge_heatmap.png"
        plt.savefig(discharge_path, dpi=300, bbox_inches="tight")

    plt.close()

    # Figure 3: Kombinierte Heatmap (Differenz zwischen Laden und Entladen)
    plt.figure(figsize=(10, 8))

    # Differenz berechnen: Positive Werte = mehr Laden, Negative = mehr Entladen
    diff_heatmap = charge_heatmap - discharge_heatmap

    # Divergierende Farbpalette
    max_abs_value = max(
        np.max(np.abs(diff_heatmap)), 1
    )  # Mindestens 1, um Division durch 0 zu vermeiden

    plt.imshow(
        diff_heatmap,
        cmap="RdBu",
        aspect="auto",
        interpolation="nearest",
        vmin=-max_abs_value,
        vmax=max_abs_value,
    )
    plt.colorbar(label="Differenz (Laden - Entladen)")

    # Werte in die Zellen eintragen
    for i in range(24):
        for j in range(7):
            value = diff_heatmap[i, j]
            if value != 0:
                plt.text(
                    j,
                    i,
                    f"{value:.0f}",
                    ha="center",
                    va="center",
                    color="black" if abs(value) < max_abs_value / 2 else "white",
                )

    plt.xticks(
        range(7), weekdays, rotation=0, ha="center"
    )  # 0-Grad-Rotation (horizontal)
    plt.yticks(range(24), hours)
    plt.title(
        "Heatmap: Differenz zwischen Lade- und Entladevorgängen",
        fontsize=14,
        fontweight="bold",
    )
    plt.tight_layout()  # Für die richtige Anzeige der Labels

    # Speichern
    if output_path:
        diff_path = f"{os.path.splitext(output_path)[0]}_diff_heatmap.png"
        plt.savefig(diff_path, dpi=300, bbox_inches="tight")

    plt.close()

    # Statistiken zurückgeben
    charge_sum = np.sum(charge_heatmap)
    discharge_sum = np.sum(discharge_heatmap)

    most_active_charge_hour = (
        int(np.sum(charge_heatmap, axis=1).argmax()) if charge_sum > 0 else None
    )
    most_active_discharge_hour = (
        int(np.sum(discharge_heatmap, axis=1).argmax()) if discharge_sum > 0 else None
    )
    most_active_weekday = (
        int(np.sum(charge_heatmap + discharge_heatmap, axis=0).argmax())
        if (charge_sum + discharge_sum) > 0
        else None
    )

    logger.info(
        f"Trading-Heatmap erstellt: {int(charge_sum)} Ladevorgänge, {int(discharge_sum)} Entladevorgänge"
    )

    return {
        "total_charges": int(charge_sum),
        "total_discharges": int(discharge_sum),
        "most_active_charge_hour": most_active_charge_hour,
        "most_active_discharge_hour": most_active_discharge_hour,
        "most_active_weekday": most_active_weekday,
    }


def plot_cycle_analysis(daily_results, output_path=None):
    """
    Erstellt Visualisierungen zur Zyklenanalyse des Batteriespeichers.

    Parameters:
    -----------
    daily_results : list
        Liste mit den täglichen Analyseergebnissen
    output_path : str, optional
        Basispfad für die Ausgabedateien
    """
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import os
    import matplotlib.dates as mdates
    from config import CAPACITY_MWH

    # Daten extrahieren
    cycle_data = pd.DataFrame(
        [
            {
                "date": result["date"],
                "cycles": result.get("cycles_completed", 0),
                "initial_soc": result.get("initial_energy_level", 0)
                / CAPACITY_MWH
                * 100,
                "final_soc": result.get("final_energy_level", 0) / CAPACITY_MWH * 100,
            }
            for result in daily_results
            if result
        ]
    )

    cycle_data["date"] = pd.to_datetime(cycle_data["date"])
    cycle_data["month"] = cycle_data["date"].dt.month
    cycle_data["year"] = cycle_data["date"].dt.year
    cycle_data["cumulative_cycles"] = cycle_data["cycles"].cumsum()

    # Figure 1: Kumulierte Zyklen über die Zeit - ÜBERARBEITET
    fig, ax = plt.subplots(figsize=(12, 6))

    # Hauptplot: Kumulierte Zyklen mit dynamischem Y-Bereich
    ax.plot(cycle_data["date"], cycle_data["cumulative_cycles"], "b-", linewidth=2)

    # Y-Achse mit 10% Puffer nach oben
    max_cycles = cycle_data["cumulative_cycles"].max()
    y_max = max_cycles * 1.2  # 20% Puffer über dem Maximum
    ax.set_ylim(0, y_max)

    # X-Achse formatieren
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))  # Alle 3 Monate
    plt.xticks(rotation=45, ha="right")

    # Titel und Labels
    ax.set_title("Kumulierte Batteriezyklen", fontsize=14, fontweight="bold")
    ax.set_ylabel("Anzahl Zyklen", fontsize=12)
    ax.grid(True, alpha=0.3)

    # Lebensdauer-Referenzen als eingebetteter Graph
    # Kleiner Graph für die Lebenszeit-Prognose
    axins = plt.axes([0.15, 0.55, 0.35, 0.35])  # [left, bottom, width, height]

    # Vereinfachte Daten für den eingebetteten Graphen
    dates = [cycle_data["date"].iloc[0], cycle_data["date"].iloc[-1]]
    cycles = [0, cycle_data["cumulative_cycles"].iloc[-1]]

    # Projektionslinie
    cycle_life = 8000  # Angenommene Lebensdauer in Zyklen
    avg_daily_cycles = cycle_data["cycles"].mean()
    if avg_daily_cycles > 0:
        days_to_end = (
            cycle_life - cycle_data["cumulative_cycles"].iloc[-1]
        ) / avg_daily_cycles
        end_date = cycle_data["date"].iloc[-1] + pd.Timedelta(days=days_to_end)

        # Vollständige Projektion
        dates.append(end_date)
        cycles.append(cycle_life)

        # Projizierte Linie plotten
        axins.plot(dates, cycles, "b-", linewidth=1.5, alpha=0.5)
        axins.scatter(dates[-1], cycles[-1], color="red", marker="o")

        # Achsen formatieren
        axins.set_ylim(0, cycle_life * 1.1)
        axins.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        axins.xaxis.set_major_locator(mdates.YearLocator())

        # Titel
        axins.set_title("Projektion bis Lebensende", fontsize=10)

        # Legende für den Hauptgraphen
        end_date_str = end_date.strftime("%m/%Y")
        ax.annotate(
            f"Projiziertes Lebensende: {end_date_str}\n(bei {avg_daily_cycles:.2f} Zyklen/Tag)",
            xy=(0.02, 0.92),
            xycoords="axes fraction",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8),
            fontsize=10,
        )

    # Figure 2: Zyklen pro Monat - UNVERÄNDERT
    plt.figure(figsize=(12, 6))
    monthly_cycles = cycle_data.groupby(["year", "month"])["cycles"].sum().reset_index()
    monthly_cycles["year_month"] = monthly_cycles.apply(
        lambda x: f"{x['year']}-{x['month']:02d}", axis=1
    )

    bars = plt.bar(
        monthly_cycles["year_month"], monthly_cycles["cycles"], color="blue", alpha=0.7
    )

    # x-Achse formatieren
    plt.xticks(rotation=45, ha="right")
    if (
        len(monthly_cycles) > 12
    ):  # Wenn mehr als 12 Monate, nicht alle x-Labels anzeigen
        n = max(1, len(monthly_cycles) // 6)  # Alle n Monate anzeigen
        for i, tick in enumerate(plt.gca().xaxis.get_major_ticks()):
            if i % n != 0:
                tick.set_visible(False)

    plt.title("Batteriezyklen pro Monat", fontsize=14, fontweight="bold")
    plt.ylabel("Anzahl Zyklen", fontsize=12)
    plt.grid(True, alpha=0.3)

    avg_cycles = monthly_cycles["cycles"].mean()
    plt.axhline(
        y=avg_cycles,
        color="red",
        linestyle="--",
        label=f"Durchschnitt: {avg_cycles:.1f} Zyklen/Monat",
    )

    # Trendlinie hinzufügen
    if len(monthly_cycles) > 2:
        x = np.arange(len(monthly_cycles))
        z = np.polyfit(x, monthly_cycles["cycles"], 1)
        p = np.poly1d(z)
        plt.plot(
            monthly_cycles["year_month"],
            p(x),
            "k--",
            alpha=0.7,
            label=f"Trend: {z[0]:.2f} Zyklen/Monat",
        )

    plt.legend()

    if output_path:
        dir_path = os.path.dirname(output_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        plt.savefig(f"{dir_path}/monthly_cycles.png", dpi=300, bbox_inches="tight")

    plt.close("all")

    # Figure 3: State of Charge (SoC) Verteilung - UNVERÄNDERT
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Initial SoC Histogramm
    bins = np.linspace(0, 100, 21)  # 5%-Schritte
    ax1.hist(cycle_data["initial_soc"], bins=bins, color="blue", alpha=0.7)
    ax1.set_title(
        "Anfangs-Ladezustand (SoC) Verteilung", fontsize=12, fontweight="bold"
    )
    ax1.set_xlabel("State of Charge (%)", fontsize=10)
    ax1.set_ylabel("Häufigkeit", fontsize=10)
    ax1.grid(True, alpha=0.3)

    # Final SoC Histogramm
    ax2.hist(cycle_data["final_soc"], bins=bins, color="green", alpha=0.7)
    ax2.set_title("End-Ladezustand (SoC) Verteilung", fontsize=12, fontweight="bold")
    ax2.set_xlabel("State of Charge (%)", fontsize=10)
    ax2.set_ylabel("Häufigkeit", fontsize=10)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    if output_path:
        plt.savefig(f"{dir_path}/soc_distribution.png", dpi=300, bbox_inches="tight")

    plt.close("all")

    # Neues Diagramm 4: Tägliche Zyklen im Zeitverlauf
    plt.figure(figsize=(12, 6))

    # 7-Tage-Durchschnitt
    cycle_data["rolling_cycles"] = (
        cycle_data["cycles"].rolling(window=7, min_periods=1).mean()
    )

    plt.plot(
        cycle_data["date"],
        cycle_data["cycles"],
        "b-",
        alpha=0.3,
        label="Tägliche Zyklen",
    )
    plt.plot(
        cycle_data["date"],
        cycle_data["rolling_cycles"],
        "r-",
        linewidth=2,
        label="7-Tage-Durchschnitt",
    )

    plt.title("Tägliche Batteriezyklen", fontsize=14, fontweight="bold")
    plt.ylabel("Zyklen pro Tag", fontsize=12)
    plt.grid(True, alpha=0.3)

    # X-Achse formatieren
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.xticks(rotation=45, ha="right")

    # Durchschnitt anzeigen
    avg_daily = cycle_data["cycles"].mean()
    plt.axhline(
        y=avg_daily,
        color="green",
        linestyle="--",
        label=f"Gesamtdurchschnitt: {avg_daily:.2f} Zyklen/Tag",
    )

    plt.legend()

    if output_path:
        plt.savefig(f"{dir_path}/daily_cycles.png", dpi=300, bbox_inches="tight")

    plt.close("all")

    # Speichern des ersten Diagramms (kumulierte Zyklen)
    if output_path:
        plt.figure(fig.number)
        plt.savefig(f"{dir_path}/cumulative_cycles.png", dpi=300, bbox_inches="tight")
        plt.close("all")

    return {
        "total_cycles": cycle_data["cumulative_cycles"].iloc[-1],
        "avg_monthly_cycles": avg_cycles,
        "avg_daily_cycles": avg_daily,
        "projected_end_date": end_date if "end_date" in locals() else None,
        "avg_soc_initial": cycle_data["initial_soc"].mean(),
        "avg_soc_final": cycle_data["final_soc"].mean(),
    }


def plot_charge_discharge_patterns(daily_results, output_path=None):
    """
    Erstellt Visualisierungen zu Lade- und Entlademustern.
    Überarbeitete Version mit besserer Fehlerbehandlung und Verwendung der Netto-Energie.

    Parameters:
    -----------
    daily_results : list
        Liste mit den täglichen Analyseergebnissen
    output_path : str, optional
        Basispfad für die Ausgabedateien
    """
    import matplotlib.pyplot as plt
    import numpy as np
    import os
    import logging
    from datetime import datetime

    # Standard-Effizienz, falls nicht in den Transaktionsdaten verfügbar
    DEFAULT_EFFICIENCY = 0.95

    logger = logging.getLogger(__name__)
    logger.info("Erstelle Lade-/Entlademuster-Visualisierung...")

    # Sammle alle Transaktionen aus den täglichen Ergebnissen
    charge_data = []  # Ladedaten nach Stunde
    discharge_data = []  # Entladedaten nach Stunde
    monthly_charge = np.zeros(12)  # Ladedaten nach Monat
    monthly_discharge = np.zeros(12)  # Entladedaten nach Monat
    weekday_charge = np.zeros(7)  # Ladedaten nach Wochentag
    weekday_discharge = np.zeros(7)  # Entladedaten nach Wochentag

    # Für jedes Tagesergebnis
    for result in daily_results:
        if not result:
            continue

        # Datum extrahieren
        date_obj = None
        if "date" in result:
            try:
                if isinstance(result["date"], datetime):
                    date_obj = result["date"]
                else:
                    date_obj = datetime.strptime(str(result["date"]), "%Y-%m-%d")
            except:
                continue

        if not date_obj:
            continue

        # Wochentag und Monat extrahieren
        weekday = date_obj.weekday()  # 0-6
        month = date_obj.month - 1  # 0-11

        # Transaktionen verarbeiten
        if "transactions" in result and not result["transactions"].empty:
            transactions = result["transactions"]

            for _, trans in transactions.iterrows():
                if "type" not in trans:
                    continue

                # Zeitpunkt ermitteln
                hour = 0
                if "index" in trans:
                    hour = int(trans["index"]) // 4  # 15-Minuten-Intervalle zu Stunden

                # Nur Transaktionen mit interval==0 berücksichtigen (Beginn eines Vorgangs)
                if "interval" in trans and trans["interval"] == 0:
                    if trans["type"] == "charge":
                        # Ladedaten sammeln
                        amount = float(trans.get("amount", 0))
                        charge_data.append(hour)
                        monthly_charge[month] += amount
                        weekday_charge[weekday] += amount
                    elif trans["type"] == "discharge":
                        # Entladedaten sammeln - GEÄNDERT: Verwende amount_usable (Netto-Energie)
                        discharge_data.append(hour)
                        # Verwende amount_usable statt amount_gross für Netto-Energie
                        discharge_amount = float(
                            trans.get(
                                "amount_usable",
                                trans.get("amount", 0) * DEFAULT_EFFICIENCY,
                            )
                        )
                        monthly_discharge[month] += discharge_amount
                        weekday_discharge[weekday] += discharge_amount

    if not charge_data and not discharge_data:
        logger.warning("Keine Lade-/Entladedaten gefunden.")
        return {}

    logger.info(
        f"Daten gesammelt: {len(charge_data)} Ladevorgänge, {len(discharge_data)} Entladevorgänge"
    )

    # Monatsnamen und Wochentagsnamen
    months = [
        "Jan",
        "Feb",
        "Mär",
        "Apr",
        "Mai",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Okt",
        "Nov",
        "Dez",
    ]
    weekdays = [
        "Montag",
        "Dienstag",
        "Mittwoch",
        "Donnerstag",
        "Freitag",
        "Samstag",
        "Sonntag",
    ]

    # Figure 1: Tagesprofile für Laden/Entladen
    plt.figure(figsize=(12, 8))

    # Histogramme für Stunden erstellen
    hourly_charge = np.zeros(24)
    hourly_discharge = np.zeros(24)

    # Zähle die Häufigkeit jeder Stunde
    for hour in charge_data:
        if 0 <= hour < 24:  # Sicherstellen, dass Stunde im gültigen Bereich ist
            hourly_charge[hour] += 1

    for hour in discharge_data:
        if 0 <= hour < 24:  # Sicherstellen, dass Stunde im gültigen Bereich ist
            hourly_discharge[hour] += 1

    # Normalisieren für bessere Vergleichbarkeit
    if np.sum(hourly_charge) > 0:
        hourly_charge = hourly_charge / np.sum(hourly_charge) * 100

    if np.sum(hourly_discharge) > 0:
        hourly_discharge = hourly_discharge / np.sum(hourly_discharge) * 100

    # X-Achse (Stunden)
    hours = np.arange(24)

    # Plotten mit nebeneinanderstehenden Balken
    plt.bar(
        hours - 0.2, hourly_charge, width=0.4, color="green", alpha=0.7, label="Laden"
    )
    plt.bar(
        hours + 0.2,
        hourly_discharge,
        width=0.4,
        color="red",
        alpha=0.7,
        label="Entladen",
    )

    plt.title(
        "Tagesprofile für Lade- und Entladevorgänge", fontsize=14, fontweight="bold"
    )
    plt.xlabel("Stunde des Tages", fontsize=12)
    plt.ylabel("Anteil am Gesamtvolumen (%)", fontsize=12)
    plt.xticks(hours)
    plt.grid(True, alpha=0.3)
    plt.legend()

    if output_path:
        dir_path = os.path.dirname(output_path)
        os.makedirs(dir_path, exist_ok=True)
        plt.savefig(
            f"{dir_path}/daily_charge_discharge_profile.png",
            dpi=300,
            bbox_inches="tight",
        )

    plt.close()

    # Figure 2: Monatliche Verteilung der Energie
    plt.figure(figsize=(12, 6))

    # X-Achse für Monate
    month_indices = np.arange(12)

    # Plotten mit nebeneinanderstehenden Balken
    width = 0.35
    plt.bar(
        month_indices - width / 2,
        monthly_charge,
        width,
        label="Geladen (MWh)",
        color="green",
        alpha=0.7,
    )
    plt.bar(
        month_indices + width / 2,
        monthly_discharge,
        width,
        label="Entladen (MWh)",
        color="red",
        alpha=0.7,
    )

    # Titel mit klarer Angabe der Daten
    plt.title("Monatliche Energie-Verteilung (Netto)", fontsize=14, fontweight="bold")
    plt.xlabel("Monat", fontsize=12)
    plt.ylabel("Energie (MWh)", fontsize=12)
    plt.xticks(month_indices, months)
    plt.grid(True, alpha=0.3)
    plt.legend()

    if output_path:
        plt.savefig(
            f"{dir_path}/monthly_energy_distribution.png", dpi=300, bbox_inches="tight"
        )

    plt.close()

    # Figure 3: Durchschnittliche Aktivität pro Wochentag
    plt.figure(figsize=(12, 6))

    # X-Achse für Wochentage
    weekday_indices = np.arange(7)

    # Plotten mit nebeneinanderstehenden Balken
    plt.bar(
        weekday_indices - width / 2,
        weekday_charge,
        width,
        label="Geladen (MWh)",
        color="green",
        alpha=0.7,
    )
    plt.bar(
        weekday_indices + width / 2,
        weekday_discharge,
        width,
        label="Entladen (MWh)",
        color="red",
        alpha=0.7,
    )

    plt.title("Aktivität nach Wochentag (Netto)", fontsize=14, fontweight="bold")
    plt.xlabel("Wochentag", fontsize=12)
    plt.ylabel("Energie (MWh)", fontsize=12)
    plt.xticks(weekday_indices, weekdays)
    plt.grid(True, alpha=0.3)
    plt.legend()

    if output_path:
        plt.savefig(f"{dir_path}/weekday_activity.png", dpi=300, bbox_inches="tight")

    plt.close()

    return {
        "total_charged": np.sum(monthly_charge),
        "total_discharged": np.sum(monthly_discharge),
        "peak_charge_hour": (
            np.argmax(hourly_charge) if np.sum(hourly_charge) > 0 else None
        ),
        "peak_discharge_hour": (
            np.argmax(hourly_discharge) if np.sum(hourly_discharge) > 0 else None
        ),
    }


def plot_efficiency_analysis(daily_results, output_path=None):
    """
    Erstellt Visualisierungen zur Effizienz der Batteriespeichernutzung.

    Parameters:
    -----------
    daily_results : list
        Liste mit den täglichen Analyseergebnissen
    output_path : str, optional
        Basispfad für die Ausgabedateien
    """
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np
    import os
    import matplotlib.dates as mdates
    from config import CAPACITY_MWH, EFFICIENCY

    # Daten extrahieren mit relevanten Metriken
    efficiency_data = pd.DataFrame(
        [
            {
                "date": result["date"],
                "profit": result.get("profit", 0),
                "total_charged": result.get("total_charged", 0),
                "total_gross_energy": result.get("total_gross_energy", 0),
                "total_usable_energy": result.get("total_usable_energy", 0),
                "total_energy_loss": result.get("total_energy_loss", 0),
                "efficiency_losses": result.get("efficiency_losses", 0),
                "charge_count": result.get("charge_count", 0),
                "discharge_count": result.get("discharge_count", 0),
                "cycles": result.get(
                    "cycles_completed", 0
                ),  # Bereits vorhandene Zykleninformation verwenden
                "initial_energy_level": result.get("initial_energy_level", 0),
                "final_energy_level": result.get("final_energy_level", 0),
            }
            for result in daily_results
            if result
        ]
    )

    efficiency_data["date"] = pd.to_datetime(efficiency_data["date"])
    efficiency_data["month"] = efficiency_data["date"].dt.month
    efficiency_data["year"] = efficiency_data["date"].dt.year

    # Figure 1: Kapazitätsnutzung (unverändert)
    plt.figure(figsize=(12, 6))

    # Tägliche Kapazitätsnutzung berechnen (Prozent der Gesamtkapazität, die umgesetzt wurde)
    efficiency_data["capacity_utilization"] = (
        efficiency_data["total_charged"] / CAPACITY_MWH * 100
    )

    # 7-Tage rollierender Durchschnitt
    efficiency_data["rolling_utilization"] = (
        efficiency_data["capacity_utilization"].rolling(window=7, min_periods=1).mean()
    )

    plt.plot(
        efficiency_data["date"],
        efficiency_data["capacity_utilization"],
        "b-",
        alpha=0.3,
        label="Tägliche Kapazitätsnutzung",
    )
    plt.plot(
        efficiency_data["date"],
        efficiency_data["rolling_utilization"],
        "r-",
        linewidth=2,
        label="7-Tage Durchschnitt",
    )

    # Durchschnittliche Kapazitätsnutzung
    avg_utilization = efficiency_data["capacity_utilization"].mean()
    plt.axhline(
        y=avg_utilization,
        color="green",
        linestyle="--",
        label=f"Durchschnitt: {avg_utilization:.1f}%",
    )

    plt.title(
        "Batteriekapazitätsnutzung im Zeitverlauf", fontsize=14, fontweight="bold"
    )
    plt.ylabel("Kapazitätsnutzung (%)", fontsize=12)
    plt.ylim(0, min(max(efficiency_data["capacity_utilization"].max() * 1.2, 100), 200))
    plt.grid(True, alpha=0.3)
    plt.legend()

    # X-Achse formatieren
    format_xaxis_with_short_german_months()

    if output_path:
        dir_path = os.path.dirname(output_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        plt.savefig(
            f"{dir_path}/capacity_utilization.png", dpi=300, bbox_inches="tight"
        )

    plt.close("all")

    # Figure 2: Wirtschaftliche Effizienz (unverändert)
    plt.figure(figsize=(12, 6))

    # Gewinn pro geladener MWh berechnen
    efficiency_data["profit_per_mwh"] = 0.0  # Standardwert
    valid_data = efficiency_data[
        efficiency_data["total_charged"] > 0.001
    ].copy()  # Explizite Kopie erstellen!
    if not valid_data.empty:
        valid_data["profit_per_mwh"] = (
            valid_data["profit"] / valid_data["total_charged"]
        )
        valid_data["rolling_profit_per_mwh"] = (
            valid_data["profit_per_mwh"].rolling(window=7, min_periods=1).mean()
        )

        plt.plot(
            valid_data["date"],
            valid_data["profit_per_mwh"],
            "b-",
            alpha=0.3,
            label="Täglicher Gewinn/MWh",
        )
        plt.plot(
            valid_data["date"],
            valid_data["rolling_profit_per_mwh"],
            "r-",
            linewidth=2,
            label="7-Tage Durchschnitt",
        )

        # Durchschnittliche Wirtschaftliche Effizienz
        avg_profit_per_mwh = valid_data["profit_per_mwh"].mean()
        plt.axhline(
            y=avg_profit_per_mwh,
            color="green",
            linestyle="--",
            label=f"Durchschnitt: {avg_profit_per_mwh:.2f} €/MWh",
        )

    plt.title(
        "Wirtschaftliche Effizienz im Zeitverlauf", fontsize=14, fontweight="bold"
    )
    plt.ylabel("Gewinn pro geladener MWh (€/MWh)", fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend()

    # X-Achse formatieren
    format_xaxis_with_short_german_months()

    if output_path:
        plt.savefig(f"{dir_path}/economic_efficiency.png", dpi=300, bbox_inches="tight")

    plt.close("all")

    # Figure 3: Batteriezyklen pro Tag (KORRIGIERT)
    plt.figure(figsize=(12, 6))

    # 7-Tage rollierender Durchschnitt für Batteriezyklen
    efficiency_data["rolling_cycles"] = (
        efficiency_data["cycles"].rolling(window=7, min_periods=1).mean()
    )

    plt.plot(
        efficiency_data["date"],
        efficiency_data["cycles"],
        "b-",
        alpha=0.3,
        label="Batteriezyklen pro Tag",
    )
    plt.plot(
        efficiency_data["date"],
        efficiency_data["rolling_cycles"],
        "r-",
        linewidth=2,
        label="7-Tage Durchschnitt",
    )

    # Durchschnittliche Anzahl Zyklen
    avg_cycles = efficiency_data["cycles"].mean()
    plt.axhline(
        y=avg_cycles,
        color="green",
        linestyle="--",
        label=f"Durchschnitt: {avg_cycles:.2f} Zyklen/Tag",
    )

    plt.title("Batteriezyklen im Zeitverlauf", fontsize=14, fontweight="bold")
    plt.ylabel("Anzahl Batteriezyklen", fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend()

    # X-Achse formatieren
    format_xaxis_with_short_german_months()

    if output_path:
        plt.savefig(f"{dir_path}/battery_cycles.png", dpi=300, bbox_inches="tight")

    plt.close("all")

    # Figure 4: Ladezustand (SoC) im Zeitverlauf (unverändert)
    plt.figure(figsize=(12, 6))

    # Berechnung des täglichen durchschnittlichen Ladezustands
    efficiency_data["initial_soc"] = (
        efficiency_data["initial_energy_level"] / CAPACITY_MWH * 100
    )
    efficiency_data["final_soc"] = (
        efficiency_data["final_energy_level"] / CAPACITY_MWH * 100
    )
    efficiency_data["avg_daily_soc"] = (
        efficiency_data["initial_soc"] + efficiency_data["final_soc"]
    ) / 2

    # 7-Tage rollierender Durchschnitt
    efficiency_data["rolling_soc"] = (
        efficiency_data["avg_daily_soc"].rolling(window=7, min_periods=1).mean()
    )

    # Plotten der Daten
    plt.plot(
        efficiency_data["date"],
        efficiency_data["avg_daily_soc"],
        "b-",
        alpha=0.3,
        label="Täglicher Ø-Ladezustand",
    )
    plt.plot(
        efficiency_data["date"],
        efficiency_data["rolling_soc"],
        "r-",
        linewidth=2,
        label="7-Tage Durchschnitt",
    )

    # Gesamtdurchschnitt anzeigen
    avg_total_soc = efficiency_data["avg_daily_soc"].mean()
    plt.axhline(
        y=avg_total_soc,
        color="green",
        linestyle="--",
        label=f"Gesamtdurchschnitt: {avg_total_soc:.1f}%",
    )

    # Achsenformatierung und Titel
    plt.title("Ladezustand (SoC) im Zeitverlauf", fontsize=14, fontweight="bold")
    plt.ylabel("Durchschnittlicher Ladezustand (%)", fontsize=12)
    plt.ylim(0, 100)  # 0-100% SoC
    plt.grid(True, alpha=0.3)
    plt.legend()

    # X-Achse formatieren
    format_xaxis_with_short_german_months()

    if output_path:
        plt.savefig(f"{dir_path}/battery_soc.png", dpi=300, bbox_inches="tight")

    plt.close("all")

    # Rückgabe der wichtigsten Kennzahlen
    return {
        "avg_capacity_utilization": avg_utilization,
        "avg_profit_per_mwh": (
            avg_profit_per_mwh if "avg_profit_per_mwh" in locals() else None
        ),
        "avg_cycles_per_day": avg_cycles,  # KORRIGIERT: cycles statt trades
        "avg_soc": avg_total_soc,
    }


def plot_price_arbitrage_analysis(daily_results, output_path=None):
    """
    Erstellt Visualisierungen zur Preis-Arbitrage und Handelserfolg.

    Parameters:
    -----------
    daily_results : list
        Liste mit den täglichen Analyseergebnissen
    output_path : str, optional
        Basispfad für die Ausgabedateien
    """
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np
    import os
    import matplotlib.dates as mdates

    # Alle Transaktionen sammeln
    all_transactions = []
    all_prices = []

    for result in daily_results:
        if result and "transactions" in result and not result["transactions"].empty:
            transactions = result["transactions"].copy()
            transactions["date"] = result["date"]
            all_transactions.append(transactions)

        # Für jeden Tag auch die Preisdaten speichern, falls vorhanden
        if "prices_df" in result and "price" in result["prices_df"].columns:
            prices = result["prices_df"][["datetime", "price"]].copy()
            all_prices.append(prices)

    if not all_transactions:
        print("Keine Transaktionen für Preisanalyse gefunden.")
        return {}

    transactions_df = pd.concat(all_transactions, ignore_index=True)

    # Figure 1: Kauf- und Verkaufspreise
    plt.figure(figsize=(12, 6))

    # Preisdaten für Laden und Entladen extrahieren
    charge_prices = transactions_df[transactions_df["type"] == "charge"]["price"]
    discharge_prices = transactions_df[transactions_df["type"] == "discharge"]["price"]

    # Gemeinsame Grenzen für beide Histogramme festlegen
    min_price = min(charge_prices.min(), discharge_prices.min())
    max_price = max(charge_prices.max(), discharge_prices.max())

    # Bins für Histogramm
    bins = np.linspace(min_price, max_price, 30)

    # Histogramme zeichnen
    plt.hist(charge_prices, bins=bins, alpha=0.5, label="Kauf (Laden)", color="green")
    plt.hist(
        discharge_prices, bins=bins, alpha=0.5, label="Verkauf (Entladen)", color="red"
    )

    plt.title("Verteilung der Handelspreise", fontsize=14, fontweight="bold")
    plt.xlabel("Preis (€/MWh)", fontsize=12)
    plt.ylabel("Häufigkeit", fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend()

    # Durchschnittliche Preise anzeigen
    avg_buy = charge_prices.mean()
    avg_sell = discharge_prices.mean()
    plt.axvline(
        x=avg_buy,
        color="green",
        linestyle="--",
        label=f"Ø Kaufpreis: {avg_buy:.2f} €/MWh",
    )
    plt.axvline(
        x=avg_sell,
        color="red",
        linestyle="--",
        label=f"Ø Verkaufspreis: {avg_sell:.2f} €/MWh",
    )

    # Durchschnittliche Handelsmarge
    margin = avg_sell - avg_buy
    plt.figtext(
        0.02,
        0.02,
        f"Durchschnittliche Handelsmarge: {margin:.2f} €/MWh ({margin/avg_buy*100:.1f}%)",
        fontsize=10,
        bbox=dict(
            facecolor="white", alpha=0.8, edgecolor="gray", boxstyle="round,pad=0.5"
        ),
    )

    plt.legend()

    if output_path:
        dir_path = os.path.dirname(output_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        plt.savefig(f"{dir_path}/price_distribution.png", dpi=300, bbox_inches="tight")

    plt.close("all")

    # Figure 2: Profitabilität pro Zyklus
    plt.figure(figsize=(12, 6))

    # Daten für jeden Tag extrahieren
    cycle_profit_data = pd.DataFrame(
        [
            {
                "date": result["date"],
                "profit": result.get("profit", 0),
                "cycles": result.get("cycles_completed", 0),
            }
            for result in daily_results
            if result and result.get("cycles_completed", 0) > 0
        ]
    )

    if not cycle_profit_data.empty:
        cycle_profit_data["date"] = pd.to_datetime(cycle_profit_data["date"])
        cycle_profit_data["profit_per_cycle"] = (
            cycle_profit_data["profit"] / cycle_profit_data["cycles"]
        )

        # 7-Tage-Durchschnitt
        cycle_profit_data["rolling_profit_per_cycle"] = (
            cycle_profit_data["profit_per_cycle"]
            .rolling(window=7, min_periods=1)
            .mean()
        )

        # Profit pro Zyklus im Zeitverlauf
        plt.plot(
            cycle_profit_data["date"],
            cycle_profit_data["profit_per_cycle"],
            "b-",
            alpha=0.3,
            label="Täglicher Profit/Zyklus",
        )
        plt.plot(
            cycle_profit_data["date"],
            cycle_profit_data["rolling_profit_per_cycle"],
            "r-",
            linewidth=2,
            label="7-Tage-Durchschnitt",
        )

        # X-Achse nur mit Monaten formatieren
        plt.gca().xaxis.set_major_formatter(
            mdates.DateFormatter("%b")
        )  # %b = abgekürzter Monatsname
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
        plt.xticks(rotation=0)  # Keine Rotation für bessere Lesbarkeit

        plt.title("Profit pro Batteriezyklus", fontsize=14, fontweight="bold")
        plt.ylabel("Profit pro Zyklus (€)", fontsize=12)
        plt.grid(True, alpha=0.3)

        # Durchschnitt für den gesamten Zeitraum
        avg_profit_per_cycle = cycle_profit_data["profit_per_cycle"].mean()
        plt.axhline(
            y=avg_profit_per_cycle,
            color="green",
            linestyle="--",
            label=f"Gesamtdurchschnitt: {avg_profit_per_cycle:.2f} €/Zyklus",
        )

        plt.legend()

        if output_path:
            plt.savefig(
                f"{dir_path}/profit_per_cycle.png", dpi=300, bbox_inches="tight"
            )

        plt.close("all")

    # Figure 3: Gewinnverteilung nach Tageszeit
    plt.figure(figsize=(12, 6))

    # Tägliche Gewinnverteilung nach Tageszeit
    if "index" in transactions_df.columns:
        # Stunde des Tages aus Index extrahieren
        transactions_df["hour"] = (
            transactions_df["index"] // 4
        )  # 15-min Intervalle zu Stunden

    # Profit pro Stunde berechnen
    hourly_profit = pd.DataFrame()
    for hour in range(24):
        # Lade-Transaktionen in dieser Stunde
        hour_charges = transactions_df[
            (transactions_df["type"] == "charge") & (transactions_df["hour"] == hour)
        ]
        # Entlade-Transaktionen in dieser Stunde
        hour_discharges = transactions_df[
            (transactions_df["type"] == "discharge") & (transactions_df["hour"] == hour)
        ]

        # Gewinn/Verlust für diese Stunde
        charge_costs = (
            hour_charges["cost"].sum() if "cost" in hour_charges.columns else 0
        )
        discharge_revenues = (
            hour_discharges["revenue"].sum()
            if "revenue" in hour_discharges.columns
            else 0
        )

        # Stundendaten hinzufügen
        hourly_profit = pd.concat(
            [
                hourly_profit,
                pd.DataFrame(
                    {"hour": [hour], "profit": [discharge_revenues - charge_costs]}
                ),
            ]
        )

    # Farbige Balken je nach Wert
    colors = ["green" if x >= 0 else "red" for x in hourly_profit["profit"]]
    plt.bar(hourly_profit["hour"], hourly_profit["profit"], color=colors, alpha=0.7)

    # Nulllinie deutlicher machen
    plt.axhline(y=0, color="black", linestyle="-", linewidth=1.5, alpha=0.7)

    # Durchschnittslinie hinzufügen
    avg_profit = hourly_profit["profit"].mean()
    plt.axhline(
        y=avg_profit, color="blue", linestyle="--", label=f"Ø Gewinn: {avg_profit:.0f}€"
    )

    # Beschriftungen und Layout
    plt.title("Gewinnverteilung nach Tageszeit", fontsize=14, fontweight="bold")
    plt.xlabel("Stunden des Tages", fontsize=12)
    plt.ylabel("Gewinn (€)", fontsize=12)
    plt.xticks(range(1, 24, 1))
    plt.grid(True, alpha=0.3)
    plt.legend()

    if output_path:
        dir_path = os.path.dirname(output_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        plt.savefig(
            f"{dir_path}/hourly_profit_distribution.png", dpi=300, bbox_inches="tight"
        )

    plt.close("all")

    return {
        "avg_buy_price": avg_buy,
        "avg_sell_price": avg_sell,
        "avg_margin": margin,
        "avg_profit_per_cycle": (
            avg_profit_per_cycle if "avg_profit_per_cycle" in locals() else None
        ),
    }


def plot_lcoe_comparison(economic_results, market_prices_df, output_path=None):
    """
    Erstellt einen LCOE (Levelized Cost of Energy) Vergleich.
    Zeigt die Wirtschaftlichkeit im Vergleich zu Marktpreisen.
    """
    import matplotlib.pyplot as plt
    import numpy as np
    import os

    # LCOE berechnen
    capex = economic_results["capex"]["total_capex"]
    opex_annual = economic_results["opex"]["total_opex"]
    years = len(economic_results["simulation"]["annual_revenues"])
    discount_rate = 0.06

    # Gesamte diskontierte Kosten
    total_discounted_costs = capex
    for year in range(1, years + 1):
        total_discounted_costs += opex_annual / ((1 + discount_rate) ** year)

    # Gesamte diskontierte Energieproduktion
    annual_energy = (
        economic_results["simulation"]["annual_revenues"][0]
        / market_prices_df["price"].mean()
    )
    total_discounted_energy = 0
    for year in range(1, years + 1):
        total_discounted_energy += annual_energy / ((1 + discount_rate) ** year)

    lcoe = (
        total_discounted_costs / total_discounted_energy
        if total_discounted_energy > 0
        else 0
    )

    # Visualisierung
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Links: LCOE-Komponenten
    components = {
        "CAPEX": capex / total_discounted_energy,
        "OPEX": (total_discounted_costs - capex) / total_discounted_energy,
        "Gesamt LCOE": lcoe,
    }

    bars = ax1.bar(
        components.keys(), components.values(), color=["#D62728", "#FF9896", "#1F77B4"]
    )

    # Marktpreis-Referenzen
    avg_market_price = market_prices_df["price"].mean()
    ax1.axhline(
        y=avg_market_price,
        color="green",
        linestyle="--",
        label=f"Ø Marktpreis: {avg_market_price:.2f} €/MWh",
    )

    ax1.set_ylabel("€/MWh", fontsize=12)
    ax1.set_title("LCOE-Analyse", fontsize=14, fontweight="bold")
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis="y")

    # Werte auf Balken
    for bar, (name, value) in zip(bars, components.items()):
        height = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 1,
            f"{value:.1f}",
            ha="center",
            va="bottom",
            fontweight="bold",
        )

    # Rechts: Rentabilitätsschwellen
    price_range = np.linspace(20, 200, 50)
    years_to_breakeven = []

    for price in price_range:
        annual_revenue = annual_energy * price
        annual_profit = annual_revenue - opex_annual

        if annual_profit <= 0:
            years_to_breakeven.append(np.inf)
        else:
            # Einfache Berechnung ohne Diskontierung
            years_to_breakeven.append(capex / annual_profit)

    ax2.plot(price_range, years_to_breakeven, linewidth=2)
    ax2.axhline(y=10, color="red", linestyle="--", alpha=0.6, label="10-Jahres-Ziel")
    ax2.axvline(
        x=avg_market_price, color="green", linestyle="--", label=f"Ø Marktpreis"
    )

    ax2.set_xlabel("Durchschnittlicher Strompreis (€/MWh)", fontsize=12)
    ax2.set_ylabel("Jahre bis Break-Even", fontsize=12)
    ax2.set_title("Break-Even-Analyse nach Strompreis", fontsize=14, fontweight="bold")
    ax2.set_ylim(0, 30)
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(
            f"{os.path.splitext(output_path)[0]}_lcoe_analysis.png",
            dpi=300,
            bbox_inches="tight",
        )
    plt.close()

    return {"lcoe": lcoe, "market_price": avg_market_price}


def plot_investment_metrics_dashboard(economic_results, output_path=None):
    """
    Erstellt ein Dashboard mit den wichtigsten Investitionskennzahlen.
    """
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    import numpy as np
    import os

    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 3, height_ratios=[1, 2, 2], width_ratios=[1, 1, 1])

    # Farben
    colors = {
        "good": "#2CA02C",
        "neutral": "#FF7F0E",
        "bad": "#D62728",
        "info": "#1F77B4",
    }

    # Daten extrahieren
    capex = economic_results["capex"]["total_capex"]
    npv = economic_results["npv"]["npv"]
    annual_revenues = economic_results["simulation"]["annual_revenues"]
    years = len(annual_revenues)

    # ROI berechnen
    total_profit = sum(annual_revenues) - economic_results["opex"]["total_opex"] * years
    roi = (total_profit / capex) * 100

    # Payback Period (vereinfacht)
    cumulative_profit = 0
    payback_period = None
    for year, revenue in enumerate(annual_revenues):
        cumulative_profit += revenue - economic_results["opex"]["total_opex"]
        if cumulative_profit >= capex:
            payback_period = year + 1
            break

    # KPI-Boxen (obere Reihe)
    kpi_data = [
        {
            "label": "NPV",
            "value": f"{npv:,.0f} €",
            "color": colors["good"] if npv > 0 else colors["bad"],
        },
        {
            "label": "ROI",
            "value": f"{roi:.1f}%",
            "color": (
                colors["good"]
                if roi > 15
                else colors["neutral"] if roi > 0 else colors["bad"]
            ),
        },
        {
            "label": "Payback",
            "value": f"{payback_period} Jahre" if payback_period else "> 10 Jahre",
            "color": (
                colors["good"]
                if payback_period and payback_period < 7
                else (
                    colors["neutral"]
                    if payback_period and payback_period < 10
                    else colors["bad"]
                )
            ),
        },
    ]

    for i, kpi in enumerate(kpi_data):
        ax = fig.add_subplot(gs[0, i])
        ax.text(
            0.5,
            0.7,
            kpi["value"],
            ha="center",
            va="center",
            fontsize=24,
            fontweight="bold",
            color=kpi["color"],
        )
        ax.text(
            0.5, 0.3, kpi["label"], ha="center", va="center", fontsize=14, color="gray"
        )

        # Box um KPI
        rect = patches.FancyBboxPatch(
            (0.1, 0.1),
            0.8,
            0.8,
            boxstyle="round,pad=0.1",
            facecolor="white",
            edgecolor=kpi["color"],
            linewidth=2,
        )
        ax.add_patch(rect)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

    # Mittlere Reihe: Kostenstruktur und Einnahmenentwicklung
    # Links: Kostenstruktur (Pie Chart)
    ax1 = fig.add_subplot(gs[1, 0])
    cost_components = {
        "Batterie": economic_results["capex"]["battery_cost"],
        "Wechselrichter": economic_results["capex"]["inverter_cost"],
        "Installation": economic_results["capex"]["additional_costs"],
        f"OPEX ({years}J)": economic_results["opex"]["total_opex"] * years,
    }

    wedges, texts, autotexts = ax1.pie(
        cost_components.values(),
        labels=cost_components.keys(),
        autopct="%1.1f%%",
        colors=["#1F77B4", "#FF7F0E", "#2CA02C", "#D62728"],
    )
    ax1.set_title("Kostenstruktur", fontsize=14, fontweight="bold")

    # Mitte: Einnahmenentwicklung
    ax2 = fig.add_subplot(gs[1, 1:])
    years_array = np.arange(1, years + 1)
    ax2.bar(years_array, annual_revenues, color=colors["info"], alpha=0.7)

    # Trendlinie
    z = np.polyfit(years_array, annual_revenues, 1)
    p = np.poly1d(z)
    ax2.plot(
        years_array,
        p(years_array),
        "r--",
        linewidth=2,
        label=f"Trend: {z[0]:.0f} €/Jahr",
    )

    ax2.set_xlabel("Betriebsjahr")
    ax2.set_ylabel("Jahreseinnahmen (€)")
    ax2.set_title("Einnahmenentwicklung", fontsize=14, fontweight="bold")
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis="y")

    # Untere Reihe: Szenarioanalyse
    ax3 = fig.add_subplot(gs[2, :])

    # Verschiedene Szenarien
    scenarios = {
        "Pessimistisch": {"revenue_factor": 0.7, "opex_factor": 1.2},
        "Basis": {"revenue_factor": 1.0, "opex_factor": 1.0},
        "Optimistisch": {"revenue_factor": 1.3, "opex_factor": 0.8},
    }

    scenario_results = {}
    for name, factors in scenarios.items():
        scenario_cashflows = [-capex]
        for year in range(years):
            revenue = (
                annual_revenues[year % len(annual_revenues)] * factors["revenue_factor"]
            )
            opex = economic_results["opex"]["total_opex"] * factors["opex_factor"]
            scenario_cashflows.append(revenue - opex)

        cumulative = np.cumsum(scenario_cashflows)
        scenario_results[name] = cumulative

        linestyle = "-" if name == "Basis" else "--"
        linewidth = 3 if name == "Basis" else 2
        ax3.plot(
            range(len(cumulative)),
            cumulative,
            label=name,
            linestyle=linestyle,
            linewidth=linewidth,
        )

    ax3.axhline(y=0, color="black", linestyle="-", alpha=0.5)
    ax3.set_xlabel("Projektjahr")
    ax3.set_ylabel("Kumulativer Cash-Flow (€)")
    ax3.set_title("Szenarioanalyse", fontsize=14, fontweight="bold")
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Haupttitel
    fig.suptitle(
        "Investment Dashboard - Batteriespeicher", fontsize=18, fontweight="bold"
    )

    plt.tight_layout()

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(
            f"{os.path.splitext(output_path)[0]}_investment_dashboard.png",
            dpi=300,
            bbox_inches="tight",
        )
    plt.close()

    return {"npv": npv, "roi": roi, "payback_period": payback_period}


def plot_risk_analysis(economic_results, output_path=None):
    """
    Erstellt eine Risikoanalyse mit Monte-Carlo-Simulation.
    """
    import matplotlib.pyplot as plt
    import numpy as np
    import os
    from scipy import stats

    np.random.seed(42)  # Für Reproduzierbarkeit

    # Parameter für Monte-Carlo
    n_simulations = 1000

    # Basis-Werte
    base_capex = economic_results["capex"]["total_capex"]
    base_revenue = np.mean(economic_results["simulation"]["annual_revenues"])
    base_opex = economic_results["opex"]["total_opex"]
    years = 10
    discount_rate = 0.06

    # Unsicherheitsbereiche (Standardabweichungen)
    capex_std = base_capex * 0.15  # 15% Unsicherheit
    revenue_std = base_revenue * 0.25  # 25% Unsicherheit
    opex_std = base_opex * 0.10  # 10% Unsicherheit

    # Monte-Carlo-Simulation
    npv_results = []

    for _ in range(n_simulations):
        # Zufällige Werte generieren
        sim_capex = np.random.normal(base_capex, capex_std)
        sim_revenues = np.random.normal(base_revenue, revenue_std, years)
        sim_opex = np.random.normal(base_opex, opex_std)

        # NPV berechnen
        cash_flows = [-sim_capex]
        for year in range(years):
            cf = (sim_revenues[year] - sim_opex) / ((1 + discount_rate) ** (year + 1))
            cash_flows.append(cf)

        npv = sum(cash_flows)
        npv_results.append(npv)

    npv_results = np.array(npv_results)

    # Visualisierung
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))

    # 1. NPV-Verteilung
    ax1.hist(npv_results, bins=50, density=True, alpha=0.7, color="#1F77B4")

    # Normalverteilung overlay
    mu, std = stats.norm.fit(npv_results)
    xmin, xmax = ax1.get_xlim()
    x = np.linspace(xmin, xmax, 100)
    p = stats.norm.pdf(x, mu, std)
    ax1.plot(x, p, "r-", linewidth=2, label="Normalverteilung")

    # Vertikale Linien für Perzentile
    percentiles = [5, 50, 95]
    colors_p = ["red", "green", "red"]
    for perc, color in zip(percentiles, colors_p):
        value = np.percentile(npv_results, perc)
        ax1.axvline(
            value,
            color=color,
            linestyle="--",
            alpha=0.7,
            label=f"{perc}. Perzentil: {value:,.0f} €",
        )

    ax1.set_xlabel("NPV (€)")
    ax1.set_ylabel("Wahrscheinlichkeitsdichte")
    ax1.set_title("NPV-Wahrscheinlichkeitsverteilung", fontsize=14, fontweight="bold")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 2. Risikoprofil
    prob_loss = (npv_results < 0).sum() / n_simulations * 100
    prob_low_return = (npv_results < base_capex * 0.1).sum() / n_simulations * 100
    prob_high_return = (npv_results > base_capex * 0.5).sum() / n_simulations * 100

    risk_categories = [
        "Verlust\n(NPV < 0)",
        "Niedrige Rendite\n(NPV < 10% CAPEX)",
        "Hohe Rendite\n(NPV > 50% CAPEX)",
    ]
    risk_probs = [prob_loss, prob_low_return, prob_high_return]
    colors_risk = ["#D62728", "#FF7F0E", "#2CA02C"]

    bars = ax2.bar(risk_categories, risk_probs, color=colors_risk, alpha=0.7)

    # Werte auf Balken
    for bar, prob in zip(bars, risk_probs):
        height = bar.get_height()
        ax2.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 1,
            f"{prob:.1f}%",
            ha="center",
            va="bottom",
            fontweight="bold",
        )

    ax2.set_ylabel("Wahrscheinlichkeit (%)")
    ax2.set_title("Risikoprofil", fontsize=14, fontweight="bold")
    ax2.set_ylim(0, 100)
    ax2.grid(True, alpha=0.3, axis="y")

    # 3. Sensitivität der Eingangsparameter
    ax3.set_title("Einfluss der Unsicherheiten auf NPV", fontsize=14, fontweight="bold")

    # Korrelationen berechnen
    correlations = {}

    # Revenue-Sensitivität
    revenue_variations = np.random.normal(1, 0.25, n_simulations)
    revenue_npvs = []
    for var in revenue_variations:
        cf = [-base_capex]
        for year in range(years):
            annual_cf = (base_revenue * var - base_opex) / (
                (1 + discount_rate) ** (year + 1)
            )
            cf.append(annual_cf)
        revenue_npvs.append(sum(cf))

    ax3.scatter(revenue_variations, revenue_npvs, alpha=0.5, s=10, label="Einnahmen")

    # CAPEX-Sensitivität
    capex_variations = np.random.normal(1, 0.15, n_simulations)
    capex_npvs = []
    for var in capex_variations:
        cf = [-base_capex * var]
        for year in range(years):
            annual_cf = (base_revenue - base_opex) / ((1 + discount_rate) ** (year + 1))
            cf.append(annual_cf)
        capex_npvs.append(sum(cf))

    ax3.scatter(capex_variations, capex_npvs, alpha=0.5, s=10, label="CAPEX")

    ax3.set_xlabel("Parametervariation (Faktor)")
    ax3.set_ylabel("NPV (€)")
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # 4. Value at Risk (VaR)
    confidence_levels = [90, 95, 99]
    var_values = []

    for conf in confidence_levels:
        var = np.percentile(npv_results, 100 - conf)
        var_values.append(var)

    ax4.bar(
        [f"{cl}%" for cl in confidence_levels], var_values, color="#D62728", alpha=0.7
    )

    ax4.set_ylabel("Value at Risk (€)")
    ax4.set_title(
        "Value at Risk bei verschiedenen Konfidenzniveaus",
        fontsize=14,
        fontweight="bold",
    )
    ax4.grid(True, alpha=0.3, axis="y")

    # Werte auf Balken
    for i, (conf, var) in enumerate(zip(confidence_levels, var_values)):
        ax4.text(
            i,
            var - abs(var) * 0.05,
            f"{var:,.0f} €",
            ha="center",
            va="top",
            fontweight="bold",
            color="white",
        )

    plt.suptitle(
        "Risikoanalyse - Monte-Carlo-Simulation", fontsize=16, fontweight="bold"
    )
    plt.tight_layout()

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(
            f"{os.path.splitext(output_path)[0]}_risk_analysis.png",
            dpi=300,
            bbox_inches="tight",
        )
    plt.close()

    return {
        "mean_npv": np.mean(npv_results),
        "std_npv": np.std(npv_results),
        "prob_loss": prob_loss,
        "var_95": np.percentile(npv_results, 5),
    }
