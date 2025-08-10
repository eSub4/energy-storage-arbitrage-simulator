# models/energy_storage.py
"""
Implementierung des Energiespeicher-Modells.
"""
import logging
import config  # Import für die Degradations-Berechnung

logger = logging.getLogger(__name__)


class EnergyStorage:
    """
    Modelliert einen Energiespeicher.
    """

    def __init__(self, capacity_mwh, charge_rate, efficiency, fee_per_mwh):
        self.capacity = capacity_mwh  # MWh
        self.charge_rate = charge_rate  # C-Rate
        self.max_power = capacity_mwh * charge_rate  # MW
        self.efficiency = efficiency  # Wirkungsgrad
        self.fee_per_mwh = fee_per_mwh  # Feste Gebühr in Euro pro MWh

        # Zustandsvariablen
        self.energy_level = 0.0  # Aktueller Energiestand in MWh
        self.cash = 0.0  # Kassabestand in €
        self.transactions = []  # Liste der Transaktionen

        # Ladestatus
        self.is_charging = False  # Aktueller Lademodus
        self.is_discharging = False  # Aktueller Entlademodus
        self.charging_price = 0.0  # Preis, zu dem geladen wird
        self.discharging_price = 0.0  # Preis, zu dem entladen wird
        self.charging_start_index = -1  # Index des Beginns des aktuellen Ladevorgangs
        self.current_interval = 0  # Aktuelles Intervall des laufenden Ladevorgangs

        # Ein Ladevorgang läuft so lange, bis das Ziel erreicht ist

        # Gesamtstatistik
        self.total_charged_energy = 0.0  # Gesamte geladene Energie
        self.total_discharged_energy = (
            0.0  # Gesamte nutzbare entladene Energie (nach Effizienzverlusten)
        )
        self.total_gross_energy = (
            0.0  # Gesamte entnommene Energie (ohne Effizienzverluste)
        )
        self.total_charge_cost = 0.0  # Gesamtkosten für Laden
        self.total_discharge_revenue = 0.0  # Gesamterlös aus Entladen

        # Statistik für die Effizienz-Berechnung
        self.gross_energy_revenue = 0.0  # Erlös ohne Effizienz-Verluste
        self.efficiency_losses = 0.0  # Erlösverluste durch Effizienz
        self.energy_losses = 0.0  # Energieverluste durch Effizienz in MWh

        # Hinzugefügte Attribute für die wirtschaftliche Simulation
        self.total_cycles = 0.0  # Gesamtanzahl der Zyklen (kumulativ)
        self.daily_cycles = 0.0  # Zyklen des aktuellen Tages (wird zurückgesetzt)
        self.operation_time_days = 0  # Betriebsdauer in Tagen

    # Property für den Gesamtgewinn (für einfachen Zugriff als Attribut)
    @property
    def total_profit(self):
        """Berechnet den Gesamtgewinn als Property"""
        return self.total_discharge_revenue - self.total_charge_cost

    # Property für cycles_completed (für Kompatibilität mit bestehendem Code)
    @property
    def cycles_completed(self):
        """Gibt die Anzahl der täglichen Zyklen zurück"""
        return self.daily_cycles

    def start_charging(self, price, time_index):
        """Beginnt einen neuen Ladevorgang"""
        if self.is_charging or self.is_discharging:
            return False  # Bereits im Lademodus

        if self.energy_level >= self.capacity:
            return False  # Batterie bereits voll

        self.is_charging = True
        self.charging_price = price
        self.charging_start_index = time_index
        self.current_interval = 0

        # Erste Ladung durchführen
        return self._charge_step(price, time_index)

    def start_discharging(self, price, time_index):
        """Beginnt einen neuen Entladevorgang"""
        if self.is_charging or self.is_discharging:
            return False  # Bereits im Entlademodus

        if self.energy_level <= 0:
            return False  # Batterie bereits leer

        self.is_discharging = True
        self.discharging_price = price
        self.charging_start_index = time_index
        self.current_interval = 0

        # Erste Entladung durchführen
        return self._discharge_step(price, time_index)

    def continue_process(self, time_index):
        """Setzt den laufenden Lade- oder Entladevorgang fort"""
        self.current_interval += 1

        if self.is_charging:
            return self._charge_step(self.charging_price, time_index)
        elif self.is_discharging:
            return self._discharge_step(self.discharging_price, time_index)
        else:
            return False

    def _charge_step(self, price, time_index):
        """Führt einen einzelnen Ladeschritt durch"""
        max_charge = self.max_power * 0.25  # Max. Ladung in 15min
        available_capacity = self.capacity - self.energy_level
        amount = min(max_charge, available_capacity)

        if amount <= 0:
            self.is_charging = False
            return False

        # Kosten mit Gebühr pro MWh
        energy_cost = amount * price
        transaction_fee = amount * self.fee_per_mwh  # Gebühr pro MWh
        cost = energy_cost + transaction_fee

        self.energy_level += amount
        self.cash -= cost

        # Gesamtstatistik aktualisieren
        self.total_charged_energy += amount
        self.total_charge_cost += cost

        # Transaktion protokollieren
        transaction = {
            "type": "charge",
            "amount": amount,
            "price": price,
            "energy_cost": energy_cost,
            "transaction_fee": transaction_fee,
            "cost": cost,
            "energy_level": self.energy_level,
            "index": time_index,
            "interval": self.current_interval,
        }

        self.transactions.append(transaction)
        return True

    def _discharge_step(self, price, time_index):
        """Führt einen einzelnen Entladeschritt durch"""
        max_discharge = self.max_power * 0.25  # Max. Entladung in 15min
        amount = min(max_discharge, self.energy_level)

        if amount <= 0:
            self.is_discharging = False
            return False

        # Berechnung der tatsächlich nutzbaren Energie nach Effizienzverlusten
        gross_energy = amount  # Brutto-Energie, die aus dem Speicher entnommen wird
        usable_energy = (
            amount * self.efficiency
        )  # Netto-Energie nach Effizienzverlusten
        energy_loss = amount * (
            1 - self.efficiency
        )  # Energieverlust durch Effizienz in MWh

        # Erlös mit Gebühr pro MWh
        gross_revenue = amount * price  # Theoretischer Erlös ohne Effizienzverluste
        efficiency_loss = gross_revenue * (
            1 - self.efficiency
        )  # Finanzieller Verlust durch Effizienz
        energy_revenue = usable_energy * price  # Effektiver Erlös nach Effizienz
        transaction_fee = usable_energy * self.fee_per_mwh  # Gebühr pro MWh
        revenue = energy_revenue - transaction_fee

        self.energy_level -= amount
        self.cash += revenue

        # Gesamtstatistik aktualisieren
        self.total_gross_energy += gross_energy  # Gesamte Brutto-Energie
        self.total_discharged_energy += usable_energy  # Gesamte nutzbare Energie
        self.total_discharge_revenue += revenue

        # Effizienz-Statistik aktualisieren
        self.gross_energy_revenue += gross_revenue
        self.efficiency_losses += efficiency_loss
        self.energy_losses += energy_loss

        # Transaktion protokollieren
        transaction = {
            "type": "discharge",
            "amount_gross": gross_energy,
            "amount_usable": usable_energy,
            "energy_loss": energy_loss,
            "price": price,
            "gross_revenue": gross_revenue,
            "efficiency_loss": efficiency_loss,
            "energy_revenue": energy_revenue,
            "transaction_fee": transaction_fee,
            "revenue": revenue,
            "energy_level": self.energy_level,
            "index": time_index,
            "interval": self.current_interval,
        }

        self.transactions.append(transaction)

        # Zyklen-Zähler aktualisieren (ein vollständiger Zyklus = Entladung einer Kapazitätsmenge)
        cycle_fraction = amount / self.capacity
        self.daily_cycles += cycle_fraction
        self.total_cycles += cycle_fraction

        return True

    def is_processing(self):
        """Prüft, ob der Speicher gerade lädt oder entlädt"""
        return self.is_charging or self.is_discharging

    def get_total_profit(self):
        """Berechnet den Gesamtgewinn"""
        return self.total_discharge_revenue - self.total_charge_cost

    def get_actual_efficiency(self):
        """Berechnet die tatsächliche Effizienz basierend auf Kosten und Erlösen"""
        if self.gross_energy_revenue == 0:
            return 0
        return (
            (self.gross_energy_revenue - self.efficiency_losses)
            / self.gross_energy_revenue
            * 100
        )

    def get_energy_efficiency(self):
        """Berechnet die Energie-Effizienz (nutzbare Energie / eingespeicherte Energie)"""
        if self.total_charged_energy == 0:
            return 0
        return self.total_discharged_energy / self.total_charged_energy * 100

    def reset_daily_transactions(self):
        """Setzt die Transaktionsliste und tägliche Zyklen zurück, behält aber die Gesamtstatistik"""
        self.transactions = []
        self.is_charging = False
        self.is_discharging = False
        self.daily_cycles = 0.0
