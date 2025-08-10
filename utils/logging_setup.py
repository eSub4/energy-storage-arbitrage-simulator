# utils/logging_setup.py
"""
Konfiguration des Loggings für die Anwendung.
"""
import logging
import os


def setup_logging():
    """
    Konfiguriert das Logging für die Anwendung.
    """
    # Sicherstellen, dass Logs-Verzeichnis existiert
    if not os.path.exists("logs"):
        os.makedirs("logs")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("logs/energy_analysis.log"),
            logging.StreamHandler(),
        ],
    )

    return logging.getLogger(__name__)
