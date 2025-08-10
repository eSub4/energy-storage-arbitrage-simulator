# economic_analysis/opex_calculator.py

"""
Berechnung der Betriebskosten (OPEX) für einen Batteriespeicher.
"""

import config


def calculate_annual_opex(capex, year=1):
    """Berechnet die jährlichen Betriebskosten."""
    # Wartung und Betrieb als Prozentsatz der CAPEX
    maintenance_operations = capex["total_capex"] * (
        config.ANNUAL_OPEX_PERCENTAGE / 100
    )

    # Versicherungskosten
    insurance = capex["total_capex"] * (config.INSURANCE_PERCENTAGE / 100)

    # Kapazitätsabhängige Wartungskosten
    capacity_based_maintenance = config.CAPACITY_MWH * config.MAINTENANCE_COST_PER_MWH

    # Inflationsanpassung für spätere Jahre
    inflation_factor = (1 + config.INFLATION_RATE / 100) ** (year - 1)

    total_opex = (
        maintenance_operations + insurance + capacity_based_maintenance
    ) * inflation_factor

    return {
        "maintenance_operations": maintenance_operations * inflation_factor,
        "insurance": insurance * inflation_factor,
        "capacity_based_maintenance": capacity_based_maintenance * inflation_factor,
        "total_opex": total_opex,
    }
