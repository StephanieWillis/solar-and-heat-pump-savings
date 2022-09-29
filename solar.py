from typing import Tuple

import pandas as pd
import numpy as np
import streamlit as st

import constants
import usage


def render() -> Tuple[bool, float]:
    st.subheader("Your solar potential")

    postcode: str = st.text_input("Postcode:")
    orientation: bool = st.selectbox('Solar Orientation',
                                           ['south', 'southwest', 'west', 'northwest',
                                            'North', 'northeast', 'east', 'southeast'])
    roof_area_m2 = st.number_input(label='roof_area', min_value=0, max_value=20, value=20)

    solar = Solar(orientation=orientation, roof_area_m2=roof_area_m2, postcode=postcode)

    st.write(f'Your roof faces {solar.orientation} and has an area of  {roof_area_m2} m\u00b2')
    st.write(f'That means you have  {solar.area_m2} available for solar, which amounts to {roof_area_m2} m\u00b2')
    return solar


class Solar:

    def __init__(self, orientation: str, roof_area_m2: float, postcode: str):

        self.orientation = orientation
        self.area_m2 = roof_area_m2 * 0.7  # hack until archy has the boxes working
        self.capacity = self.area_m2
        profile_kWh_per_m2 = self.get_generation_profile(postcode)
        self.generation = usage.Demand(profile=profile_kWh_per_m2 * self.area_m2, units='kWh')

    def get_capacity(self):
        NotImplemented

    def get_generation_profile(self, postcode: str):
        # TODO properly using orientation and postcode
        print(self.orientation)  # will use this later
        idx = constants.BASE_YEAR_HALF_HOUR_INDEX
        minute_of_the_day = idx.hour * 60 + idx.minute

        kW_per_m2_peak = 0.6
        generation = - np.cos(minute_of_the_day * np.pi * 2/(24 * 60)) * kW_per_m2_peak
        profile_kW_per_m2 = pd.Series(index=constants.BASE_YEAR_HALF_HOUR_INDEX, data=generation)
        profile_kW_per_m2.loc[profile_kW_per_m2 < 0] = 0
        profile_kWh_per_m2 = profile_kW_per_m2/2  # because we know the time base is half hourly
        # If not importing this from elsewhere think about whether need to integrate (take the previous half hour)

        return profile_kWh_per_m2






