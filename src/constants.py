from dataclasses import dataclass

import pandas as pd

HOUSE_TYPES = ["Terrace", "Semi-detached", "Detached", "Flat"]

BASE_YEAR_HALF_HOUR_INDEX = pd.date_range(start="2020-01-01", end="2021-01-01", freq="30T")
EMPTY_TIMESERIES = pd.Series(index=BASE_YEAR_HALF_HOUR_INDEX, data=0)


@dataclass
class Fuel:
    name: str
    units: str = "kwh"
    converter_consumption_units_to_kwh: float = 1

    def convert_kwh_to_fuel_units(self, value_kwh: [float | pd.Series | pd.DataFrame]):
        value_fuel_units = value_kwh / self.converter_consumption_units_to_kwh
        return value_fuel_units

    def convert_fuel_units_to_kwh(self, value_fuel_units: [float | pd.Series | pd.DataFrame]):
        value_kwh = value_fuel_units * self.converter_consumption_units_to_kwh
        return value_kwh


kwh_PER_LITRE_OF_OIL = 10.35
# https://www.thegreenage.co.uk/is-heating-oil-a-cheap-way-to-heat-my-home/
ELECTRICITY = Fuel("electricity")
GAS = Fuel(name="gas")
OIL = Fuel(name="oil", units="litres", converter_consumption_units_to_kwh=kwh_PER_LITRE_OF_OIL)
FUELS = [ELECTRICITY, GAS, OIL]


@dataclass
class HeatingConstants:
    space_heating_efficiency: float
    water_heating_efficiency: float
    fuel: Fuel


DEFAULT_HEATING_CONSTANTS = {
    "Gas boiler": HeatingConstants(space_heating_efficiency=0.85, water_heating_efficiency=0.8, fuel=GAS),
    "Oil boiler": HeatingConstants(space_heating_efficiency=0.8, water_heating_efficiency=0.75, fuel=OIL),
    "Direct electric": HeatingConstants(space_heating_efficiency=1.0, water_heating_efficiency=1.0, fuel=ELECTRICITY),
    "Heat pump": HeatingConstants(space_heating_efficiency=3.5, water_heating_efficiency=3.0, fuel=ELECTRICITY),
}


@dataclass
class TariffConstants:
    p_per_kwh_gas: float
    p_per_kwh_elec: float
    p_per_day_gas: float
    p_per_day_elec: float
    p_per_L_oil: float


STANDARD_TARIFF = TariffConstants(
    p_per_kwh_gas=10.3, p_per_kwh_elec=34.0, p_per_day_gas=28.0, p_per_day_elec=46.0, p_per_L_oil=95.0
)


class SolarConstants:
    SOLAR_ORIENTATIONS = ["South", "Southwest", "West", "Northwest", "North", "Northeast", "East", "Southeast"]
    MIN_ROOF_AREA = 0
    MAX_ROOF_AREA = 20
    DEFAULT_ROOF_AREA = 20
    PANEL_HEIGHT_M = 1.9
    PANEL_WIDTH_M = 1.0
    PANEL_AREA = PANEL_HEIGHT_M * PANEL_WIDTH_M
    KW_PEAK_PER_PANEL = 0.35  # output with incident radiation of 1kW/m2
    # Panel dimensions and kW_peak from https://www.greenmatch.co.uk/blog/how-many-solar-panels-do-i-need
    PCT_OF_DIMENSION_USABLE = 0.9  # a guess
    PERCENT_ROOF_USABLE = 0.8  # complete guess
