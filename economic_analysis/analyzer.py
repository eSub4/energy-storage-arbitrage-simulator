# economic_analysis/analyzer.py

"""
Berechnet den Nettokapitalwert (NPV) für Investitionsprojekte.

Dieses Modul stellt einen Rechner zur Verfügung, der CAPEX, OPEX
und Einnahmen über eine bestimmte Projektdauer berücksichtigt, um die
Rentabilität einer Investition zu bewerten.
"""


def run_economic_analysis(
    prices_df,
    output_dir=None,
    annual_profit=None,
    annual_cycles=None,
    daily_results=None,
):
    """
    Führt die wirtschaftliche Analyse des Energiespeichers durch.

    Parameters:
    -----------
    prices_df : DataFrame
        DataFrame mit den Preisdaten
    output_dir : str, optional
        Verzeichnis für Ausgabedateien
    annual_profit : float, optional
        Tatsächlicher jährlicher Gewinn aus den Tagesanalysen
    annual_cycles : float, optional
        Tatsächliche jährliche Zyklen aus den Tagesanalysen
    daily_results : list, optional
        Liste mit den Ergebnissen der täglichen Analysen (für erweiterte Visualisierungen)

    """

    # Logger einrichten
    from utils.logging_setup import setup_logging

    logger = setup_logging()

    import os
    from economic_analysis.capex_calculator import (
        calculate_total_capex as calculate_capex,
    )
    from economic_analysis.opex_calculator import (
        calculate_annual_opex as calculate_opex,
    )
    from economic_analysis.npv_calculator import calculate_npv

    # Konfigurationsparameter importieren
    from config import (
        CAPACITY_MWH,
        SIMULATION_YEARS,
        MAX_LIFETIME_CYCLES,
        MAX_CYCLE_DEGRADATION,
        DEFAULT_ANNUAL_CYCLES,
        DISCOUNT_RATE,
    )

    logger.info("Starte wirtschaftliche Analyse...")

    # CAPEX berechnen
    capex_results = calculate_capex()

    # OPEX berechnen
    opex_results = calculate_opex(capex=capex_results, year=1)

    # Wirtschaftliche Simulation durchführen
    years = SIMULATION_YEARS

    if annual_profit is not None:
        # Jahresgewinn aus den Tagesanalysen verwenden
        logger.info(f"Verwende Jahresgewinn aus Tagesanalysen: {annual_profit:.2f} €")

        # Zyklen berücksichtigen
        if annual_cycles is not None:
            logger.info(f"Verwende jährliche Zyklen: {annual_cycles:.1f}")
        else:
            # Fallback, wenn keine Zyklen übergeben wurden
            annual_cycles = DEFAULT_ANNUAL_CYCLES
            logger.info(
                f"Keine Zyklen verfügbar, verwende Standardannahme: {annual_cycles} Zyklen/Jahr"
            )

        # Einfache Degradation basierend nur auf Zyklen
        max_lifetime_cycles = MAX_LIFETIME_CYCLES
        max_cycle_degradation = MAX_CYCLE_DEGRADATION

        # Jährliche Einnahmen und Kapazität unter Berücksichtigung von Degradation
        annual_revenues = []
        remaining_capacity = []
        yearly_cycles = []
        cumulative_cycles = 0

        for year in range(years):
            # Kumulative Zyklen berechnen
            cumulative_cycles += annual_cycles

            # Degradation durch Zyklen berechnen (maximal 30% Verlust)
            # Lineare Interpolation: 0 Zyklen = 0% Verlust, max_lifetime_cycles = 30% Verlust
            cycle_degradation = min(
                max_cycle_degradation,
                (cumulative_cycles / max_lifetime_cycles) * max_cycle_degradation,
            )

            # Verbleibende Kapazität (in Prozent)
            capacity_factor = 1.0 - cycle_degradation
            remaining_capacity.append(CAPACITY_MWH * capacity_factor)

            # Einnahmen werden proportional zur Kapazität reduziert
            yearly_revenue = annual_profit * capacity_factor
            annual_revenues.append(yearly_revenue)

            # Zyklen werden mit der Zeit auch reduziert (weniger Kapazität → weniger Handelsvolumen)
            yearly_cycles.append(annual_cycles * capacity_factor)

        # Gesamtergebnis für alle Jahre berechnen
        total_revenue = sum(annual_revenues)
        average_yearly_revenue = total_revenue / years
        final_capacity_percentage = (remaining_capacity[-1] / CAPACITY_MWH) * 100

        logger.info(f"Gesamteinnahmen über {years} Jahre: {total_revenue:.2f} €")
        logger.info(
            f"Durchschnittliche jährliche Einnahmen: {average_yearly_revenue:.2f} €"
        )
        logger.info(
            f"Verbleibende Kapazität nach {years} Jahren: {final_capacity_percentage:.1f}%"
        )

        # Simulationsergebnisse zusammenstellen
        simulation_results = {
            "annual_revenues": annual_revenues,
            "average_yearly_revenue": average_yearly_revenue,
            "total_revenue": total_revenue,
            "annual_cycles": yearly_cycles,
            "remaining_capacity": remaining_capacity,
            "final_capacity_percentage": final_capacity_percentage,
        }

    # NPV und andere Wirtschaftlichkeitskennzahlen berechnen
    npv_results = calculate_npv(simulation_results["annual_revenues"])

    # Den Discount Rate Wert zum Ergebnis hinzufügen, damit er verfügbar ist für Visualisierungen
    npv_results["discount_rate"] = DISCOUNT_RATE

    # Visualisierungen erstellen, falls ein Output-Verzeichnis angegeben wurde
    if output_dir:
        try:
            from visualization.plotting import (
                plot_economic_results_extended,
                plot_breakeven_scenarios,
                plot_monthly_profit_analysis,
                plot_trading_heatmap,
            )
            import os

            # Separaten Unterordner für wirtschaftliche Analysen erstellen
            econ_dir = os.path.join(output_dir, "wirtschaftliche_analyse")
            os.makedirs(econ_dir, exist_ok=True)

            # Pfad für die Grafik im neuen Unterordner
            plot_path = os.path.join(econ_dir, "economic_analysis.png")

            # Gemeinsame Ergebnisdaten für alle Visualisierungsfunktionen mit explizitem Discount Rate
            economic_data = {
                "capex": capex_results,
                "opex": opex_results,
                "npv": npv_results,
                "simulation": simulation_results,
                "discount_rate": DISCOUNT_RATE,
            }

            # Standard-Grafiken erstellen und speichern
            detailed_results = plot_economic_results_extended(economic_data, plot_path)

            # Zusätzliche Visualisierungen erstellen

            # 1. Break-Even-Szenarien
            try:
                breakeven_results = plot_breakeven_scenarios(economic_data, plot_path)
                if breakeven_results and "standard_breakeven" in breakeven_results:
                    be_years = breakeven_results["standard_breakeven"]
                    # Angepasste Log-Nachricht mit Berücksichtigung des konfigurierten Zeitraums
                    if be_years:
                        if be_years < years:
                            logger.info(
                                f"Break-Even im Standardszenario: {be_years:.2f} Jahre"
                            )
                        else:
                            logger.info(
                                f"Break-Even im Standardszenario: > {years} Jahre"
                            )
                    else:
                        logger.info(f"Break-Even im Standardszenario: > {years} Jahre")
            except Exception as e:
                logger.warning(f"Fehler bei den Break-Even-Szenarien: {e}")

            # 2. & 3. Monatliche Gewinnanalyse und Trading Heatmap
            if daily_results:
                try:
                    monthly_results = plot_monthly_profit_analysis(
                        daily_results, plot_path
                    )
                    if monthly_results:
                        logger.info(
                            f"Monatliche Gewinnanalyse erstellt: Bester Monat ist {monthly_results.get('best_month', 'N/A')}"
                        )
                except Exception as e:
                    logger.warning(f"Fehler bei der monatlichen Gewinnanalyse: {e}")

                try:
                    trading_results = plot_trading_heatmap(daily_results, plot_path)
                    if trading_results:
                        charge_hour = trading_results.get("most_active_charge_hour")
                        if charge_hour is not None:
                            logger.info(
                                f"Trading-Heatmap erstellt: Beste Ladestunde ist {charge_hour}:00 Uhr"
                            )
                        else:
                            logger.info(
                                "Trading-Heatmap erstellt: Keine eindeutige beste Ladestunde identifiziert"
                            )
                except Exception as e:
                    logger.warning(f"Fehler bei der Trading-Heatmap: {e}")
            else:
                logger.info(
                    "Keine täglichen Ergebnisse für die erweiterte Visualisierung verfügbar"
                )

            # Zusätzliche Informationen loggen
            if detailed_results and "breakeven_point" in detailed_results:
                if detailed_results["breakeven_point"]:
                    # Angepasste Log-Nachricht mit Berücksichtigung des konfigurierten Zeitraums
                    if detailed_results["breakeven_point"] < years:
                        logger.info(
                            f"Break-Even (nominal): {detailed_results['breakeven_point']:.2f} Jahre"
                        )
                    else:
                        logger.info(f"Break-Even (nominal): > {years} Jahre")
                else:
                    logger.info(f"Break-Even (nominal): > {years} Jahre")

            logger.info(
                f"Erweiterte wirtschaftliche Analyse-Grafiken gespeichert im Verzeichnis: {econ_dir}"
            )

        except Exception as e:
            logger.warning(f"Fehler beim Erstellen der Grafik: {e}")
            logger.warning(
                "Visualisierung übersprungen, aber wirtschaftliche Analyse wurde durchgeführt."
            )

    logger.info(
        f"Wirtschaftliche Analyse abgeschlossen. NPV: {npv_results['npv']:.2f} €"
    )

    # Auch im Rückgabewert den Discount Rate übergeben
    return {
        "capex": capex_results,
        "opex": opex_results,
        "npv": npv_results,
        "simulation": simulation_results,
        "discount_rate": DISCOUNT_RATE,
    }
