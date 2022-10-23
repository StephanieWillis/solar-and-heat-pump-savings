import numpy as np

from src import constants
from src import building_model
from src import solar


def test_set_up_from_heating_name():
    house_floor_area_m2 = 100
    house_type = "terrace"
    envelope = building_model.BuildingEnvelope(house_type=house_type, floor_area_m2=house_floor_area_m2)

    # heat pump
    hp_house = building_model.House.set_up_from_heating_name(envelope=envelope, heating_name='Heat pump')
    hp_house_elec_consumption = hp_house.consumption_per_fuel['electricity']

    assert (hp_house_elec_consumption.imported.profile_kwh + hp_house_elec_consumption.exported.profile_kwh
            == hp_house_elec_consumption.overall.profile_kwh).all()
    assert list(hp_house.consumption_per_fuel.keys()) == ['electricity']
    assert hp_house_elec_consumption.fuel.name == 'electricity'
    assert hp_house_elec_consumption.fuel.units == 'kwh'
    assert (hp_house_elec_consumption.overall.profile_kwh > 0).all()
    assert hp_house_elec_consumption.overall.annual_sum_kwh > 0
    assert not hp_house.has_multiple_fuels
    assert hp_house.total_annual_consumption_kwh == hp_house.energy_and_bills_df['Your annual energy use kwh'].iloc[0]
    assert hp_house.total_annual_bill == hp_house.energy_and_bills_df['Your annual energy bill £'].iloc[0]

    # gas boiler
    gas_house = building_model.House.set_up_from_heating_name(envelope=envelope, heating_name='Gas boiler')
    assert gas_house.has_multiple_fuels

    assert gas_house.envelope == hp_house.envelope
    assert list(gas_house.consumption_per_fuel.keys()) == ['electricity', 'gas']

    # oil boiler
    oil_house = building_model.House.set_up_from_heating_name(envelope=envelope, heating_name='Oil boiler')
    assert (oil_house.consumption_per_fuel['oil'].overall.annual_sum_fuel_units <
            oil_house.consumption_per_fuel['oil'].overall.annual_sum_kwh)
    np.testing.assert_almost_equal(oil_house.consumption_per_fuel['oil'].overall.annual_sum_fuel_units
                                   * constants.kwh_PER_LITRE_OF_OIL,
                                   oil_house.consumption_per_fuel['oil'].overall.annual_sum_kwh)

    assert oil_house.solar.generation.overall.annual_sum_kwh == 0

    return hp_house, gas_house, oil_house


def test_upgrade_buildings():
    house_floor_area_m2 = 100
    house_type = "terrace"
    envelope = building_model.BuildingEnvelope(house_type=house_type, floor_area_m2=house_floor_area_m2)
    oil_house = building_model.House.set_up_from_heating_name(envelope=envelope, heating_name='Oil boiler')

    upgrade_heating = building_model.HeatingSystem.from_constants(name='Heat pump',
                                                                  parameters=constants.DEFAULT_HEATING_CONSTANTS[
                                                                      'Heat pump'])
    solar_install = solar.Solar(orientation='South',
                                roof_plan_area=48)
    hp_house, solar_house, both_house = building_model.upgrade_buildings(baseline_house=oil_house,
                                                                         upgrade_heating=upgrade_heating,
                                                                         upgrade_solar=solar_install)
    assert hp_house.solar.generation.overall.annual_sum_kwh == 0
    assert abs(both_house.solar.generation.overall.annual_sum_kwh) > 0
    np.testing.assert_almost_equal(both_house.consumption_per_fuel['electricity'].exported.annual_sum_kwh
                                   + both_house.consumption_per_fuel['electricity'].imported.annual_sum_kwh,
                                   both_house.consumption_per_fuel['electricity'].overall.annual_sum_kwh)
    assert hp_house.total_annual_bill > both_house.total_annual_bill

