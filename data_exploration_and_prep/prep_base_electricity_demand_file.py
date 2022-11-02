import datetime

import pandas as pd
import numpy as np

from constants import BASE_YEAR_HOURLY_INDEX

# Read in profiles and reformat ready to wrangle into a year of data
ELEC_PROFILES_XLSX = '../data_exploration_and_prep/AllProfileClasses.xlsx'

DAY_OF_WEEK_MAPPER = {1: 'Wd', 2: 'Wd', 3: 'Wd', 4: 'Wd', 5: 'Wd', 6: 'Sat', 7: 'Sun'}
# SEASON_LAST_DAY_MAPPER = ['Wtr': "2013-03-01",
#                           'Spr': "2013-05-01",
#                           'Sum': "2013-07-01",
#                           'HSum': "2013-08-01",
#                           'Aut': "2013-11-01",
# ('Wtr', "2013-12-31")]

df_half_hourly_day = pd.read_excel(io=ELEC_PROFILES_XLSX, sheet_name='Profile Class 1')
df_half_hourly_day['DateTime'] = pd.to_datetime("2013-01-01" + ' ' + df_half_hourly_day['Time'].astype(str))
df_half_hourly_day.set_index('DateTime', inplace=True)
df_half_hourly_day.drop(columns='Time', inplace=True)
df_hourly_day = df_half_hourly_day.resample('1H').sum()
# go back to only time in the index as will need it without the date to merge into the year
df_hourly_day.index = df_hourly_day.index.time

df_hourly_day.columns = df_hourly_day.columns.str.split(' ', expand=True)
df_hourly_day.columns.set_names(['season', 'day_of_the_week'], inplace=True)

# Set up whole year df
df_hourly_year = pd.DataFrame(index=BASE_YEAR_HOURLY_INDEX, columns=['season_group'], data=0)
df_hourly_year['day_of_week_group'] = df_hourly_year.index.dayofweek.map(DAY_OF_WEEK_MAPPER)
df_hourly_year['season'].loc[df_hourly_year.index < "2013-03-01"] = 'Wtr'


