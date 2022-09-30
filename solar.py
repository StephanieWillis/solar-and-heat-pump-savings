from typing import Tuple

import pandas as pd
import numpy as np
import streamlit as st

from constants import SolarConstants, BASE_YEAR_HALF_HOUR_INDEX
import usage


class Solar:

    def __init__(self, orientation: str, roof_height_m: float, roof_width_m: float, postcode: str):

        self.orientation = orientation
        self.number_of_panels = self.get_number_of_panels(roof_width_m, roof_height_m)
        self.peak_capacity_kW_out_per_kW_in_per_m2 = self.get_peak_capacity(kWp_per_panel=SolarConstants.KW_PEAK_PER_PANEL)   # defined as output when incident irradiance = 1kW/m2
        profile_kWh_per_m2 = self.get_generation_profile(postcode)
        self.generation = usage.Consumption(profile=profile_kWh_per_m2 * self.peak_capacity_kW_out_per_kW_in_per_m2,
                                            fuel='electricity',
                                            units='kWh')

    @staticmethod
    def get_number_of_panels(roof_width_m: float, roof_height_m: float) -> float:
        height_available_for_panels = roof_height_m * SolarConstants.PCT_OF_DIMENSION_USABLE
        width_available_for_panels = roof_width_m * SolarConstants.PCT_OF_DIMENSION_USABLE

        number_of_rows = int(height_available_for_panels/SolarConstants.PANEL_HEIGHT_M)
        number_of_columns = int(width_available_for_panels/SolarConstants.PANEL_WIDTH_M)

        number_of_panels = number_of_columns * number_of_rows
        return number_of_panels

    def get_peak_capacity(self, kWp_per_panel: float):
        return self.number_of_panels * kWp_per_panel

    def get_generation_profile(self, postcode: str):
        # TODO properly using orientation and postcode
        print(self.orientation)  # will use this later
        idx = BASE_YEAR_HALF_HOUR_INDEX
        minute_of_the_day = idx.hour * 60 + idx.minute

        kW_per_m2_peak = 0.01
        generation = - np.cos(minute_of_the_day * np.pi * 2/(24 * 60)) * kW_per_m2_peak
        profile_kW_per_m2 = pd.Series(index=BASE_YEAR_HALF_HOUR_INDEX, data=generation)
        profile_kW_per_m2.loc[profile_kW_per_m2 < 0] = 0
        profile_kWh_per_m2 = profile_kW_per_m2/2  # because we know the time base is half hourly
        # If not importing this from elsewhere think about whether need to integrate (take the previous half hour)

        return profile_kWh_per_m2


def render() -> Solar:
    st.subheader("Your solar potential")

    postcode: str = st.text_input("Postcode:")
    orientation: str = st.selectbox('Solar Orientation', SolarConstants.SOLAR_ORIENTATIONS)
    roof_height = st.number_input(label='Roof height (m)', min_value=0, max_value=10, value=2)
    roof_width = st.number_input(label='Roof width (m)', min_value=0, max_value=20, value = 8)

    solar_install = Solar(orientation=orientation, roof_width_m=roof_width, roof_height_m=roof_height,
                          postcode=postcode)

    st.write(f'Your roof faces {solar_install.orientation} and could fit  {solar_install.number_of_panels}')
    st.write(f'That amounts to {solar_install.peak_capacity_kW_out_per_kW_in_per_m2} kW of peak capacity.')
    st.write(f'We estimate that would generate {int(solar_install.generation.annual_sum):,}  kWh of electricity per year')
    return solar_install




