import solar

import plotly.express as px


def test_solar():
    orientation = 'South'
    roof_area_m2 = 30
    postcode = 'DN20 0RG'
    solar_install = solar.Solar(orientation=orientation, roof_area_m2=roof_area_m2, postcode=postcode)
    profile = solar_install.generation.profile

    assert solar_install.orientation == orientation
    assert solar_install.area_m2 == roof_area_m2 * 0.7  # TODO store this somewhere
    assert solar_install.generation.units == "kWh"
    assert solar_install.generation.fuel == 'electricity'

    fig = px.line(profile.loc["2020-01-01": "2020-01-03"])
    fig.show()
    return solar_install


if __name__ == '__main__':

    solar_install_trial = test_solar()

