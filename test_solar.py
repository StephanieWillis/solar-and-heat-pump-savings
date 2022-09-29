import solar

import plotly.express as px


def test_solar():
    orientation = 'South'
    roof_area_m2 = 30
    postcode = 'DN20 0RG'
    solar_install = solar.Solar(orientation=orientation, roof_area_m2=roof_area_m2, postcode=postcode)
    fig = px.line(solar_install.profile)
    fig.show()
    return solar_install


if __name__ == '__main__':

    solar_install_trial = test_solar()

