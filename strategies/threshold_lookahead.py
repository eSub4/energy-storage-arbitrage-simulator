# strategies/threshold_lookahead.py

"""
Implementiert eine perzentil-basierte Handelsstrategie mit Vorausschau (Lookahead).

Dieses Modul enthält die Kernlogik für die Handelsentscheidungen des Batteriespeichers.
Die Strategie basiert auf der Analyse von Preis-Perzentilen innerhalb eines rollierenden
Zeitfensters, um Kauf- und Verkaufsschwellen dynamisch zu bestimmen. Zusätzliche
heuristische Prüfungen werden angewendet, um die Profitabilität zu maximieren und
suboptimale Handelsentscheidungen zu vermeiden.
"""


def threshold_lookahead(prices_df, storage, window_size=None):
    """Führt eine perzentil-basierte Handelsstrategie mit Vorausschau aus.

    Diese Funktion simuliert den Betrieb eines Energiespeichers über einen gesamten
    Zeitraum, basierend auf einer dynamischen Schwellenwertstrategie. Für jeden
    Zeitpunkt wird ein Vorausschau-Fenster analysiert, um Kauf- und Verkaufsschwellen
    (z. B. 20. und 80. Perzentil) zu ermitteln.

    Die eigentliche Handelsentscheidung unterliegt weiteren Validierungsprüfungen:
    - Prüfung auf ausreichende Kapazität (SoC-Grenzen).
    - Erwartung einer positiven Preisentwicklung (Preis-Tendenz).
    - Vergleich mit dem letzten Handelsgeschäft zur Vermeidung von Folgeverlusten.
    - Dynamische Anpassung des Handelsvolumens basierend auf der Preisextremität.
    - Einhaltung eines Mindesthandelsvolumens.

    Lade- und Entladevorgänge werden als kontinuierliche Prozesse modelliert, die
    mehrere Zeitintervalle andauern können, bis ein definiertes Ziel erreicht ist.

    Args:
        prices_df (pd.DataFrame): Ein DataFrame, der die Preisdaten enthält.
            Muss die Spalten 'price' (numerisch) und 'datetime' (datetime-Objekt)
            enthalten.
        storage (EnergyStorage): Eine Instanz der `EnergyStorage`-Klasse, die
            den Zustand des Speichers modelliert und durch die Strategie
            gesteuert wird.
        window_size (int, optional): Die Größe des Vorausschau-Fensters in
            Anzahl der Zeitintervalle. Wenn nicht angegeben, wird der Wert
            `ROLLING_WINDOW_SIZE` aus der `config.py` verwendet.

    Returns:
        tuple: Ein Tupel, das zwei Elemente enthält:
            - EnergyStorage: Das aktualisierte `storage`-Objekt nach Abschluss
              der Simulation, inklusive aller Transaktionsprotokolle und
              finalen Kennzahlen.
            - list: Eine detaillierte `energy_history`, die für jeden
              Zeitpunkt den Ladezustand und die durchgeführte Aktion
              (Laden, Entladen, Halten) als Dictionary speichert.
    """

    import numpy as np
    import logging
    import time
    from config import ROLLING_WINDOW_SIZE

    logger = logging.getLogger(__name__)

    # Fenstergröße aus Config verwenden, falls nicht explizit übergeben
    if window_size is None:
        window_size = ROLLING_WINDOW_SIZE

    price_array = prices_df["price"].values
    T = len(price_array)

    logger.info(
        f"Starte perzentil-basierte TH mit Rolling Window Fenstergröße {window_size}, für {T} Zeitpunkte"
    )

    energy_history = []

    # Zielvorgaben für laufende Vorgänge
    charge_target = None  # Ziel-Energielevel beim Laden
    discharge_target = None  # Ziel-Energielevel beim Entladen
    current_operation_price = None  # Preis der aktuellen Operation

    # Parameter für wirtschaftlich sinnvolle Kauf-/Verkaufsentscheidungen
    last_discharge_price = 0  # Letzter Verkaufspreis
    last_charge_price = float("inf")  # Letzter Kaufpreis, initial auf unendlich

    # Tracking für Statusmeldungen
    last_status_time = time.time()
    status_interval = 10  # Statusmeldung alle 10 Sekunden

    # Schrittweise durch den gesamten Zeitraum gehen
    idx = 0
    while idx < T:
        # Statusmeldung für längere Simulationen
        current_time = time.time()
        if current_time - last_status_time > status_interval:
            progress = (idx / T) * 100
            logger.info(f"Fortschritt: {progress:.1f}% ({idx}/{T} Zeitpunkte)")
            last_status_time = current_time

        # Energiestand speichern
        energy_history.append(
            {
                "time_index": idx,
                "energy_level": storage.energy_level,
                "action": (
                    1 if storage.is_charging else (-1 if storage.is_discharging else 0)
                ),
            }
        )

        # Wenn bereits ein Vorgang läuft, fortsetzen bis zum Ziel erreicht
        if storage.is_processing():
            if storage.is_charging and charge_target is not None:
                # Prüfen ob Ladeziel erreicht wurde
                if storage.energy_level >= charge_target - 0.1:  # Kleine Toleranz
                    storage.is_charging = False
                    logger.debug(
                        f"  ✓ Ladevorgang abgeschlossen: {storage.energy_level:.2f} MWh (Ziel: {charge_target:.2f} MWh)"
                    )
                    charge_target = None
                    current_operation_price = None
                else:
                    # Weiter laden
                    storage.continue_process(idx)

            elif storage.is_discharging and discharge_target is not None:
                # Prüfen ob Entladeziel erreicht wurde
                if storage.energy_level <= discharge_target + 0.1:  # Kleine Toleranz
                    storage.is_discharging = False
                    logger.debug(
                        f"  ✓ Entladevorgang abgeschlossen: {storage.energy_level:.2f} MWh (Ziel: {discharge_target:.2f} MWh)"
                    )
                    discharge_target = None
                    current_operation_price = None
                    # Speichere den Preis des abgeschlossenen Entladevorgangs
                    last_discharge_price = (
                        current_price if "current_price" in locals() else 0
                    )
                    # Nach einem Entladevorgang den letzten Ladepreis zurücksetzen
                    last_charge_price = float("inf")
                else:
                    # Weiter entladen
                    storage.continue_process(idx)
            else:
                # Sicherheitsabbruch falls keine Ziele definiert
                storage.continue_process(idx)

            idx += 1
            continue

        # Neue Handelsentscheidung nur wenn kein Vorgang läuft
        current_price = price_array[idx]

        # Erweiterte Zukunftsanalyse mit Rolling Window
        look_ahead_window = min(window_size, T - idx)

        # Mindestfenstergröße-Prüfung entfernt, alle Fenstergrößen werden berücksichtigt
        if look_ahead_window >= 1:  # Mindestens 1 Datenpunkt muss vorhanden sein
            future_prices = price_array[idx : idx + look_ahead_window]

            # Perzentil-Berechnungen für zukünftige Preise
            buy_threshold_percentile = (
                20  # Nur kaufen, wenn Preis unter dem 20. Perzentil liegt
            )
            sell_threshold_percentile = (
                80  # Nur verkaufen, wenn Preis über dem 80. Perzentil liegt
            )

            buy_threshold_price = np.percentile(future_prices, buy_threshold_percentile)
            sell_threshold_price = np.percentile(
                future_prices, sell_threshold_percentile
            )

            future_mean = np.mean(future_prices)
            future_std = np.std(future_prices)

            # KAUFENTSCHEIDUNG (Laden) - ohne Sonderbehandlung negativer Preise
            if storage.energy_level < storage.capacity * 0.9:  # Noch Platz vorhanden
                # Sonderbehandlung negativer Preise entfernt
                is_very_low_price = current_price < buy_threshold_price
                price_likely_to_rise = (
                    future_mean > current_price * 1.2
                )  # 20% wahrscheinlicher Anstieg

                # NEUE PRÜFUNG: Ist der aktuelle Preis besser als der letzte Kaufpreis?
                is_better_than_last_charge = (
                    current_price < last_charge_price * 0.95
                )  # 5% niedriger als der letzte Kaufpreis

                if (
                    is_very_low_price
                    and price_likely_to_rise
                    and (
                        is_better_than_last_charge or last_charge_price == float("inf")
                    )
                ):
                    # Berechne Ziel-Lademenge
                    available_capacity = storage.capacity - storage.energy_level

                    # Bei sehr niedrigen Preisen (unter 10. Perzentil): Mehr laden
                    if current_price < np.percentile(future_prices, 10):
                        target_amount = (
                            available_capacity * 0.8
                        )  # 80% der verfügbaren Kapazität laden
                    else:
                        # Sonst moderate Menge (40-60% der verfügbaren Kapazität)
                        target_amount = available_capacity * 0.5

                    # Stelle sicher, dass wir eine sinnvolle Menge laden
                    if target_amount >= storage.capacity * 0.1:
                        # Setze Ladeziel
                        charge_target = storage.energy_level + target_amount
                        charge_target = min(
                            charge_target, storage.capacity
                        )  # Nicht über Kapazität

                        # Zeit für Log-Ausgabe bestimmen (Tageszeit formatieren)
                        try:
                            current_datetime = prices_df.iloc[idx]["datetime"]
                            time_str = current_datetime.strftime("%d.%m. %H:%M")
                        except (IndexError, KeyError, AttributeError):
                            time_str = f"Index {idx}"

                        logger.debug(f"\n🟢 GROSSHANDELSKAUF ENTSCHEIDUNG:")
                        logger.debug(f"   Zeitpunkt: {time_str}")
                        logger.debug(f"   Aktueller Preis: {current_price:.2f} €/MWh")
                        logger.debug(
                            f"   Letzter Kaufpreis: {last_charge_price if last_charge_price != float('inf') else 'Kein vorheriger Kauf'}"
                        )
                        logger.debug(
                            f"   Zukünftiger Durchschnittspreis: {future_mean:.2f} €/MWh"
                        )
                        logger.debug(
                            f"   Aktueller Ladestand: {storage.energy_level:.2f} MWh ({storage.energy_level/storage.capacity*100:.1f}%)"
                        )
                        logger.debug(
                            f"   Ziel-Ladestand: {charge_target:.2f} MWh ({charge_target/storage.capacity*100:.1f}%)"
                        )
                        logger.debug(
                            f"   Zu ladende Menge: {charge_target - storage.energy_level:.2f} MWh"
                        )

                        # Aktualisiere den letzten Kaufpreis
                        last_charge_price = current_price
                        current_operation_price = current_price
                        storage.start_charging(current_price, idx)
                        # Nach einem Ladevorgang den letzten Entladepreis zurücksetzen
                        last_discharge_price = 0
                        idx += 1
                        continue

            # VERKAUFSENTSCHEIDUNG (Entladen)
            if storage.energy_level > storage.capacity * 0.1:  # Genug Energie vorhanden
                is_very_high_price = current_price > sell_threshold_price
                price_likely_to_fall = (
                    future_mean < current_price * 0.9
                )  # 10% wahrscheinlicher Abfall

                # Ist der aktuelle Preis besser als der letzte Entladepreis?
                is_better_than_last_discharge = (
                    current_price > last_discharge_price * 1.05
                )  # 5% höher als der letzte Entladepreis

                if (
                    is_very_high_price
                    and price_likely_to_fall
                    and (is_better_than_last_discharge or last_discharge_price == 0)
                ):
                    # Berechne Ziel-Entlademenge
                    available_energy = storage.energy_level

                    # Bei sehr hohen Preisen: Mehr entladen
                    if current_price > np.percentile(
                        future_prices, 90
                    ):  # Extrem hoher Preis (über 90. Perzentil)
                        target_amount = (
                            available_energy * 0.8
                        )  # 80% der verfügbaren Energie entladen
                    else:
                        # Sonst moderate Menge (40-60% der verfügbaren Energie)
                        target_amount = available_energy * 0.5

                    # Stelle sicher, dass wir eine sinnvolle Menge entladen
                    if target_amount >= storage.capacity * 0.1:
                        # Setze Entladeziel
                        discharge_target = storage.energy_level - target_amount
                        discharge_target = max(discharge_target, 0)  # Nicht unter 0

                        # Zeit für Log-Ausgabe bestimmen
                        try:
                            current_datetime = prices_df.iloc[idx]["datetime"]
                            time_str = current_datetime.strftime("%d.%m. %H:%M")
                        except (IndexError, KeyError, AttributeError):
                            time_str = f"Index {idx}"

                        logger.debug(f"\n🔴 GROSSHANDELSVERKAUF ENTSCHEIDUNG:")
                        logger.debug(f"   Zeitpunkt: {time_str}")
                        logger.debug(f"   Aktueller Preis: {current_price:.2f} €/MWh")
                        logger.debug(
                            f"   Letzter Entladepreis: {last_discharge_price:.2f} €/MWh"
                        )
                        logger.debug(
                            f"   Zukünftiger Durchschnittspreis: {future_mean:.2f} €/MWh"
                        )
                        logger.debug(
                            f"   Aktueller Ladestand: {storage.energy_level:.2f} MWh ({storage.energy_level/storage.capacity*100:.1f}%)"
                        )
                        logger.debug(
                            f"   Ziel-Ladestand: {discharge_target:.2f} MWh ({discharge_target/storage.capacity*100:.1f}%)"
                        )
                        logger.debug(
                            f"   Zu entladende Menge: {storage.energy_level - discharge_target:.2f} MWh"
                        )

                        current_operation_price = current_price
                        # Aktualisiere den letzten Entladepreis
                        last_discharge_price = current_price
                        # Nach einem Entladevorgang den letzten Ladepreis zurücksetzen
                        last_charge_price = float("inf")
                        storage.start_discharging(current_price, idx)
                        idx += 1
                        continue

        idx += 1

    logger.info(
        f"Perzentil-basierte TH abgeschlossen. Energieverlauf mit {len(energy_history)} Einträgen erstellt."
    )
    return storage, energy_history


def create_trading_summary(energy_history):
    """
    Erstellt eine Zusammenfassung der Großhandelsgeschäfte.
    """
    trades = []
    current_trade = None

    for i, state in enumerate(energy_history):
        if state["action"] != 0 and current_trade is None:
            # Neuer Trade beginnt
            current_trade = {
                "type": "charge" if state["action"] == 1 else "discharge",
                "start_index": state["time_index"],
                "start_energy": state["energy_level"],
                "intervals": 1,
            }
        elif current_trade is not None:
            if state["action"] == 0:
                # Trade endet
                current_trade["end_index"] = state["time_index"] - 1
                current_trade["end_energy"] = (
                    energy_history[i - 1]["energy_level"]
                    if i > 0
                    else state["energy_level"]
                )
                current_trade["energy_traded"] = abs(
                    current_trade["end_energy"] - current_trade["start_energy"]
                )
                trades.append(current_trade)
                current_trade = None
            else:
                # Trade läuft weiter
                current_trade["intervals"] += 1

    # Letzten Trade abschließen, falls noch offen
    if current_trade is not None:
        current_trade["end_index"] = energy_history[-1]["time_index"]
        current_trade["end_energy"] = energy_history[-1]["energy_level"]
        current_trade["energy_traded"] = abs(
            current_trade["end_energy"] - current_trade["start_energy"]
        )
        trades.append(current_trade)

    return trades
