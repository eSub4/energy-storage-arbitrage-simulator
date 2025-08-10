# data/data_loader.py

"""
Funktionen zum Laden und Aufbereiten der Preisdaten.
"""
import pandas as pd
import logging
from utils.localization import format_date_german
import config

logger = logging.getLogger(__name__)


def load_price_data(file_path=None):
    """
    Lädt die Preisdaten aus der CSV-Datei.

    Args:
        file_path: Optionaler Pfad zur CSV-Datei. Wenn None, wird der Standardpfad verwendet.
    """
    try:
        # Falls kein Dateipfad übergeben wurde, verwende den Standardpfad aus der Konfiguration
        if file_path is None:
            file_path = config.DEFAULT_PRICE_FILE
            logger.info(f"Verwende Standardpfad aus der Konfiguration")

        # Versuchen, die CSV-Datei einzulesen
        logger.info(f"Starte Einlesen der Datei: {file_path}")
        df = pd.read_csv(file_path, sep=";", decimal=",")
        logger.info(f"Erfolgreich eingelesen: {len(df)} Zeilen")

        # Anpassung für das spezifische Format dieser CSV
        if "Datum von" in df.columns:
            df["datetime"] = pd.to_datetime(df["Datum von"], format="%d.%m.%Y %H:%M")
            logger.info(
                f"Zeitreihe konvertiert: {df['datetime'].min()} bis {df['datetime'].max()}"
            )

        # Preisspalte identifizieren und umbenennen
        if "Deutschland/Luxemburg [€/MWh] Berechnete Auflösungen" in df.columns:
            price_col = "Deutschland/Luxemburg [€/MWh] Berechnete Auflösungen"
            df.rename(columns={price_col: "price"}, inplace=True)
        else:
            # Allgemeinere Methode falls die Spalte nicht genau so heißt
            price_columns = [col for col in df.columns if "MWh" in col or "€" in col]
            if price_columns:
                logger.info(f"Preisspalte gefunden: {price_columns[0]}")
                df.rename(columns={price_columns[0]: "price"}, inplace=True)
            else:
                # Fallback
                logger.warning(
                    "Keine eindeutige Preisspalte gefunden, verwende letzte Spalte"
                )
                df.rename(columns={df.columns[-1]: "price"}, inplace=True)

        # Sicherstellen, dass die Preisspalte numerisch ist
        if isinstance(df["price"].iloc[0], str):
            df["price"] = df["price"].str.replace(",", ".").astype(float)
        else:
            df["price"] = pd.to_numeric(df["price"], errors="coerce")

        # Fehlende Werte behandeln
        if df["price"].isna().any():
            logger.warning(
                f"Warnung: {df['price'].isna().sum()} fehlende Werte in der Preisspalte gefunden."
            )
            df["price"] = df["price"].interpolate(method="linear")

        # Daten nach Zeitstempel sortieren
        if "datetime" in df.columns:
            df.sort_values("datetime", inplace=True)
            df.reset_index(drop=True, inplace=True)

            # Informationen über die aufbereiteten Daten anzeigen
            logger.info("\nAufbereitete Daten:")
            logger.info(
                f"Zeitraum: {format_date_german(df['datetime'].min())} bis {format_date_german(df['datetime'].max())}"
            )
            logger.info(f"Anzahl der Datenpunkte: {len(df)}")
            logger.info(
                f"Preisbereich: {df['price'].min():.2f} € bis {df['price'].max():.2f} €/MWh"
            )
            logger.info(f"Durchschnittspreis: {df['price'].mean():.2f} €/MWh")
            logger.info(f"Preisvolatilität (Stdabw.): {df['price'].std():.2f} €/MWh")

            # Zähle die Anzahl der Tage
            df["date"] = df["datetime"].dt.date
            unique_days = df["date"].nunique()
            logger.info(f"Anzahl der Tage im Datensatz: {unique_days}")

        return df

    except Exception as e:
        logger.error(f"Fehler beim Einlesen der Datei: {str(e)}")
        return None
