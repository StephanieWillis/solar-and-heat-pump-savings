import copy

import pandas as pd
import plotly.express as px
import numpy as np
from math import floor

import solar
from constants import OrientationOptions, SolarConstants


def test_roof_area_returns_expected_type_and_value():
    pitch = 45
    plan_area = 14
    solar_install = solar.Solar(orientation=OrientationOptions['South'],
                                roof_plan_area=plan_area,
                                latitude=51.681,
                                longitude=-3.724,
                                pitch=pitch)

    assert isinstance(solar_install.roof_area, float)
    assert solar_install.roof_area == plan_area/np.cos(np.deg2rad(45))


def test_get_number_of_panels_returns_expected_type_and_value():
    pitch = 22
    plan_area = 11.2
    solar_install = solar.Solar(orientation=OrientationOptions['North'],
                                roof_plan_area=plan_area,
                                latitude=51.681,
                                longitude=-3.724,
                                pitch=pitch)
    assert isinstance(solar_install.number_of_panels, int)
    assert solar_install.number_of_panels == floor(plan_area/np.cos(np.deg2rad(pitch))
                                              * SolarConstants.PERCENT_SQUARE_USABLE / SolarConstants.PANEL_AREA)


def test_peak_capacity_kw_out_per_kw_in_per_m2_returns_expected_type_and_value():
    solar_install = solar.Solar(orientation=OrientationOptions['North'],
                                roof_plan_area=10.5,
                                latitude=51.681,
                                longitude=-3.724)
    assert isinstance(solar_install.peak_capacity_kw_out_per_kw_in_per_m2, float)
    assert solar_install.peak_capacity_kw_out_per_kw_in_per_m2 == (solar_install.number_of_panels
                                                                   * SolarConstants.KW_PEAK_PER_PANEL)


def test_get_hourly_radiation_from_eu_api_returns_expected_annual_sum():
    solar_install = solar.Solar(orientation=OrientationOptions['East'],
                                roof_plan_area=10.5,
                                latitude=51.681,
                                longitude=-3.724,
                                pitch=30)
    solar_install.number_of_panels = 10  # overwrite for test
    assert solar_install.peak_capacity_kw_out_per_kw_in_per_m2 == 3.0
    pv_power_kw = solar_install.get_hourly_radiation_from_eu_api()
    np.testing.assert_almost_equal(pv_power_kw.sum(), 2271.12168)
    np.testing.assert_almost_equal(solar_install.generation.exported.annual_sum_kwh, - 2271.12168)
    np.testing.assert_almost_equal(solar_install.generation.overall.annual_sum_kwh, - 2271.12168)
    np.testing.assert_almost_equal(solar_install.generation.imported.annual_sum_kwh, 0)

    return pv_power_kw


def test_generation_attributed_to_correct_fuel_and_consumption_stream():
    solar_install = solar.Solar(orientation=OrientationOptions['Southwest'],
                                roof_plan_area=4,
                                latitude=51.681,
                                longitude=-3.724,
                                pitch=30)
    assert solar_install.generation.fuel.name == 'electricity'
    assert solar_install.generation.fuel.units == "kwh"

    assert isinstance(solar_install.generation.overall.hourly, pd.Series)
    assert (solar_install.generation.overall.hourly <= 0).all()  # export defined as negative
    fig = px.line(solar_install.generation.overall.hourly.loc["2020-01-01": "2020-01-03"])
    fig.show()

    assert isinstance(solar_install.generation.overall.annual_sum_kwh, float)
    assert (solar_install.generation.exported.annual_sum_kwh == solar_install.generation.overall.annual_sum_kwh)
    assert (solar_install.generation.imported.annual_sum_kwh == 0)

    return solar_install


def test_solar_install_when_roof_area_is_zero():

    solar_install = solar.Solar(orientation=OrientationOptions['Southwest'],
                                roof_plan_area=0,
                                latitude=51.681,
                                longitude=-3.724,
                                pitch=30)
    np.testing.assert_almost_equal(solar_install.generation.exported.annual_sum_kwh, 0)
    np.testing.assert_almost_equal(solar_install.generation.overall.annual_sum_kwh, 0)
    np.testing.assert_almost_equal(solar_install.generation.imported.annual_sum_kwh, 0)
    assert (solar_install.generation.overall.hourly == 0).all()
    assert(solar_install.generation.overall.hourly.index == list(range(8760))).all()
    return solar_install


def test_cache_on_get_hourly_radiation_from_eu_api():

    solar_install = solar.Solar(orientation=OrientationOptions['Southwest'],
                                roof_plan_area=20,
                                latitude=51.681,
                                longitude=-3.724,
                                pitch=30)

    # check works when getting property
    solar.Solar.get_hourly_radiation_from_eu_api.cache_clear()
    solar_install.generation.overall.annual_sum_kwh
    solar_install.generation.imported.annual_sum_kwh
    solar_install.generation.exported.days_in_year
    solar_install.generation.fuel.name
    print(solar.Solar.get_hourly_radiation_from_eu_api.cache_info())
    assert solar.Solar.get_hourly_radiation_from_eu_api.cache_info().hits == 3
    assert solar.Solar.get_hourly_radiation_from_eu_api.cache_info().misses == 1
    assert solar.Solar.get_hourly_radiation_from_eu_api.cache_info().currsize == 1

    # check also works on copy
    solar_install_two = solar_install
    assert hash(solar_install) == hash(solar_install_two)
    assert solar.Solar.get_hourly_radiation_from_eu_api.cache_info().hits == 4
    assert solar.Solar.get_hourly_radiation_from_eu_api.cache_info().misses == 1
    assert solar.Solar.get_hourly_radiation_from_eu_api.cache_info().currsize == 1

    # Should miss here
    solar_install_two.number_of_panels = 1
    solar_install_two.generation.overall.annual_sum_kwh
    assert solar.Solar.get_hourly_radiation_from_eu_api.cache_info().hits == 4
    assert solar.Solar.get_hourly_radiation_from_eu_api.cache_info().misses == 2
    assert solar.Solar.get_hourly_radiation_from_eu_api.cache_info().currsize == 2


