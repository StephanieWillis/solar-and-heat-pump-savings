from dataclasses import dataclass

import pandas as pd

from fuels import Fuel

# Use same year as solar year
BASE_YEAR_HOURLY_INDEX = pd.date_range(start="2013-01-01", end="2014-01-01", freq="1H", inclusive="left")
EMPTY_TIMESERIES = pd.Series(index=BASE_YEAR_HOURLY_INDEX, data=0)

# class here on house type?
BASE_ELECTRICITY_DEMAND_BY_HOUSE_TYPE = {}

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
class BuildingTypeConstants:
    name: str
    annual_base_electricity_demand_kWh: float
    base_electricity_demand_profile_kWh: pd.Series
    annual_heat_demand_kWh: float


HEATING_DEMAND_BY_HOUSE_TYPE = {"Terrace": 9900,  # order here defines dropdown order and default, so most common first
                                "Semi-detached": 10600,
                                "Flat": 6600,
                                "Detached": 14000}
NORMALIZED_HOURLY_BASE_DEMAND: pd.Series = pd.read_pickle('../src/hourly_base_electricity_demand_profiles_2013.pkl')
# based on elexon profiling data https://www.elexon.co.uk/operations-settlement/profiling/
# data processing done in data_exploration_and_prep folder

# Decide whether to add floor area or not? < get issue with adjusting space heating demand and then what you do
BUILDING_TYPE_OPTIONS = {
    "Terrace": BuildingTypeConstants(
        name="Terrace",
        annual_base_electricity_demand_kWh=2890,  # used value for terrace - small up to 70m2
        base_electricity_demand_profile_kWh=NORMALIZED_HOURLY_BASE_DEMAND,
        annual_heat_demand_kWh=9900),  # order here defines dropdown order and default, so most common first
    "Semi-detached": BuildingTypeConstants(
        name="Semi-detached",
        annual_base_electricity_demand_kWh=3850,
        base_electricity_demand_profile_kWh=NORMALIZED_HOURLY_BASE_DEMAND,
        annual_heat_demand_kWh=10600),
    "Flat": BuildingTypeConstants(
        name="Semi-detached",
        annual_base_electricity_demand_kWh=2830,
        base_electricity_demand_profile_kWh=NORMALIZED_HOURLY_BASE_DEMAND,
        annual_heat_demand_kWh=6600),
    "Detached": BuildingTypeConstants(
        name="Detached",
        annual_base_electricity_demand_kWh=4150,
        base_electricity_demand_profile_kWh=NORMALIZED_HOURLY_BASE_DEMAND,
        annual_heat_demand_kWh=14000)
}
# Annual base electricity demand numbers based on data from
# https://www.energysavingtrust.org.uk/sites/default/files/reports/PoweringthenationreportCO332.pdf
# Annual heat demand numbers based on data from https://ukerc.rl.ac.uk/DC/cgi-bin/edc_search.pl?WantComp=165
# data processing done in data_exploration_and_prep folder


@dataclass
class HeatingConstants:
    efficiency: float
    fuel: Fuel
    normalized_hourly_heat_demand_profile: pd.Series
    #  Not splitting space and water heating because hourly demand profiles are combined


NORMALIZED_HOURLY_HEAT_DEMAND_DF: pd.DataFrame = pd.read_pickle('../src/hourly_heating_demand_profiles_2013.pkl')
# based on data from https://ukerc.rl.ac.uk/DC/cgi-bin/edc_search.pl?WantComp=165
# processed in data_exploration_and_prep

DEFAULT_HEATING_CONSTANTS = {
    "Gas boiler": HeatingConstants(
        efficiency=0.84,
        fuel=GAS,
        normalized_hourly_heat_demand_profile=NORMALIZED_HOURLY_HEAT_DEMAND_DF['Normalised_Gas_boiler_heat']),
    "Oil boiler": HeatingConstants(
        efficiency=0.84,
        fuel=OIL,
        normalized_hourly_heat_demand_profile=NORMALIZED_HOURLY_HEAT_DEMAND_DF['Normalised_Gas_boiler_heat']),
    "Direct electric": HeatingConstants(
        efficiency=1.0,
        fuel=ELECTRICITY,
        normalized_hourly_heat_demand_profile=NORMALIZED_HOURLY_HEAT_DEMAND_DF[
            'Normalised_Resistance_heater_heat']),
    "Heat pump": HeatingConstants(
        efficiency=3.0,
        fuel=ELECTRICITY,
        normalized_hourly_heat_demand_profile=NORMALIZED_HOURLY_HEAT_DEMAND_DF['Normalised_ASHP_heat']),
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
    p_per_kwh_gas=10.3, p_per_kwh_elec_import=34.0, p_per_kwh_elec_export=15.0,
    p_per_L_oil=95.0, p_per_day_gas=28.0, p_per_day_elec=46.0)


@dataclass()
class Orientation:
    """ Azimuth is degrees clockwise from South, max absolute value of 180"""
    azimuth_degrees: float

    # https://re.jrc.ec.europa.eu/pvg_tools/en/

    def __post_init__(self):
        if self.azimuth_degrees > 180:
            self.azimuth_degrees += -360
        elif self.azimuth_degrees <= -180:
            self.azimuth_degrees += 360


ORIENTATION_OPTIONS = {
    'South': Orientation(0),
    'Southwest': Orientation(45),
    'West': Orientation(90),
    'Northwest': Orientation(135),
    'North': Orientation(180),
    'Northeast': Orientation(-45),
    'East': Orientation(-90),
    'Southeast': Orientation(-135)}


class SolarConstants:
    ORIENTATIONS = ORIENTATION_OPTIONS
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
    API_YEAR = 2013
    # Was 202 Based on quick comparison of years for one location in the uk.
    # If you don't pass years to the API it gives you all hours from first to last year they have data for.
    SYSTEM_LOSS = 14  # percentage loss in the system - the PVGIS documentation suggests 14 %
