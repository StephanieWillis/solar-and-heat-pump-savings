import copy
from typing import List, Tuple

import pandas as pd
import numpy as np

from building_model import House, HeatingSystem
from solar import Solar


class Retrofit:

    def __init__(self, baseline_house: 'House', upgrade_house: 'House'):
        self.baseline_house = baseline_house
        self.upgrade_house = upgrade_house

    @property
    def bill_savings_absolute(self):
        return self.baseline_house.total_annual_bill - self.upgrade_house.total_annual_bill

    @property
    def bill_savings_pct(self):
        return self.bill_savings_absolute/ self.baseline_house.total_annual_bill

    @property
    def carbon_savings_absolute(self):
        return self.baseline_house.total_annual_tco2 - self.upgrade_house.total_annual_tco2

    @property
    def carbon_savings_pct(self):
        return self.carbon_savings_absolute/self.baseline_house.total_annual_tco2

    @property
    def incremental_cost(self):
        return self.upgrade_house.upfront_cost_after_grants - self.baseline_house.upfront_cost

    @property
    def simple_payback(self) -> float:
        if self.bill_savings_absolute > 0:
            payback = self.incremental_cost/self.bill_savings_absolute
        else:
            payback = np.nan
        return payback


def upgrade_buildings(baseline_house: 'House', solar_install: 'Solar', upgrade_heating: 'HeatingSystem'
                      ) -> Tuple['House', 'House', 'House']:
    hp_house = copy.deepcopy(baseline_house)  # do after modifications so modifications flow through
    hp_house.heating_system = upgrade_heating

    solar_house = copy.deepcopy(baseline_house)
    solar_house.solar_install = solar_install

    both_house = copy.deepcopy(hp_house)
    both_house.solar_install = solar_install

    assert (hp_house.consumption_per_fuel['electricity'].overall.annual_sum_kwh -
            hp_house.heating_consumption.overall.annual_sum_kwh
            - hp_house.electricity_consumption_excluding_heating.overall.annual_sum_kwh) < 0.1

    return solar_house, hp_house, both_house


def generate_all_retrofit_cases(baseline_house: 'House', solar_house: 'House', hp_house: 'House',
                                both_house: 'House'):
    solar_retrofit = Retrofit(baseline_house=baseline_house, upgrade_house=solar_house)
    hp_retrofit = Retrofit(baseline_house=baseline_house, upgrade_house=hp_house)
    both_retrofit = Retrofit(baseline_house=baseline_house, upgrade_house=both_house)
    return solar_retrofit, hp_retrofit, both_retrofit


def combine_results_dfs_multiple_houses(houses: List['House'], keys: List['str']):
    results_df = pd.concat([house.energy_and_bills_df for house in houses], keys=keys)
    results_df.index.names = ['Upgrade option', 'old_index']
    results_df = results_df.reset_index()
    results_df = results_df.drop(columns='old_index')
    return results_df




