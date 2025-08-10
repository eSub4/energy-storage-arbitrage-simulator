# economic_analysis/capex_calculator.py

"""
Berechnung der Kapitalkosten (CAPEX) für den Batteriespeicher.
"""

import config


def calculate_total_capex():
    """Berechnet die Kapitalkosten des Batteriespeichers."""
    # Batteriekosten
    battery_cost = config.CAPACITY_MWH * config.BATTERY_COST_PER_MWH

    # Wechselrichterkosten (basierend auf max. Leistung)
    max_power_mw = config.CAPACITY_MWH * config.CHARGE_DISCHARGE_RATE
    inverter_cost = max_power_mw * config.INVERTER_COST_PER_MW

    # Basis-CAPEX
    base_capex = battery_cost + inverter_cost

    # Zusätzliche Kosten (Installation, Planung, etc.)
    additional_costs = base_capex * (config.ADDITIONAL_COSTS_PERCENTAGE / 100)

    # Gesamtkosten
    total_capex = base_capex + additional_costs

    return {
        "battery_cost": battery_cost,
        "inverter_cost": inverter_cost,
        "base_capex": base_capex,
        "additional_costs": additional_costs,
        "total_capex": total_capex,
    }
