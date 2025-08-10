# visualization/parallel_plotting.py

"""
Beschleunigt die Erstellung von Tages-Visualisierungen durch parallele Verarbeitung.

Dieses Modul löst das Performance-Problem, das bei der sequenziellen Erstellung
einer großen Anzahl von Diagrammen entsteht. Anstatt jedes Tages-Diagramm
nacheinander zu generieren, nutzt es den `concurrent.futures.ProcessPoolExecutor`,
um die Aufgaben auf alle verfügbaren CPU-Kerne zu verteilen.

Die Hauptfunktion `create_visualizations_parallel` agiert als Manager, der die
zu visualisierenden Tage auswählt und an einen Pool von Arbeiter-Prozessen
verteilt. Jeder dieser Prozesse führt die `visualize_single_day`-Funktion aus,
um ein einzelnes Diagramm zu erstellen und zu speichern. Dieser Ansatz reduziert
die Gesamtdauer für die Visualisierung drastisch.
"""


def create_visualizations_parallel(
    daily_results,
    prices_df,
    output_dir,
    save_plots=True,
    show_plots=False,
    visualization_frequency=10,
):
    """
    Erstellt Visualisierungen für alle Tage parallel.

    Parameters:
    -----------
    daily_results : list
        Liste mit den täglichen Analyseergebnissen
    prices_df : DataFrame
        DataFrame mit den Preisdaten für den gesamten Zeitraum
    output_dir : str
        Verzeichnis für die Ausgabe der Grafiken
    save_plots : bool, optional
        Ob Plots gespeichert werden sollen
    show_plots : bool, optional
        Ob Plots angezeigt werden sollen (sollte für Parallelisierung False sein)
    visualization_frequency : int, optional
        Frequenz der Visualisierung (z.B. 10 = jeder 10. Tag wird visualisiert)
    """
    show_plots = False

    import concurrent.futures
    import os
    import time
    import logging

    logger = logging.getLogger(__name__)

    # Berechne die Anzahl der zu visualisierenden Tage
    days_to_visualize = len(
        [r for i, r in enumerate(daily_results) if i % visualization_frequency == 0]
    )

    logger.info(
        f"Starte parallele Visualisierung für {days_to_visualize} Tage mit {os.cpu_count()} Prozessen"
    )
    start_time = time.time()

    # Stelle sicher, dass das Ausgabeverzeichnis existiert
    daily_viz_dir = output_dir
    os.makedirs(daily_viz_dir, exist_ok=True)

    # Liste der zu visualisierenden Tage erstellen
    visualization_tasks = []
    for day_index, result in enumerate(daily_results):
        if day_index % visualization_frequency == 0:
            visualization_tasks.append((day_index, result))

    # Fortschrittszähler für Logging
    processed_count = 0
    total_count = len(visualization_tasks)

    # ProcessPoolExecutor für CPU-intensive Aufgaben
    with concurrent.futures.ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        # Aufgaben einreichen
        future_to_day = {
            executor.submit(
                visualize_single_day,
                result,
                prices_df,
                daily_viz_dir,
                save_plots,
                show_plots,
            ): (day_index, result["date"])
            for day_index, result in visualization_tasks
        }

        # Ergebnisse sammeln
        for future in concurrent.futures.as_completed(future_to_day):
            day_index, date = future_to_day[future]
            processed_count += 1

            try:
                # Ergebnis des Futures abrufen (fängt Ausnahmen ab)
                success = future.result()
                progress = (processed_count / total_count) * 100

                # Nur alle 5% Fortschrittsmeldungen ausgeben, um das Log nicht zu überfüllen
                if processed_count % max(1, total_count // 20) == 0:
                    logger.info(
                        f"Visualisierung: [{progress:.1f}%] Tag {day_index+1}: {date.strftime('%d.%m.%Y')} verarbeitet"
                    )

            except Exception as e:
                logger.error(
                    f"Fehler bei der Visualisierung von Tag {day_index} ({date}): {str(e)}"
                )

    elapsed_time = time.time() - start_time
    logger.info(
        f"Parallele Visualisierung abgeschlossen in {elapsed_time:.2f} Sekunden"
    )


def visualize_single_day(
    result, prices_df, output_dir, save_plot=True, show_plot=False
):
    """
    Visualisiert einen einzelnen Tag. Diese Funktion wird für jeden Tag in einem eigenen Prozess ausgeführt.

    Parameters:
    -----------
    result : dict
        Tagesergebnis mit allen relevanten Daten
    prices_df : DataFrame
        DataFrame mit allen Preisdaten (wird gefiltert)
    output_dir : str
        Ausgabeverzeichnis
    save_plot : bool
        Ob der Plot gespeichert werden soll
    show_plot : bool
        Ob der Plot angezeigt werden soll (sollte für Parallelisierung False sein)

    Returns:
    --------
    bool
        True bei Erfolg, False bei Fehler
    """
    import pandas as pd
    from visualization.plotting import visualize_day
    import matplotlib.pyplot as plt

    try:
        # Matplotlib auf nicht-interaktiven Backend setzen für Multiprocessing
        plt.switch_backend("Agg")

        # Datum extrahieren
        date_dt = result["date"]

        # Transaktionen extrahieren
        day_transactions_df = result.get("transactions", pd.DataFrame())

        # Preisdaten für diesen Tag filtern
        day_prices = (
            prices_df[prices_df["datetime"].dt.date == date_dt.date()]
            .copy()
            .reset_index()
        )

        # Energiehistorie extrahieren - wir müssen diese aus dem Gesamtergebnis rekonstruieren
        # Falls in result nicht enthalten, erstellen wir eine leere Liste
        if "energy_history" in result:
            day_energy_history = result["energy_history"]
        else:
            # Fallback: Leere Energiehistorie
            day_energy_history = []

        # Visualisierung erstellen
        visualize_day(
            day_prices,
            day_transactions_df,
            day_energy_history,
            date_dt,
            output_dir=output_dir,
            save_plot=save_plot,
            show_plot=show_plot,
            daily_cycles=result.get("cycles_completed", 0),
        )

        return True

    except Exception as e:
        # Bei Fehler in einzelner Visualisierung nur diese überspringen
        import traceback

        print(f"Fehler bei Visualisierung für {result['date']}: {str(e)}")
        print(traceback.format_exc())
        return False
