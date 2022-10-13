from math import floor
from typing import Tuple

import pandas as pd
import numpy as np
import streamlit as st

from constants import SolarConstants
import constants
import usage
import roof


def render_questions() -> "Solar":
    st.header("Your solar potential")

    st.write(
        "Search for your home below and draw a square where you think solar panels might go on your most South"
        "facing roof. Use the hexagonal tool to draw the square.  "
    )
    polygons = roof.roof_mapper(800, 400)

    postcode: str = st.text_input("Postcode:")
    orientation: str = st.selectbox("Solar Orientation", SolarConstants.SOLAR_ORIENTATIONS)

    solar_install = Solar(orientation=orientation, roof_area=polygons.area if polygons else 0, postcode=postcode)
    if polygons:
        st.write(f"We estimate you can fit {solar_install.number_of_panels} on your roof!")

    return solar_install


def render_outputs(solar_install: "Solar"):
    st.header("Solar potential")
    st.write(f"Your roof faces {solar_install.orientation} and could fit  {solar_install.number_of_panels} panels")
    st.write(f"That amounts to {round(solar_install.peak_capacity_kW_out_per_kW_in_per_m2, 1)} kW of peak capacity.")
    st.write(
        f"We estimate that would generate {int(solar_install.generation.annual_sum_kwh):,}  kwh of electricity per year"
    )


class Solar:
    def __init__(self, orientation: str, roof_area: float, postcode: str):

        self.orientation = orientation
        self.number_of_panels = self.get_number_of_panels(roof_area)
        self.peak_capacity_kW_out_per_kW_in_per_m2 = self.get_peak_capacity(
            kWp_per_panel=SolarConstants.KW_PEAK_PER_PANEL
        )
        profile_kwh_per_m2 = self.get_generation_profile(postcode)
        self.generation = usage.Consumption(
            profile_kwh=profile_kwh_per_m2 * self.peak_capacity_kW_out_per_kW_in_per_m2, fuel=constants.ELECTRICITY
        )

    @staticmethod
    def get_number_of_panels(roof_area) -> int:
        usable_area = roof_area * SolarConstants.PERCENT_ROOF_USABLE
        number_of_panels = floor(usable_area / SolarConstants.PANEL_AREA)

        return number_of_panels

    def get_peak_capacity(self, kWp_per_panel: float):
        return self.number_of_panels * kWp_per_panel

    def get_generation_profile(self, postcode: str):
        # TODO properly using orientation and postcode
        print(self.orientation)  # will use this later

        # Stand in for now in absense of proper data
        idx = constants.BASE_YEAR_HALF_HOUR_INDEX
        minute_of_the_day = idx.hour * 60 + idx.minute
        kW_per_m2_peak = 0.3
        generation = -np.cos(minute_of_the_day * np.pi * 2 / (24 * 60)) * kW_per_m2_peak
        profile_kW_per_m2 = pd.Series(index=constants.BASE_YEAR_HALF_HOUR_INDEX, data=generation)
        profile_kW_per_m2.loc[profile_kW_per_m2 < 0] = 0
        profile_kwh_per_m2 = profile_kW_per_m2 / 2  # because we know the time base is half hourly
        # If not importing this from elsewhere think about whether need to integrate (take the previous half hour)

        return profile_kwh_per_m2
