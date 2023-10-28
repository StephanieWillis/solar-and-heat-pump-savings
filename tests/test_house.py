import numpy as np
import pandas as pd

from .context import src
from src import building_model, solar, constants, roof, retrofit
from src.constants import SolarConstants


def test_envelope():
    house_type = "terrace"
    base_demand = constants.NORMALIZED_HOURLY_BASE_DEMAND * 1000.0
    envelope = building_model.BuildingEnvelope(house_type=house_type,
                                               annual_heating_demand=10000,
                                               base_electricity_demand_profile_kwh=base_demand)

    assert envelope.house_type == house_type
    assert len(envelope.base_demand.index) == 8760
    assert envelope.base_demand.sum() == 1000
    assert (envelope.base_demand >= 0).all()
    assert envelope.annual_heating_demand == 10000


def test_heating_system():
    profile = pd.Series(index=constants.BASE_YEAR_HOURLY_INDEX, data=1 / 8760)
    elec_res = building_model.HeatingSystem(name='Direct electric',
                                            efficiency=1.0,
                                            fuel=constants.ELECTRICITY,
                                            hourly_normalized_demand_profile=profile)

    annual_demand = 10000
    heating_consumption = elec_res.calculate_consumption(annual_space_heating_demand_kwh=annual_demand)

    assert (heating_consumption.overall.hourly_profile_kwh == profile * annual_demand / elec_res.efficiency).all()
    np.testing.assert_almost_equal(heating_consumption.imported.annual_sum_kwh,
                                   annual_demand / elec_res.efficiency)


def test_heating_system_from_constants():
    gas_boiler = building_model.HeatingSystem.from_constants(name="Gas boiler",
                                                             parameters=constants.DEFAULT_HEATING_CONSTANTS[
                                                                 "Gas boiler"])
    assert gas_boiler.fuel.name == 'gas'
    assert gas_boiler.fuel.units == 'kWh'
    assert gas_boiler.fuel.tco2_per_kwh == constants.GAS_TCO2_PER_KWH
    assert gas_boiler.fuel.converter_consumption_units_to_kwh == 1
    np.testing.assert_almost_equal(gas_boiler.hourly_normalized_demand_profile.sum(), 1.0)

    annual_demand = 12001
    space_heating_consumption = gas_boiler.calculate_consumption(annual_demand)
    assert space_heating_consumption.fuel == constants.GAS
    np.testing.assert_almost_equal(space_heating_consumption.overall.annual_sum_kwh,
                                   annual_demand / gas_boiler.efficiency)


def test_tariff_calculate_annual_cost():
    cheapo = building_model.Tariff(fuel=constants.ELECTRICITY,
                                   p_per_day=1.1,
                                   p_per_unit_import=2.0,
                                   p_per_unit_export=50)
    profile = pd.Series(index=constants.BASE_YEAR_HOURLY_INDEX, data=1 / 8760)
    elec_res = building_model.HeatingSystem(name='Direct electric',
                                            efficiency=1.0,
                                            fuel=constants.ELECTRICITY,
                                            hourly_normalized_demand_profile=profile)
    annual_demand = 10 * 8760
    space_heating_consumption = elec_res.calculate_consumption(annual_demand)
    # Check cost when no export
    annual_cost = cheapo.calculate_annual_net_cost(consumption=space_heating_consumption)
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
    annual_cost_with_export = cheapo.calculate_annual_net_cost(consumption=space_heating_consumption)
    assert annual_cost_with_export < annual_cost
    np.testing.assert_almost_equal(annual_cost_with_export,
                                   (cheapo.p_per_day * consumption_with_export.overall.days_in_year
                                    + cheapo.p_per_unit_import * consumption_with_export.imported.annual_sum_kwh
                                    - cheapo.p_per_unit_export * consumption_with_export.exported.annual_sum_kwh
                                    ) / 100)


def test_set_up_house_from_heating_name():
    envelope = building_model.BuildingEnvelope.from_building_type_constants(constants.BUILDING_TYPE_OPTIONS['Terrace'])

    # heat pump
    hp_house = building_model.House.set_up_from_heating_name(envelope=envelope, heating_name='Heat pump')
    hp_house_elec_consumption = hp_house.consumption_per_fuel['electricity']

    assert list(hp_house.consumption_per_fuel.keys()) == ['electricity']
    assert hp_house_elec_consumption.fuel.name == 'electricity'
    assert hp_house_elec_consumption.fuel.units == 'kWh'
    assert (hp_house_elec_consumption.overall.hourly_profile_kwh > 0).all()
    assert hp_house_elec_consumption.overall.annual_sum_kwh > 0
    assert (hp_house_elec_consumption.imported.hourly_profile_kwh
            + hp_house_elec_consumption.exported.hourly_profile_kwh
            == hp_house_elec_consumption.overall.hourly_profile_kwh).all()

    assert not hp_house.has_multiple_fuels
    df = hp_house.energy_and_bills_df
    assert (round(hp_house.total_annual_consumption_kwh, 0)
            == df['Your annual energy use kwh'].loc[df['fuel'] == 'electricity imports'].iloc[0])
    assert (round(hp_house.total_annual_bill)
            == df['Your annual energy bill £'].loc[df['fuel'] == 'electricity imports'].iloc[0])

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

    assert oil_house.solar_install.generation.overall.annual_sum_kwh == 0

    return hp_house, gas_house, oil_house


def test_typical_home_hits_price_cap():
    # price cap under Energy price guarantee is £2500 for house that uses 12,000kWh of gas and 2,900kWh of elec
    gas_boiler = building_model.HeatingSystem.from_constants(
        name='Gas boiler',
        parameters=constants.DEFAULT_HEATING_CONSTANTS['Gas boiler'])
    demand = 2900 * constants.NORMALIZED_HOURLY_BASE_DEMAND
    envelope = building_model.BuildingEnvelope(house_type='typical',
                                               annual_heating_demand=12000 * gas_boiler.efficiency,
                                               base_electricity_demand_profile_kwh=demand)
    gas_house = building_model.House.set_up_from_heating_name(envelope=envelope, heating_name='Gas boiler')
    assert gas_house.has_multiple_fuels is True
    np.testing.assert_almost_equal(gas_house.annual_consumption_per_fuel_kwh['electricity'], 2900)
    np.testing.assert_almost_equal(gas_house.annual_consumption_per_fuel_kwh['gas'], 12000)
    np.testing.assert_almost_equal(gas_house.total_annual_bill, 2492.1)  # looks like it isn't exactly 2500 after all
    np.testing.assert_almost_equal(gas_house.total_annual_tco2,
                                   (12000 * constants.GAS_TCO2_PER_KWH + 2900 * constants.ELEC_TCO2_PER_KWH))


def test_upgrade_buildings():
    envelope = building_model.BuildingEnvelope.from_building_type_constants(constants.BUILDING_TYPE_OPTIONS['Flat'])
    oil_house = building_model.House.set_up_from_heating_name(envelope=envelope, heating_name='Oil boiler')

    upgrade_heating = building_model.HeatingSystem.from_constants(name='Heat pump',
                                                                  parameters=constants.DEFAULT_HEATING_CONSTANTS[
                                                                      'Heat pump'])
    test_polygon = roof.Polygon(_points=[[0.132377, 52.19524],
                                  [0.13242, 52.195234],
                                  [0.132428, 52.195252],
                                  [0.132384, 52.19526],
                                  [0.132377, 52.19524]])
    solar_install = solar.Solar(orientation=SolarConstants.ORIENTATIONS['South'],
                                polygons=[test_polygon])

    solar_house, hp_house, both_house = retrofit.upgrade_buildings(baseline_house=oil_house,
                                                                   upgrade_heating=upgrade_heating,
                                                                   solar_install=solar_install)
    assert hp_house.solar_install.generation.overall.annual_sum_kwh == 0
    assert both_house.solar_install.generation.overall.annual_sum_kwh < 0  # export defined as negative
    np.testing.assert_almost_equal(both_house.consumption_per_fuel['electricity'].imported.annual_sum_kwh
                                   - both_house.consumption_per_fuel['electricity'].exported.annual_sum_kwh,
                                   both_house.consumption_per_fuel['electricity'].overall.annual_sum_kwh)

    assert (both_house.solar_install.generation.overall.annual_sum_kwh
            == solar_house.solar_install.generation.overall.annual_sum_kwh)

    assert hp_house.total_annual_bill > both_house.total_annual_bill
    np.testing.assert_almost_equal(both_house.annual_bill_import_and_export_per_fuel['electricity']['imported']
                                   - both_house.annual_bill_import_and_export_per_fuel['electricity']['exported'],
                                   both_house.annual_bill_per_fuel['electricity'])

    np.testing.assert_almost_equal(both_house.consumption_per_fuel['electricity'].imported.annual_sum_tco2
                                   - both_house.consumption_per_fuel['electricity'].exported.annual_sum_tco2,
                                   both_house.consumption_per_fuel['electricity'].overall.annual_sum_tco2)

    assert hp_house.percent_self_use_of_solar == 0
    assert oil_house.percent_self_use_of_solar == 0
    assert solar_house.percent_self_use_of_solar > 0
    assert round(solar_house.percent_self_use_of_solar, 3) == 0.827  # so high because only 0.8kW of panels
    assert both_house.percent_self_use_of_solar > solar_house.percent_self_use_of_solar
    assert round(both_house.percent_self_use_of_solar, 3) == 0.920

    return hp_house, solar_house, both_house
