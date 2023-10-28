from dataclasses import dataclass

import pandas as pd
from pathlib import Path

from fuels import Fuel

THIS_FILE = Path(__file__)

# Use same year as solar year
BASE_YEAR_HOURLY_INDEX = pd.date_range(start="2013-01-01", end="2014-01-01", freq="1H", inclusive="left")
EMPTY_TIMESERIES = pd.Series(index=BASE_YEAR_HOURLY_INDEX, data=0)

ELEC_TCO2_PER_KWH = 186 / 10 ** 6
ELECTRICITY = Fuel("electricity", tco2_per_kwh=ELEC_TCO2_PER_KWH)
GAS_TCO2_PER_KWH = 202 / 10 ** 6
GAS = Fuel(name="gas", tco2_per_kwh=GAS_TCO2_PER_KWH)
OIL_TCO2_PER_KWH = 260 / 10 ** 6
KWH_PER_LITRE_OF_OIL = 10.35  # https://www.thegreenage.co.uk/is-heating-oil-a-cheap-way-to-heat-my-home/
OIL = Fuel(name="oil", units="litres", converter_consumption_units_to_kwh=KWH_PER_LITRE_OF_OIL,
           tco2_per_kwh=OIL_TCO2_PER_KWH)
FUELS = [ELECTRICITY, GAS, OIL]


@dataclass
class BuildingTypeConstants:
    name: str
    annual_base_electricity_demand_kWh: float
    normalized_base_electricity_demand_profile_kWh: pd.Series
    annual_heat_demand_kWh: float


elec_path = Path(THIS_FILE.parent.parent / 'data/normalized_hourly_base_electricity_demand_profile_2013.pkl')
NORMALIZED_HOURLY_BASE_DEMAND: pd.Series = pd.read_pickle(elec_path)
# Based on elexon profiling data https://www.elexon.co.uk/operations-settlement/profiling/
# Data processing done in data_exploration_and_prep folder

# Decide whether to add floor area or not? < get issue with adjusting space heating demand and then what you do
BUILDING_TYPE_OPTIONS = {
    "Terrace": BuildingTypeConstants(
        name="Terrace",
        annual_base_electricity_demand_kWh=2890,  # used value for terrace - small up to 70m2
        normalized_base_electricity_demand_profile_kWh=NORMALIZED_HOURLY_BASE_DEMAND,
        annual_heat_demand_kWh=9900),  # order here defines dropdown order and default, so most common first
    "Semi-detached": BuildingTypeConstants(
        name="Semi-detached",
        annual_base_electricity_demand_kWh=3850,
        normalized_base_electricity_demand_profile_kWh=NORMALIZED_HOURLY_BASE_DEMAND,
        annual_heat_demand_kWh=10600),
    "Flat": BuildingTypeConstants(
        name="Flat",
        annual_base_electricity_demand_kWh=2830,
        normalized_base_electricity_demand_profile_kWh=NORMALIZED_HOURLY_BASE_DEMAND,
        annual_heat_demand_kWh=6600),
    "Detached": BuildingTypeConstants(
        name="Detached",
        annual_base_electricity_demand_kWh=4150,
        normalized_base_electricity_demand_profile_kWh=NORMALIZED_HOURLY_BASE_DEMAND,
        annual_heat_demand_kWh=14000)
}


# Annual base electricity demand numbers based on data from
# https://www.energysavingtrust.org.uk/sites/default/files/reports/PoweringthenationreportCO332.pdf
# Annual heat demand numbers based on data from https://ukerc.rl.ac.uk/DC/cgi-bin/edc_search.pl?WantComp=165
# Data processing done in data_exploration_and_prep folder


@dataclass
class HeatingConstants:
    efficiency: float
    fuel: Fuel
    normalized_hourly_heat_demand_profile: pd.Series
    #  Not splitting space and water heating because hourly demand profiles are combined


heat_path = Path(THIS_FILE.parent.parent / 'data/hourly_heating_demand_profiles_2013.pkl')
NORMALIZED_HOURLY_HEAT_DEMAND_DF: pd.DataFrame = pd.read_pickle(heat_path)
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

RPI_ratio_oct_21_to_sept_23 = 378.4/312.0
HEAT_PUMP_COSTS = {"Terrace": 10000 * RPI_ratio_oct_21_to_sept_23,
                   "Semi-detached": 11100 * RPI_ratio_oct_21_to_sept_23,
                   "Flat": 9100 * RPI_ratio_oct_21_to_sept_23,
                   "Detached": 13100 * RPI_ratio_oct_21_to_sept_23}
GAS_BOILER_COSTS = {"Terrace": 1800 * 10000 / 11100 * RPI_ratio_oct_21_to_sept_23,
                    "Semi-detached": 1800 * RPI_ratio_oct_21_to_sept_23,
                    "Flat": 1500 * RPI_ratio_oct_21_to_sept_23,
                    "Detached": 2200 * RPI_ratio_oct_21_to_sept_23}
HEATING_SYSTEM_COSTS = {"Gas boiler": GAS_BOILER_COSTS,
                        "Heat pump": HEAT_PUMP_COSTS,
                        "Oil boiler": GAS_BOILER_COSTS,  # assume they are the same
                        "Direct electric": GAS_BOILER_COSTS
                        }
HEATING_SYSTEM_GRANTS = {"Gas boiler": 0,
                         "Heat pump": 7500,  # Boiler upgrade scheme,
                         "Oil boiler": 0,
                         "Direct electric": 0
                         }
HEATING_SYSTEM_LIFETIME = 20


# TODO: reference nesta tool: http://asf-hp-cost-demo-l-b-1046547218.eu-west-1.elb.amazonaws.com


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
    """ Azimuth is degrees clockwise from South, max absolute value of 180
    Defined like this to be consistent with  https://re.jrc.ec.europa.eu/pvg_tools/en/"""
    azimuth_degrees: float
    name: str

    def __post_init__(self):
        if self.azimuth_degrees > 180:
            self.azimuth_degrees += -360
        elif self.azimuth_degrees <= -180:
            self.azimuth_degrees += 360


ORIENTATION_OPTIONS = {
    'South': Orientation(azimuth_degrees=0, name='South'),
    'Southwest': Orientation(azimuth_degrees=45, name='Southwest'),
    'West': Orientation(azimuth_degrees=90, name='West'),
    'Northwest': Orientation(azimuth_degrees=135, name='Northwest'),
    'North': Orientation(azimuth_degrees=180, name='North'),
    'Northeast': Orientation(azimuth_degrees=-135, name='Northeast'),
    'East': Orientation(azimuth_degrees=-90, name='East'),
    'Southeast': Orientation(azimuth_degrees=-45, name='Southeast')}


class SolarConstants:
    ORIENTATIONS = ORIENTATION_OPTIONS
    DEFAULT_LAT = 51.509865
    DEFAULT_LONG = -0.118092

    ROOF_PITCH_DEGREES = 30
    # Specs for this panel: https://midsummerwholesale.co.uk/buy/longi-solar/longi-lr5hib-400w
    PANEL_HEIGHT_M = 1.722
    PANEL_WIDTH_M = 1.134
    SMALL_PANEL_BORDER_M = 0.6  # gap to leave at side of roof (so 30cm each side)
    BIG_PANEL_BORDER_M = 0.8  # gap to leave at side of roof for bigger roofs (so 40cm each side)
    PANEL_AREA = PANEL_HEIGHT_M * PANEL_WIDTH_M
    KW_PEAK_PER_PANEL = 0.400  # output with incident radiation of 1kW/m2
    # Panel dimensions and kW_peak from https://www.greenmatch.co.uk/blog/how-many-solar-panels-do-i-need
    COST_PER_KWP_LESS_THAN_4_KW = 1883
    COST_PER_KWP_MORE_THAN_4_KW = 1616
    LIFETIME = 25

    PERCENT_SQUARE_USABLE = 0.8  # complete guess - only used when shape drawn isn't rectangular

    API_YEAR = 2013
    # Was 202 Based on quick comparison of years for one location in the uk.
    # If you don't pass years to the API it gives you all hours from first to last year they have data for.
    SYSTEM_LOSS = 14  # percentage loss in the system - the PVGIS documentation suggests 14 %


CLASS_NAME_OF_SIDEBAR_DIV = "\"css-1f8pn94 edgvbvh3\""

# Based on 2020/2021 data residential size solar PV installations cost about £1700 per kW.
