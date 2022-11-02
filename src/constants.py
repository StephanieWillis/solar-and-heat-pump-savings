from dataclasses import dataclass

import pandas as pd

from fuels import Fuel

HOUSE_TYPES = ["Terrace", "Semi-detached", "Detached", "Flat"]
DEFAULT_FLOOR_AREA = 80

# Use same year as solar year
BASE_YEAR_HOURLY_INDEX = pd.date_range(start="2020-01-01", end="2021-01-01", freq="1H", inclusive="left")
EMPTY_TIMESERIES = pd.Series(index=BASE_YEAR_HOURLY_INDEX, data=0)

KWH_PER_LITRE_OF_OIL = 10.35  # https://www.thegreenage.co.uk/is-heating-oil-a-cheap-way-to-heat-my-home/

ELEC_TCO2_PER_KWH = 186 / 10 ** 6
ELECTRICITY = Fuel("electricity", tco2_per_kwh=ELEC_TCO2_PER_KWH)
GAS_TCO2_PER_KWH = 202 / 10 ** 6
GAS = Fuel(name="gas", tco2_per_kwh=GAS_TCO2_PER_KWH)
OIL_TCO2_PER_KWH = 260 / 10 ** 6
OIL = Fuel(name="oil", units="litres", converter_consumption_units_to_kwh=KWH_PER_LITRE_OF_OIL,
           tco2_per_kwh=OIL_TCO2_PER_KWH)
FUELS = [ELECTRICITY, GAS, OIL]


@dataclass
class HeatingConstants:
    space_heating_efficiency: float
    water_heating_efficiency: float
    fuel: Fuel


DEFAULT_HEATING_CONSTANTS = {
    "Gas boiler": HeatingConstants(space_heating_efficiency=0.85, water_heating_efficiency=0.8, fuel=GAS),
    "Oil boiler": HeatingConstants(space_heating_efficiency=0.85, water_heating_efficiency=0.8, fuel=OIL),
    "Direct electric": HeatingConstants(space_heating_efficiency=1.0, water_heating_efficiency=1.0, fuel=ELECTRICITY),
    "Heat pump": HeatingConstants(space_heating_efficiency=3.4, water_heating_efficiency=3.0, fuel=ELECTRICITY),
}


@dataclass
class TariffConstants:
    p_per_kwh_gas: float
    p_per_kwh_elec_import: float
    p_per_kwh_elec_export: float
    p_per_L_oil: float
    p_per_day_gas: float
    p_per_day_elec: float


STANDARD_TARIFF = TariffConstants(
    p_per_kwh_gas=10.3, p_per_kwh_elec_import=34.0, p_per_kwh_elec_export=15.0, p_per_L_oil=95.0,
    p_per_day_gas=28.0, p_per_day_elec=46.0
)


@dataclass()
class Orientation:
    """ Azimuth is degrees clockwise from South, max absolute value of 180
    Defined like this to be consistent with  https://re.jrc.ec.europa.eu/pvg_tools/en/"""
    azimuth_degrees: float
    name: str

    def __post_init__(self):
        if self.azimuth_degrees > 180:
            self.azimuth_degrees += -360
        elif self.azimuth_degrees <= -180:
            self.azimuth_degrees += 360


OrientationOptions = {
    'South': Orientation(azimuth_degrees=0, name='South'),
    'Southwest': Orientation(azimuth_degrees=45, name='Southwest'),
    'West': Orientation(azimuth_degrees=90, name='West'),
    'Northwest': Orientation(azimuth_degrees=135, name='Northwest'),
    'North': Orientation(azimuth_degrees=180, name='North'),
    'Northeast': Orientation(azimuth_degrees=-45, name='Northeast'),
    'East': Orientation(azimuth_degrees=-90, name='East'),
    'Southeast': Orientation(azimuth_degrees=-135, name='Southeast')}


class SolarConstants:
    ORIENTATIONS = OrientationOptions
    DEFAULT_LAT = 51.509865
    DEFAULT_LONG = -0.118092
    MIN_ROOF_AREA = 0
    MAX_ROOF_AREA = 20
    DEFAULT_ROOF_AREA = 20
    ROOF_PITCH_DEGREES = 30
    PANEL_HEIGHT_M = 1.67
    PANEL_WIDTH_M = 1.0
    PANEL_AREA = PANEL_HEIGHT_M * PANEL_WIDTH_M
    KW_PEAK_PER_PANEL = 0.30  # output with incident radiation of 1kW/m2
    # Panel dimensions and kW_peak from https://www.greenmatch.co.uk/blog/how-many-solar-panels-do-i-need
    PERCENT_SQUARE_USABLE = 0.8  # complete guess
    API_YEAR = 2020  # Based on quick comparison of years for one location in the uk.
    # If you don't pass years to the API it gives you all hours from first to last year they have data for.
    SYSTEM_LOSS = 14  # percentage loss in the system - the PVGIS documentation suggests 14 %

