import pandas as pd

import solar


def test_solar():
    orientation = 'South'
    roof_height = 2
    roof_width = 7
    postcode = 'DN20 0RG'
    solar_install = solar.Solar(orientation=orientation,
                                roof_width_m=roof_width,
                                roof_height_m=roof_height,
                                postcode=postcode)
    assert solar_install.generation.fuel.name == 'electricity'
    assert solar_install.number_of_panels > 0
    assert solar_install.generation.annual_sum_kwh > 0

    assert solar_install.orientation == orientation
    assert solar_install.generation.fuel.units == "kwh"
    assert solar_install.generation.fuel.name == 'electricity'
    assert isinstance(solar_install.number_of_panels, int)
    assert isinstance(solar_install.peak_capacity_kw_out_per_kw_in_per_m2, float)
    assert isinstance(solar_install.generation.profile_kwh, pd.Series)
    assert isinstance(solar_install.generation.annual_sum_kwh, float)

    # fig = px.line(profile.loc["2020-01-01": "2020-01-03"])
    # fig.show()
    return solar_install


if __name__ == '__main__':

    solar_install_trial = test_solar()
