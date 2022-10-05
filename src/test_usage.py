import constants
import usage


def test_calculate_consumption():
    house_floor_area_m2 = 100
    house_type = "terrace"
    house = usage.BuildingEnvelope(house_type=house_type, floor_area_m2=house_floor_area_m2)
    heating_system = usage.HeatingSystem(name='Heat pump',
                                         space_heating_efficiency=3.5,
                                         water_heating_efficiency=3.0,
                                         fuel=constants.ELECTRICITY)

    consumption_dict = house.calculate_consumption(heating_system=heating_system)
    assert list(consumption_dict.keys()) == ['electricity']
    assert consumption_dict['electricity'].fuel.name == 'electricity'
    assert consumption_dict['electricity'].fuel.units == 'kWh'
    assert (consumption_dict['electricity'].profile > 0).all()
    assert consumption_dict['electricity'].annual_sum > 0
    return consumption_dict


if __name__ == '__main__':

    consumption_dict_trial = test_calculate_consumption()
    print(consumption_dict_trial)
