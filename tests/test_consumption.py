import pandas as pd
import numpy as np

from src import consumption
from src import constants
from src.constants import BASE_YEAR_HOURLY_INDEX


def test_consumption_stream_annual_sum():
    stream_5 = consumption.ConsumptionStream(hourly_profile_kwh=pd.Series(index=BASE_YEAR_HOURLY_INDEX, data=5))
    assert stream_5.annual_sum_kwh == 5 * len(BASE_YEAR_HOURLY_INDEX)

    profile_increasing = consumption.ConsumptionStream(hourly_profile_kwh=pd.Series(index=BASE_YEAR_HOURLY_INDEX,
                                                                                    data=list(range(
                                                                                        len(BASE_YEAR_HOURLY_INDEX)))))
    assert profile_increasing.annual_sum_kwh == sum(list(range(len(BASE_YEAR_HOURLY_INDEX))))


def test_consumption_stream_add():
    stream_5 = consumption.ConsumptionStream(hourly_profile_kwh=pd.Series(index=BASE_YEAR_HOURLY_INDEX, data=5))
    stream_2 = consumption.ConsumptionStream(hourly_profile_kwh=pd.Series(index=BASE_YEAR_HOURLY_INDEX, data=2))
    profile_added = stream_2.add(stream_5)
    assert profile_added.hourly_profile_kwh[0] == 2 + 5
    profile_increasing = consumption.ConsumptionStream(hourly_profile_kwh=pd.Series(index=BASE_YEAR_HOURLY_INDEX,
                                                                                    data=list(range(
                                                                                        len(BASE_YEAR_HOURLY_INDEX)))))
    profile_added_again = profile_added.add(profile_increasing)
    assert profile_added_again.hourly_profile_kwh.iloc[1] == 2 + 5 + 1


def test_consumption_stream_fuel_units():
    stream_elec = consumption.ConsumptionStream(hourly_profile_kwh=pd.Series(index=BASE_YEAR_HOURLY_INDEX, data=5))
    assert stream_elec.fuel == constants.ELECTRICITY
    assert (stream_elec.hourly_profile_kwh == stream_elec.hourly_profile_fuel_units).all()
    assert stream_elec.annual_sum_kwh == stream_elec.annual_sum_fuel_units

    stream_gas = consumption.ConsumptionStream(hourly_profile_kwh=pd.Series(index=BASE_YEAR_HOURLY_INDEX, data=10),
                                               fuel=constants.GAS)
    assert (stream_gas.hourly_profile_kwh == stream_gas.hourly_profile_fuel_units).all()

    stream_oil = consumption.ConsumptionStream(hourly_profile_kwh=pd.Series(index=BASE_YEAR_HOURLY_INDEX, data=12),
                                               fuel=constants.OIL)
    assert stream_oil.annual_sum_fuel_units != stream_oil.annual_sum_kwh
    assert (stream_oil.hourly_profile_kwh / stream_oil.hourly_profile_fuel_units
            == constants.KWH_PER_LITRE_OF_OIL).all()


def test_consumption_stream_tco2():
    stream_gas = consumption.ConsumptionStream(hourly_profile_kwh=pd.Series(index=BASE_YEAR_HOURLY_INDEX, data=10),
                                               fuel=constants.GAS)
    assert stream_gas.annual_sum_tco2 == stream_gas.annual_sum_kwh * constants.GAS_TCO2_PER_KWH

    stream_oil = consumption.ConsumptionStream(hourly_profile_kwh=pd.Series(index=BASE_YEAR_HOURLY_INDEX, data=12),
                                               fuel=constants.OIL)
    assert stream_oil.annual_sum_tco2 == stream_oil.annual_sum_kwh * constants.OIL_TCO2_PER_KWH


def test_consumption_import_only():
    profile = pd.Series(index=constants.BASE_YEAR_HOURLY_INDEX, data=0.5)
    consumption_gas = consumption.Consumption(hourly_profile_kwh=profile, fuel=constants.GAS)
    assert consumption_gas.exported.annual_sum_kwh == 0
    assert consumption_gas.imported.annual_sum_kwh == 0.5 * consumption_gas.overall.hours_in_year
    assert (consumption_gas.imported.hourly_profile_kwh == consumption_gas.overall.hourly_profile_kwh).all()


def test_consumption_import_and_export():
    idx = constants.BASE_YEAR_HOURLY_INDEX
    minute_of_the_day = idx.hour * 60 + idx.minute
    profile_data = - np.cos(minute_of_the_day * np.pi * 2 / (24 * 60))
    profile = pd.Series(index=idx, data=profile_data)
    consumption_oil = consumption.Consumption(hourly_profile_kwh=profile, fuel=constants.OIL)

    np.testing.assert_almost_equal(consumption_oil.overall.annual_sum_kwh, 0)  # symmetric
    assert consumption_oil.imported.annual_sum_kwh > 0
    assert consumption_oil.exported.annual_sum_kwh > 0
    np.testing.assert_almost_equal(consumption_oil.imported.annual_sum_kwh,
                                   consumption_oil.exported.annual_sum_kwh)
    np.testing.assert_almost_equal(consumption_oil.imported.annual_sum_fuel_units,
                                   consumption_oil.exported.annual_sum_fuel_units)   # symmetric

    assert (consumption_oil.imported.hourly_profile_kwh >= 0).all()
    assert (consumption_oil.exported.hourly_profile_fuel_units >= 0).all()

    consumption_oil_two = consumption.Consumption(hourly_profile_kwh=profile, fuel=constants.OIL)
    consumption_oil_added = consumption_oil_two.add(consumption_oil)
    np.testing.assert_almost_equal(consumption_oil_added.overall.annual_sum_kwh, 0)  # symmetric
    assert consumption_oil_added.imported.annual_sum_kwh == 2 * consumption_oil.imported.annual_sum_kwh
    assert (consumption_oil_added.overall.hourly_profile_fuel_units
            == 2 * consumption_oil_two.overall.hourly_profile_fuel_units).all()
