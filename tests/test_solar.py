import pandas as pd
import plotly.express as px
import numpy as np

import solar
from constants import ORIENTATION_OPTIONS, SolarConstants, BASE_YEAR_HOURLY_INDEX
from roof import Polygon

TEST_POLYGONS = [Polygon(_points=[[0.132377, 52.19524],
                                  [0.13242, 52.195234],
                                  [0.132428, 52.195252],
                                  [0.132384, 52.19526],
                                  [0.132377, 52.19524]]),
                 Polygon(_points=[[0.132234, 52.195281],
                                  [0.132274, 52.195273],
                                  [0.132259, 52.195254],
                                  [0.132227, 52.195259],
                                  [0.132234, 52.195281]]),
                 Polygon(_points=[[0.132306, 52.195271],
                                  [0.132354, 52.195266],
                                  [0.132349, 52.195253],
                                  [0.132302, 52.195259],
                                  [0.132306, 52.195271]])]


def test_roof_area_returns_expected_type_and_value_one_polygon():
    pitch = 45
    solar_install = solar.Solar(orientation=ORIENTATION_OPTIONS['South'],
                                polygons=[TEST_POLYGONS[0]],
                                pitch=pitch)

    assert isinstance(solar_install.roof_area, float)
    assert solar_install.roof_area == solar_install.roof_plan_area / np.cos(np.deg2rad(pitch))


def test_get_number_of_panels_returns_expected_type_and_value():
    pitch = 22
    solar_install = solar.Solar(orientation=ORIENTATION_OPTIONS['South'],
                                polygons=[TEST_POLYGONS[0]],
                                pitch=pitch)
    assert isinstance(solar_install.number_of_panels, int)
    assert solar_install.number_of_panels == 2
    assert solar_install.number_of_panels != solar_install.get_number_of_panels_from_polygon_area(TEST_POLYGONS[0])


def test_peak_capacity_kw_out_per_kw_in_per_m2_returns_expected_type_and_value():
    solar_install = solar.Solar(orientation=ORIENTATION_OPTIONS['South'],
                                polygons=[TEST_POLYGONS[0]])
    assert isinstance(solar_install.peak_capacity_kw_out_per_kw_in_per_m2, float)
    assert solar_install.peak_capacity_kw_out_per_kw_in_per_m2 == (solar_install.number_of_panels
                                                                   * SolarConstants.KW_PEAK_PER_PANEL)


def test_get_hourly_radiation_from_eu_api_returns_expected_annual_sum():
    solar_install = solar.Solar(orientation=ORIENTATION_OPTIONS['East'],
                                polygons=[TEST_POLYGONS[0]],
                                pitch=30)
    assert solar_install.number_of_panels_has_been_overwritten is False
    solar_install.number_of_panels = 10  # overwrite for test
    assert solar_install.number_of_panels_has_been_overwritten is True

    assert solar_install.peak_capacity_kw_out_per_kw_in_per_m2 == 3.0
    pv_power_kw = solar_install.get_hourly_radiation_from_eu_api()
    ANNUAL_KWH = 2326.95354
    np.testing.assert_almost_equal(pv_power_kw.sum(), ANNUAL_KWH)
    np.testing.assert_almost_equal(solar_install.generation.exported.annual_sum_kwh, ANNUAL_KWH)
    np.testing.assert_almost_equal(solar_install.generation.overall.annual_sum_kwh, - ANNUAL_KWH)
    np.testing.assert_almost_equal(solar_install.generation.imported.annual_sum_kwh, 0)

    return pv_power_kw


def test_generation_attributed_to_correct_fuel_and_consumption_stream():
    solar_install = solar.Solar(orientation=ORIENTATION_OPTIONS['South'],
                                polygons=[TEST_POLYGONS[0]],
                                pitch=30)
    assert solar_install.generation.fuel.name == 'electricity'
    assert solar_install.generation.fuel.units == "kwh"

    assert isinstance(solar_install.generation.overall.hourly_profile_kwh, pd.Series)
    assert (solar_install.generation.overall.hourly_profile_kwh <= 0).all()  # export defined as negative
    assert (solar_install.generation.exported.hourly_profile_kwh >= 0).all()  # but positive when 'exported' property
    assert (solar_install.generation.imported.hourly_profile_kwh == 0).all()
    # fig = px.line(solar_install.generation.overall.hourly_profile_kwh.loc["2020-01-01": "2020-01-03"])
    # fig.show()

    assert isinstance(solar_install.generation.overall.annual_sum_kwh, float)
    assert (solar_install.generation.exported.annual_sum_kwh == - solar_install.generation.overall.annual_sum_kwh)
    assert (solar_install.generation.imported.annual_sum_kwh == 0)

    return solar_install


def test_solar_install_when_roof_area_is_zero():
    solar_install = solar.Solar(orientation=ORIENTATION_OPTIONS['Southwest'],
                                polygons=[Polygon.make_zero_area_instance()],
                                pitch=30)
    np.testing.assert_almost_equal(solar_install.generation.exported.annual_sum_kwh, 0)
    np.testing.assert_almost_equal(solar_install.generation.overall.annual_sum_kwh, 0)
    np.testing.assert_almost_equal(solar_install.generation.imported.annual_sum_kwh, 0)
    assert (solar_install.generation.overall.hourly_profile_kwh == 0).all()
    assert (solar_install.generation.overall.hourly_profile_kwh.index == BASE_YEAR_HOURLY_INDEX).all()
    return solar_install


def test_default_solar_install():
    solar_install = solar.Solar.create_zero_area_instance()
    np.testing.assert_almost_equal(solar_install.generation.exported.annual_sum_kwh, 0)
    np.testing.assert_almost_equal(solar_install.generation.overall.annual_sum_kwh, 0)
    np.testing.assert_almost_equal(solar_install.generation.imported.annual_sum_kwh, 0)
    assert (solar_install.generation.overall.hourly_profile_kwh == 0).all()
    assert (solar_install.generation.overall.hourly_profile_kwh.index == BASE_YEAR_HOURLY_INDEX).all()
    assert solar_install.orientation == SolarConstants.ORIENTATIONS['South']
    assert solar_install.pitch == SolarConstants.ROOF_PITCH_DEGREES
    return solar_install


def test_solar_install_polygon_does_not_have_4_vertices():
    test_polygon = Polygon(_points=[[0.132377, 52.19524],
                                    [0.13242, 52.195234],
                                    [0.132428, 52.195252],
                                    [0.132384, 52.19526],
                                    [0.132382, 52.19525],
                                    [0.132377, 52.19524]])
    solar_install = solar.Solar(orientation=ORIENTATION_OPTIONS['Southwest'],
                                polygons=[test_polygon],
                                pitch=30)
    assert solar_install.number_of_panels == solar_install.get_number_of_panels_from_polygon_area(test_polygon)


def test_cache_on_get_hourly_radiation_from_eu_api():
    solar_install = solar.Solar(orientation=ORIENTATION_OPTIONS['Southwest'],
                                polygons=TEST_POLYGONS,
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

    # check also works on copy - should hit
    solar_install_two = solar_install
    solar_install_two.generation.overall.annual_sum_kwh
    assert hash(solar_install) == hash(solar_install_two)
    print(solar.Solar.get_hourly_radiation_from_eu_api.cache_info())
    assert solar.Solar.get_hourly_radiation_from_eu_api.cache_info().hits == 4
    assert solar.Solar.get_hourly_radiation_from_eu_api.cache_info().misses == 1
    assert solar.Solar.get_hourly_radiation_from_eu_api.cache_info().currsize == 1

    # Change number of panels - should miss
    solar_install_two.number_of_panels = 1
    solar_install_two.generation.overall.annual_sum_kwh
    print(solar.Solar.get_hourly_radiation_from_eu_api.cache_info())
    assert solar.Solar.get_hourly_radiation_from_eu_api.cache_info().hits == 4
    assert solar.Solar.get_hourly_radiation_from_eu_api.cache_info().misses == 2
    assert solar.Solar.get_hourly_radiation_from_eu_api.cache_info().currsize == 2

    # Change orientation - should miss
    solar_install.orientation = ORIENTATION_OPTIONS['South']
    solar_install.generation.overall.annual_sum_kwh
    print(solar.Solar.get_hourly_radiation_from_eu_api.cache_info())
    assert solar.Solar.get_hourly_radiation_from_eu_api.cache_info().hits == 4
    assert solar.Solar.get_hourly_radiation_from_eu_api.cache_info().misses == 3
    assert solar.Solar.get_hourly_radiation_from_eu_api.cache_info().currsize == 3
