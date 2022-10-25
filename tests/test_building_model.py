import numpy as np
import pandas as pd

from src import constants
from src.constants import SolarConstants
from src import building_model
from src import solar


def test_envelope():
    house_floor_area_m2 = 100
    house_type = "terrace"
    envelope = building_model.BuildingEnvelope(floor_area_m2=house_floor_area_m2, house_type=house_type)

    assert envelope.floor_area_m2 == house_floor_area_m2
    assert envelope.house_type == house_type
    assert len(envelope.base_demand.index) == 8760 + 24  # leap year
    assert envelope.base_demand.sum() > 0
    assert (envelope.space_heating_demand > 0).all()
    assert (envelope.water_heating_demand > 0).all()


def test_heating_system():
    elec_res = building_model.HeatingSystem(name='Electric storage heater',
                                            space_heating_efficiency=1.0,
                                            water_heating_efficiency=1.0,
                                            fuel=constants.ELECTRICITY)

    demand = pd.Series(index=constants.BASE_YEAR_HOURLY_INDEX, data=5)
    space_heating_consumption = elec_res.calculate_space_heating_consumption(demand)
    water_heating_consumption = elec_res.calculate_water_heating_consumption(demand)

    assert (space_heating_consumption.overall.hourly_profile_kwh == demand / elec_res.space_heating_efficiency).all()
    assert water_heating_consumption.overall.annual_sum_kwh == demand.sum() / elec_res.water_heating_efficiency
    assert water_heating_consumption.exported.annual_sum_kwh == 0
    assert space_heating_consumption.imported.annual_sum_kwh == demand.sum() / elec_res.space_heating_efficiency


def test_heating_system_from_constants():
    gas_boiler = building_model.HeatingSystem.from_constants(name="Gas boiler",
                                                             parameters=constants.DEFAULT_HEATING_CONSTANTS[
                                                                 "Gas boiler"])
    assert gas_boiler.fuel.name == 'gas'
    assert gas_boiler.fuel.units == 'kwh'
    assert gas_boiler.fuel.tco2_per_kwh == constants.GAS_TCO2_PER_KWH
    assert gas_boiler.fuel.converter_consumption_units_to_kwh == 1

    demand = pd.Series(index=constants.BASE_YEAR_HOURLY_INDEX, data=20)
    space_heating_consumption = gas_boiler.calculate_space_heating_consumption(demand)
    assert space_heating_consumption.fuel == constants.GAS
    np.testing.assert_almost_equal(space_heating_consumption.overall.annual_sum_kwh,
                                   demand.sum() / gas_boiler.space_heating_efficiency)


def test_tariff_calculate_annual_cost():
    cheapo = building_model.Tariff(fuel=constants.ELECTRICITY,
                                   p_per_day=1.1,
                                   p_per_unit_import=2.0,
                                   p_per_unit_export=50)
    elec_res = building_model.HeatingSystem(name='Electric storage heater',
                                            space_heating_efficiency=1.0,
                                            water_heating_efficiency=1.0,
                                            fuel=constants.ELECTRICITY)
    demand = pd.Series(index=constants.BASE_YEAR_HOURLY_INDEX, data=10)
    space_heating_consumption = elec_res.calculate_space_heating_consumption(demand)
    # Check cost when no export
    annual_cost = cheapo.calculate_annual_cost(consumption=space_heating_consumption)
    np.testing.assert_almost_equal(annual_cost,
                                   (cheapo.p_per_day * space_heating_consumption.overall.days_in_year
                                    + cheapo.p_per_unit_import * space_heating_consumption.overall.annual_sum_kwh)
                                   / 100)

    # Check consumption with export behaves as you expect
    consumption_with_export = space_heating_consumption
    consumption_with_export.overall.hourly_profile_kwh.iloc[0] -= 100
    assert consumption_with_export.overall.annual_sum_kwh == 10 * consumption_with_export.overall.hours_in_year - 100
    assert consumption_with_export.imported.annual_sum_kwh == 10 * consumption_with_export.overall.hours_in_year - 10
    assert consumption_with_export.exported.annual_sum_kwh == 90

    # Check cost with export
    annual_cost_with_export = cheapo.calculate_annual_cost(consumption=space_heating_consumption)
    assert annual_cost_with_export < annual_cost
    np.testing.assert_almost_equal(annual_cost_with_export,
                                   (cheapo.p_per_day * consumption_with_export.overall.days_in_year
                                    + cheapo.p_per_unit_import * consumption_with_export.imported.annual_sum_kwh
                                    - cheapo.p_per_unit_export * consumption_with_export.exported.annual_sum_kwh
                                    ) / 100)


def test_set_up_house_from_heating_name():
    house_floor_area_m2 = 100
    house_type = "terrace"
    envelope = building_model.BuildingEnvelope(house_type=house_type, floor_area_m2=house_floor_area_m2)

    # heat pump
    hp_house = building_model.House.set_up_from_heating_name(envelope=envelope, heating_name='Heat pump')
    hp_house_elec_consumption = hp_house.consumption_per_fuel['electricity']

    assert list(hp_house.consumption_per_fuel.keys()) == ['electricity']
    assert hp_house_elec_consumption.fuel.name == 'electricity'
    assert hp_house_elec_consumption.fuel.units == 'kwh'
    assert (hp_house_elec_consumption.overall.hourly_profile_kwh > 0).all()
    assert hp_house_elec_consumption.overall.annual_sum_kwh > 0
    assert (
            hp_house_elec_consumption.imported.hourly_profile_kwh + hp_house_elec_consumption.exported.hourly_profile_kwh
            == hp_house_elec_consumption.overall.hourly_profile_kwh).all()

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
                                   * constants.KWH_PER_LITRE_OF_OIL,
                                   oil_house.consumption_per_fuel['oil'].overall.annual_sum_kwh)

    assert oil_house.solar.generation.overall.annual_sum_kwh == 0

    return hp_house, gas_house, oil_house


# def test_upgrade_buildings():
#     house_floor_area_m2 = 100
#     house_type = "terrace"
#     envelope = building_model.BuildingEnvelope(house_type=house_type, floor_area_m2=house_floor_area_m2)
#     oil_house = building_model.House.set_up_from_heating_name(envelope=envelope, heating_name='Oil boiler')
#
#     upgrade_heating = building_model.HeatingSystem.from_constants(name='Heat pump',
#                                                                   parameters=constants.DEFAULT_HEATING_CONSTANTS[
#                                                                       'Heat pump'])
#     solar_install = solar.Solar(orientation=SolarConstants.ORIENTATIONS['South'],
#                                 roof_plan_area=48)
#     hp_house, solar_house, both_house = building_model.upgrade_buildings(baseline_house=oil_house,
#                                                                          upgrade_heating=upgrade_heating,
#                                                                          upgrade_solar=solar_install)
#     assert hp_house.solar.generation.overall.annual_sum_kwh == 0
#     assert both_house.solar.generation.overall.annual_sum_kwh < 0  # export defined as negative
#     np.testing.assert_almost_equal(both_house.consumption_per_fuel['electricity'].exported.annual_sum_kwh
#                                    + both_house.consumption_per_fuel['electricity'].imported.annual_sum_kwh,
#                                    both_house.consumption_per_fuel['electricity'].overall.annual_sum_kwh)
#     assert hp_house.total_annual_bill > both_house.total_annual_bill
#
#     assert both_house.solar.generation.overall.annual_sum_kwh == solar_house.solar.generation.overall.annual_sum_kwh
#
#     return hp_house, solar_house, both_house


def test_combine_results_dfs_multiple_houses():
    pass

# TODO: solve issue where heat pump isn't using any electricity
# TODO: solve issue wher esolar is increasing electricity bills - perhaps related to above
