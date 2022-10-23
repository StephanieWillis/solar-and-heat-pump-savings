from math import floor

import numpy as np
import pandas as pd

import constants
from building_model import Consumption
from constants import SolarConstants

API_end_point = 'https://re.jrc.ec.europa.eu/api/v5_2/tool_name?param1=value1&param2=value2&...'


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
