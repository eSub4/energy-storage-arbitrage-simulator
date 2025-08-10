# economic_analysis/npv_calculator.py

"""
Berechnung des Kapitalwerts (NPV) der Investition.
"""

import config
from economic_analysis.capex_calculator import calculate_total_capex
from economic_analysis.opex_calculator import calculate_annual_opex


def calculate_npv(annual_revenues, discount_rate=None):
    """
    Berechnet den Kapitalwert (NPV) basierend auf CAPEX, OPEX und jährlichen Einnahmen.
    """

    capex = calculate_total_capex()
    total_capex = capex["total_capex"]

    # Verwende übergebenen Wert oder default aus config
    if discount_rate is None:
        discount_rate = config.DISCOUNT_RATE

    # SIMULATION_YEARS aus config verwenden, statt EVALUATION_PERIOD_YEARS
    years = getattr(config, "SIMULATION_YEARS", 10)

    # Cash-Flows berechnen
    cash_flows = [-total_capex]  # Initial Investment (Jahr 0)

    cumulative_cash_flow = -total_capex
    payback_period = None

    for year in range(1, years + 1):
        # OPEX für das aktuelle Jahr
        opex = calculate_annual_opex(capex, year)

        # Jahreseinnahme (falls verfügbar, sonst 0)
        revenue = annual_revenues[year - 1] if year <= len(annual_revenues) else 0

        # Cash-Flow für dieses Jahr
        yearly_cash_flow = revenue - opex["total_opex"]
        cash_flows.append(yearly_cash_flow)

        # Kumulativer Cash-Flow für Amortisationszeit
        cumulative_cash_flow += yearly_cash_flow
        if payback_period is None and cumulative_cash_flow >= 0:
            payback_period = year

    # NPV berechnen
    npv = 0
    discount_factor = 1 + (config.DISCOUNT_RATE / 100)

    for year, cf in enumerate(cash_flows):
        npv += cf / (discount_factor**year)

    return {
        "npv": npv,
        "cash_flows": cash_flows,
        "payback_period": (
            payback_period if payback_period else "über Betrachtungszeitraum hinaus"
        ),
    }
