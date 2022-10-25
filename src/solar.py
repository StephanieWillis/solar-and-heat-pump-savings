from functools import cache
from math import floor

import numpy as np
import pandas as pd
import requests

import constants
from consumption import Consumption
from constants import SolarConstants, Orientation


class Solar:

    def __init__(self, orientation: Orientation, roof_plan_area: float,
                 latitude: float = SolarConstants.DEFAULT_LAT, longitude: float = SolarConstants.DEFAULT_LONG,
                 pitch: float = SolarConstants.ROOF_PITCH_DEGREES):
        """ Roof plan area because based on lat long therefore doesn't account for roof pitch"""

        self.orientation = orientation
        self.latitude = latitude  # Latitude, in decimal degrees, south is negative
        self.longitude = longitude  # Longitude, in decimal degrees, west is negative
        self.pitch = pitch
        self.roof_area = roof_plan_area / np.cos(np.radians(self.pitch))

        self.number_of_panels = self.get_number_of_panels()  # not a property because want to be able to overwrite
        self.kwp_per_panel = SolarConstants.KW_PEAK_PER_PANEL

    def __hash__(self):
        return hash((self.orientation.azimuth_degrees, self.latitude, self.longitude, self.pitch, self.number_of_panels))

    def __eq__(self, other: 'Solar'):
        result = (isinstance(other, 'Solar')
                  and self.orientation.azimuth_degrees == other.orientation.azimuth_degrees
                  and self.latitude == other.latitude
                  and self.longitude == other.longitude
                  and self.pitch == other.pitch
                  and self.number_of_panels == other.number_of_panels
                  )
        return result

    def get_number_of_panels(self) -> int:
        """ Very simplified assumption here that you can use fixed proportion of area because hard to do properly"""
        usable_area = self.roof_area * SolarConstants.PERCENT_SQUARE_USABLE
        number_of_panels = floor(usable_area / SolarConstants.PANEL_AREA)
        return number_of_panels

    @property
    def peak_capacity_kw_out_per_kw_in_per_m2(self):
        """ The nominal output capacity of the system when there is 1kW/m2 of irradiance on the panel"""
        return self.number_of_panels * self.kwp_per_panel

    @property
    def generation(self):
        if self.peak_capacity_kw_out_per_kw_in_per_m2 > 0:
            profile_kwh = self.get_hourly_radiation_from_eu_api()
            profile_kwh.index = constants.BASE_YEAR_HOURLY_INDEX
        else:
            profile_kwh = pd.Series(index=constants.BASE_YEAR_HOURLY_INDEX, data=0)
        # set negative as generation not consumption
        profile_kwh_negative = profile_kwh * -1
        generation = Consumption(hourly_profile_kwh=profile_kwh_negative, fuel=constants.ELECTRICITY)
        return generation

    @cache
    def get_hourly_radiation_from_eu_api(self) -> pd.Series:
        """ Returns series of 8760 of average solar pv power for that hour in kW. Index 0 to 8759"""
        # API Documentation here: https://joint-research-centre.ec.europa.eu/
        #   pvgis-photovoltaic-geographical-information-system/getting-started-pvgis/api-non-interactive-service_en
        # Limit of 30 calls per second

        tool_name = 'seriescalc'
        api_url = f'https://re.jrc.ec.europa.eu/api/v5_2/{tool_name}'

        params = {'lat': self.latitude,
                  'lon': self.longitude,
                  'startyear': SolarConstants.API_YEAR,  # just take one year for now
                  'endyear': SolarConstants.API_YEAR,
                  'pvcalculation': 1,  # estimate hourly PV production
                  'peakpower': self.peak_capacity_kw_out_per_kw_in_per_m2,  # installed capacity
                  'mountingplace': "building",
                  'loss': SolarConstants.SYSTEM_LOSS,
                  'angle': self.pitch,
                  'aspect': self.orientation.azimuth_degrees,
                  'outputformat': "json"
                  }
        print("making api call")
        response = requests.get(api_url, params=params)

        if response.status_code == 200:
            dictr = response.json()
            df = pd.DataFrame(dictr['outputs']['hourly'])
            # can add timeseries as index later if needed
            pv_power_kw = df['P'] / 1000  # source data in W so convert to kW
            pv_power_kw.index = constants.BASE_YEAR_HOURLY_INDEX
        else:
            print(response.status_code)
            print(response.text)
            raise requests.ConnectionError

        return pv_power_kw
