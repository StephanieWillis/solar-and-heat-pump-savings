import pandas as pd

import solar
import roof

import plotly.express as px


def test_solar():
    orientation = 'South'
    roof_height = 2
    roof_width = 7
    postcode = 'DN20 0RG'
    solar_install = solar.Solar(orientation=orientation,
                                roof_width_m=roof_width,
                                roof_height_m=roof_height,
                                postcode=postcode)
    profile = solar_install.generation.profile

    assert solar_install.orientation == orientation
    assert solar_install.generation.fuel.units == "kWh"
    assert solar_install.generation.fuel.name == 'electricity'
    assert isinstance(solar_install.number_of_panels, int)
    assert isinstance(solar_install.peak_capacity_kW_out_per_kW_in_per_m2, float)
    assert isinstance(solar_install.generation.profile, pd.Series)
    assert isinstance(solar_install.generation.annual_sum, float)

    polygons = roof.roof_mapper(800, 400)

    # fig = px.line(profile.loc["2020-01-01": "2020-01-03"])
    # fig.show()
    return solar_install


if __name__ == '__main__':

    solar_install_trial = test_solar()

