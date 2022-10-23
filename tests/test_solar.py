import pandas as pd
import plotly.express as px
import numpy as np

import solar


def test_get_number_of_panels():
    orientation = 'South'
    roof_area = 14
    solar_install = solar.Solar(orientation=orientation,
                                roof_plan_area=roof_area)
    assert solar_install.number_of_panels > 0
    assert isinstance(solar_install.number_of_panels, int)


def test_generation():
    orientation = 'South'
    roof_area = 14
    solar_install = solar.Solar(orientation=orientation,
                                roof_plan_area=roof_area)
    assert solar_install.generation.fuel.name == 'electricity'
    assert (solar_install.generation.exported.annual_sum_kwh == solar_install.generation.overall.annual_sum_kwh)
    assert (solar_install.generation.imported.annual_sum_kwh == 0)
    assert abs(solar_install.generation.overall.annual_sum_kwh) > 0

    assert solar_install.generation.fuel.units == "kwh"
    assert solar_install.generation.fuel.name == 'electricity'

    assert isinstance(solar_install.generation.overall.profile_kwh, pd.Series)
    assert isinstance(solar_install.generation.overall.annual_sum_kwh, float)

    # fig = px.line(solar_install.generation.overall.profile_kwh.loc["2020-01-01": "2020-01-03"])
    # fig.show()


def test_peak_capacity_kw_out_per_kw_in_per_m2():
    orientation = 'North'
    roof_area = 10.5
    solar_install = solar.Solar(orientation=orientation,
                                roof_plan_area=roof_area)
    assert isinstance(solar_install.peak_capacity_kw_out_per_kw_in_per_m2, float)


def test_get_hourly_radiation_from_eu_api():
    pv_power_kw = solar.get_hourly_radiation_from_eu_api(lat=51.681,
                                                         lon=-3.724,
                                                         peak_capacity_kw_out_per_kw_in_per_m2=4,
                                                         pitch=30,
                                                         azimuth=-90
                                                         )
    np.testing.assert_almost_equal(pv_power_kw.sum(), 3035.86684)

    return pv_power_kw
