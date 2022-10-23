from math import floor

import numpy as np
import pandas as pd
import requests

import constants
from consumption import Consumption
from constants import SolarConstants


class Solar:

    def __init__(self, orientation: str, roof_plan_area: float):
        """ Roof plan area because based on lat long therefore doesn't account for roof pitch"""

        self.orientation = orientation
        self.profile_kwh_per_m2 = self.get_generation_profile()

        self.number_of_panels = self.get_number_of_panels(roof_plan_area)
        self.kwp_per_panel = SolarConstants.KW_PEAK_PER_PANEL

    @staticmethod
    def get_number_of_panels(roof_plan_area: float) -> int:
        roof_area = roof_plan_area / np.cos(np.radians(SolarConstants.ROOF_PITCH_DEGREES))
        usable_area = roof_area * SolarConstants.PERCENT_SQUARE_USABLE
        number_of_panels = floor(usable_area / SolarConstants.PANEL_AREA)

        return number_of_panels

    @staticmethod
    def get_generation_profile():
        # TODO properly using orientation and location

        # Stand in for now in absense of proper data
        idx = constants.BASE_YEAR_HALF_HOUR_INDEX
        minute_of_the_day = idx.hour * 60 + idx.minute
        kw_per_m2_peak = 0.3
        generation = - np.cos(minute_of_the_day * np.pi * 2 / (24 * 60)) * kw_per_m2_peak
        profile_kw_per_m2 = pd.Series(index=constants.BASE_YEAR_HALF_HOUR_INDEX, data=generation)
        profile_kw_per_m2.loc[profile_kw_per_m2 < 0] = 0
        profile_kwh_per_m2 = profile_kw_per_m2 / 2  # because we know the time base is half hourly
        return profile_kwh_per_m2

    @property
    def peak_capacity_kw_out_per_kw_in_per_m2(self):
        return self.number_of_panels * self.kwp_per_panel

    @property
    def generation(self):
        # set negative as generation not consumption
        profile_kwh = -1 * self.profile_kwh_per_m2 * self.peak_capacity_kw_out_per_kw_in_per_m2
        generation = Consumption(profile_kwh=profile_kwh, fuel=constants.ELECTRICITY)
        return generation


def get_hourly_radiation_from_eu_api(lat: float, lon: float, peak_capacity_kw_out_per_kw_in_per_m2: float,
                                     pitch: float, azimuth: float) -> pd.Series:
    """ Returns series of 8760 of average solar pv power for that hour in kW. Index 0 to 8759"""

    tool_name = 'seriescalc'
    api_url = f'https://re.jrc.ec.europa.eu/api/v5_2/{tool_name}'

    params = {'lat': lat,  # Latitude, in decimal degrees, south is negative
              'lon': lon,  # Longitude, in decimal degrees, west is negative.
              'startyear': 2015,  # just take one year for now
              'endyear': 2015,  # defaults here are first and last year they have data for
              'pvcalculation': 1,  # estimate hourly PV production
              'peakpower': peak_capacity_kw_out_per_kw_in_per_m2,  # installed capacity
              'mountingplace': "building",
              'loss': 14,  # percentage loss in the system - the PVGIS documentation suggests 14 %
              'angle': pitch,
              'aspect': azimuth,
              'outputformat': "json"
              }
    response = requests.get(api_url, params=params)

    if response.status_code == 200:
        dictr = response.json()
        df = pd.DataFrame(dictr['outputs']['hourly'])
        pv_power_kw = df['P'] / 1000  # source data in W so convert to kW
    else:
        print(response.status_code)
        print(response.text)
        raise requests.ConnectionError

    return pv_power_kw


