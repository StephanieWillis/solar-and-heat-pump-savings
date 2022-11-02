import pandas as pd
import numpy as np

HEATING_PROFILES_CSV = '../data_exploration_and_prep/Half-hourly_profiles_of_heating_technologies.csv'
COLS_TO_KEEP = ['Normalised_ASHP_heat', 'Normalised_Resistance_heater_heat', 'Normalised_Gas_boiler_heat']

df_half_hourly = pd.read_csv(filepath_or_buffer=HEATING_PROFILES_CSV, index_col='index', usecols=['index'] + COLS_TO_KEEP)

df_half_hourly.index = pd.to_datetime(df_half_hourly.index)
df_hourly = df_half_hourly.resample('1H').sum()
np.testing.assert_almost_equal(df_hourly.sum().sum(), df_half_hourly.sum().sum())
assert len(df_hourly) == 8760

df_hourly = df_hourly/df_hourly.sum()  # normalize so demand profile sums to 1
assert (df_hourly.sum().sum() == 3.0)

pd.to_pickle(df_hourly, "../src/hourly_heating_demand_profiles_2013.pkl")