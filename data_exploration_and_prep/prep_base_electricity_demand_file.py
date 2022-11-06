import datetime

import pandas as pd
import plotly.express as px
import numpy as np

from constants import BASE_YEAR_HOURLY_INDEX

# Read in profiles and reformat ready to wrangle into a year of data
# https://www.elexon.co.uk/operations-settlement/profiling/
ELEC_PROFILES_XLSX = '../data_exploration_and_prep/AllProfileClasses.xlsx'

DAY_OF_WEEK_MAPPER = {0: 'Wd', 1: 'Wd', 2: 'Wd', 3: 'Wd', 4: 'Wd', 5: 'Sat', 6: 'Sun'}
# In 2013 clocks changed on 31st of March and 27th of October. August bank holiday was on the 26th.
SEASON_FIRST_DAY_MAPPER = {'Wtr_start': "2013-01-01",
                           'Spr': "2013-03-31",  # from day of clock change
                           'Smr': "2013-05-11",  # from sixteenth sat before August bank holiday
                           'Hsr': "2013-07-20",  # from sixth sat before August bank holiday
                           'Aut': "2013-09-02",  # from Monday after August bank holiday
                           'Wtr_end': "2013-10-27"}  # from day of clock change in October
# Mapper to combine two winter periods
SEASON_MAPPER = {'Wtr_start': 'Wtr', 'Wtr_end': 'Wtr', 'Spr': 'Spr', 'Smr': 'Smr', 'Hsr': 'Hsr', 'Aut': 'Aut'}

df_half_hourly_day = pd.read_excel(io=ELEC_PROFILES_XLSX, sheet_name='Profile Class 1')
df_half_hourly_day['DateTime'] = pd.to_datetime("2013-01-01" + ' ' + df_half_hourly_day['Time'].astype(str))
df_half_hourly_day.set_index('DateTime', inplace=True)
df_half_hourly_day.drop(columns='Time', inplace=True)
# Initial data is in kW not in kWh so need to divide by 2 when sum
df_hourly_day = df_half_hourly_day.resample('1H').sum() / 2
pd.testing.assert_series_equal(left=df_hourly_day.mean(),
                               right=df_half_hourly_day.mean())  # average power should be the same

# go back to only time in the index as will need it without the date to merge into the year
df_hourly_day.index = df_hourly_day.index.time
df_hourly_day.index.name = 'time'

# Split out season and day of the week to make it easier to match on them
df_hourly_day.columns = df_hourly_day.columns.str.split(' ', expand=True)
df_hourly_day.columns.set_names(['season_group', 'day_of_week_group'], inplace=True)
series_hourly_day = df_hourly_day.stack([0, 1])
series_hourly_day.name = 'consumption_kWh'
df_hourly_day_transformed = series_hourly_day.reset_index()
# Reorder cols to make understanding df easier
df_hourly_day_transformed = df_hourly_day_transformed[['season_group', 'day_of_week_group', 'time',
                                                       'consumption_kWh']]

# Set up whole year df
df_hourly_year = pd.DataFrame(index=BASE_YEAR_HOURLY_INDEX, columns=['season_group'], data=0)
df_hourly_year['day_of_week_group'] = df_hourly_year.index.dayofweek.map(DAY_OF_WEEK_MAPPER)
for season, start_date in SEASON_FIRST_DAY_MAPPER.items():
    df_hourly_year.loc[df_hourly_year.index >= start_date, 'season_group'] = season
df_hourly_year['season_group'] = df_hourly_year['season_group'].map(SEASON_MAPPER)
df_hourly_year['time'] = df_hourly_year.index.time
df_hourly_year['datetime'] = df_hourly_year.index

df_merged = pd.merge(left=df_hourly_year, right=df_hourly_day_transformed, how='left',
                     on=['season_group', 'day_of_week_group', 'time'])
df_merged.set_index('datetime', inplace=True)

# normalize so demand profile sums to 1
hourly_kwh_series = df_merged['consumption_kWh']
hourly_kwh_series_normalized = hourly_kwh_series / hourly_kwh_series.sum()
assert (hourly_kwh_series_normalized.sum() == 1.0)

fig = px.line(hourly_kwh_series_normalized)
fig.show()

pd.to_pickle(hourly_kwh_series_normalized, "../data/normalized_hourly_base_electricity_demand_profile_2013.pkl")
