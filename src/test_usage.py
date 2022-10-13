import pandas as pd
import numpy as np

import constants
import usage


def test_set_up_house():
    house_floor_area_m2 = 100
    house_type = "terrace"
    envelope = usage.BuildingEnvelope(house_type=house_type, floor_area_m2=house_floor_area_m2)
    hp_house = usage.House.set_up_from_heating_name(envelope=envelope, heating_name='Heat pump')

    assert list(hp_house.consumption_profile_per_fuel.keys()) == ['electricity']
    assert hp_house.consumption_profile_per_fuel['electricity'].fuel.name == 'electricity'
    assert hp_house.consumption_profile_per_fuel['electricity'].fuel.units == 'kwh'
    assert (hp_house.consumption_profile_per_fuel['electricity'].profile_kwh > 0).all()
    assert hp_house.consumption_profile_per_fuel['electricity'].annual_sum_kwh > 0
    assert not hp_house.has_multiple_fuels
    assert hp_house.total_annual_consumption_kwh == hp_house.energy_and_bills_df['Your annual energy use kwh'].iloc[0]
    assert hp_house.total_annual_bill == hp_house.energy_and_bills_df['Your annual energy bill £'].iloc[0]

    gas_house = usage.House.set_up_from_heating_name(envelope=envelope, heating_name='Gas boiler')
    assert gas_house.has_multiple_fuels

    assert gas_house.envelope == hp_house.envelope
    assert list(gas_house.consumption_profile_per_fuel.keys()) == ['electricity', 'gas']

    oil_house = usage.House.set_up_from_heating_name(envelope=envelope, heating_name='Oil boiler')
    assert (oil_house.consumption_profile_per_fuel['oil'].annual_sum_fuel_units <
            oil_house.consumption_profile_per_fuel['oil'].annual_sum_kwh)
    np.testing.assert_almost_equal(oil_house.consumption_profile_per_fuel['oil'].annual_sum_fuel_units
                                   * constants.kwh_PER_LITRE_OF_OIL,
                                   oil_house.consumption_profile_per_fuel['oil'].annual_sum_kwh)

    return hp_house, gas_house, oil_house


if __name__ == '__main__':
    hp_house_check, gas_house_check, oil_house_check = test_set_up_house()
    results_df = usage.combined_results_dfs_multiple_houses([oil_house_check, hp_house_check], ['oil', 'heat pump'])
