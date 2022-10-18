import pandas as pd
import numpy as np

import constants
import building_model


def test_set_up_house():
    house_floor_area_m2 = 100
    house_type = "terrace"
    envelope = building_model.BuildingEnvelope(house_type=house_type, floor_area_m2=house_floor_area_m2)
    hp_house = building_model.House.set_up_from_heating_name(envelope=envelope, heating_name='Heat pump')

    assert list(hp_house.consumption_profile_per_fuel.keys()) == ['electricity']
    assert hp_house.consumption_profile_per_fuel['electricity'].fuel.name == 'electricity'
    assert hp_house.consumption_profile_per_fuel['electricity'].fuel.units == 'kwh'
    assert (hp_house.consumption_profile_per_fuel['electricity'].profile_kwh > 0).all()
    assert hp_house.consumption_profile_per_fuel['electricity'].annual_sum_kwh > 0
    assert not hp_house.has_multiple_fuels
    assert hp_house.total_annual_consumption_kwh == hp_house.energy_and_bills_df['Your annual energy use kwh'].iloc[0]
    assert hp_house.total_annual_bill == hp_house.energy_and_bills_df['Your annual energy bill £'].iloc[0]

    gas_house = building_model.House.set_up_from_heating_name(envelope=envelope, heating_name='Gas boiler')
    assert gas_house.has_multiple_fuels

    assert gas_house.envelope == hp_house.envelope
    assert list(gas_house.consumption_profile_per_fuel.keys()) == ['electricity', 'gas']

    oil_house = building_model.House.set_up_from_heating_name(envelope=envelope, heating_name='Oil boiler')
    assert (oil_house.consumption_profile_per_fuel['oil'].annual_sum_fuel_units <
            oil_house.consumption_profile_per_fuel['oil'].annual_sum_kwh)
    np.testing.assert_almost_equal(oil_house.consumption_profile_per_fuel['oil'].annual_sum_fuel_units
                                   * constants.kwh_PER_LITRE_OF_OIL,
                                   oil_house.consumption_profile_per_fuel['oil'].annual_sum_kwh)

    assert oil_house.solar.generation.annual_sum_kwh == 0

    return hp_house, gas_house, oil_house


def test_solar():
    orientation = 'South'
    roof_area = 14
    solar_install = building_model.Solar(orientation=orientation,
                                         roof_area=roof_area)
    assert solar_install.generation.fuel.name == 'electricity'
    assert solar_install.number_of_panels > 0
    assert abs(solar_install.generation.annual_sum_kwh) > 0

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


def test_upgrade_homes():
    house_floor_area_m2 = 100
    house_type = "terrace"
    envelope = building_model.BuildingEnvelope(house_type=house_type, floor_area_m2=house_floor_area_m2)
    oil_house = building_model.House.set_up_from_heating_name(envelope=envelope, heating_name='Oil boiler')

    upgrade_heating = building_model.HeatingSystem.from_constants(name='Heat pump',
                                                                  parameters=constants.DEFAULT_HEATING_CONSTANTS[
                                                                      'Heat pump'])
    solar_install = building_model.Solar(orientation='South',
                                         roof_area=48)
    hp_house, solar_house, both_house = building_model.upgrade_buildings(baseline_house=oil_house,
                                                                         upgrade_heating=upgrade_heating,
                                                                         upgrade_solar=solar_install)
    assert hp_house.solar.generation.annual_sum_kwh == 0
    assert abs(both_house.solar.generation.annual_sum_kwh) > 0
    assert hp_house.total_annual_bill > both_house.total_annual_bill


if __name__ == '__main__':
    hp_house_check, gas_house_check, oil_house_check = test_set_up_house()
    results_df = building_model.combined_results_dfs_multiple_houses([oil_house_check, hp_house_check],
                                                                     ['oil', 'heat pump'])
    solar_install_trial = test_solar()
    test_upgrade_homes()
