# config.py
"""
Konfigurationsdatei für die Energiespeicher-Simulation mit wirtschaftlicher Betrachtung.
"""
from pathlib import Path

# -------- Technische Parameter des Speichersystems --------
CAPACITY_MWH = 1.0  # Speicherkapazität in MWh
CHARGE_DISCHARGE_RATE = 0.5  # 0.5C bedeutet 2h für vollständige Ladung/Entladung
EFFICIENCY = 0.85  # 95% Wirkungsgrad
FEE_PER_MWH = 0.0  # Feste Gebühr in Euro pro MWh

# -------- Wirtschaftliche Parameter: CAPEX --------
BATTERY_COST_PER_MWH = 85000.0  # Batteriekosten in Euro pro MWh
INVERTER_COST_PER_MW = 75000.0  # Wechselrichterkosten in Euro pro MW
# Prozentsatz für Nebenkosten (Installation, Planung, etc.)
ADDITIONAL_COSTS_PERCENTAGE = 67.0


# -------- Wirtschaftliche Parameter: OPEX --------
ANNUAL_OPEX_PERCENTAGE = 0.75  # Jährliche Betriebskosten als Prozentsatz der CAPEX
INSURANCE_PERCENTAGE = 0.5  # Versicherungskosten als Prozentsatz der CAPEX pro Jahr
MAINTENANCE_COST_PER_MWH = 2500.0  # Jährliche Wartungskosten in Euro pro MWh Kapazität
INFLATION_RATE = 2.0  # Jährliche Inflationsrate in Prozent

# -------- Technische Parameter für Wirtschaftlichkeitsberechnung --------
ANNUAL_DEGRADATION_RATE = 2.0  # Jährliche Kapazitätsdegradation in Prozent
CYCLE_DEGRADATION_RATE = 0.005  # Degradation pro vollständigem Zyklus in Prozent

# Wirtschaftliche Simulationsparameter
SIMULATION_YEARS = 15  # Simulationszeitraum in Jahren
MAX_LIFETIME_CYCLES = 8000  # Maximale Lebensdauer in Zyklen
MAX_CYCLE_DEGRADATION = 0.3  # Maximale Degradation durch Zyklen (30%)
DEFAULT_ANNUAL_CYCLES = 300  # Standard-Anzahl jährlicher Zyklen (Fallback)
DISCOUNT_RATE = 0.05  # Diskontierungsrate für NPV-Berechnung (6%)

# -------- Visualisierungskonfiguration --------
OUTPUT_DIR = "output_plots"
SAVE_PLOTS = True
VISUALIZE_FREQUENCY = 1  # 1 = jeden Tag, 5 = jeden 5. Tag, 10 = jeden 10. Tag, usw.

# -------- Pfad zur Preisdatei --------
BASE_DIR = Path(__file__).parent
DEFAULT_PRICE_FILE = (
    BASE_DIR
    / "SMARD_15min_Jahr 2024_DE"
    / "Gro_handelspreise_202401010000_202501010000_Viertelstunde.csv"
)

# -------- Einstellungen für die TH-Strategie --------
ROLLING_WINDOW_SIZE = 6  # Fenstergröße für die TH-Strategie
