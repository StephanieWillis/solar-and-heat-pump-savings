# Solar output calculation

Using EU joint research centre calculations.

- GUI [here](https://re.jrc.ec.europa.eu/pvg_tools/en/tools.html)
- User manual [here](https://joint-research-centre.ec.europa.eu/pvgis-photovoltaic-geographical-information-system/getting-started-pvgis/pvgis-user-manual_en)
- API instructions [here](https://joint-research-centre.ec.europa.eu/pvgis-photovoltaic-geographical-information-system/getting-started-pvgis/api-non-interactive-service_en)

API. They have various options. The interesting two from our perspective are:
1. **Hourly solar radiation and PV data**: does the solar generation calculation for you. This includes very detailed 
calculations accounting for losses due to temperature and shading due to objects on the horizon
2. **Typical Meteorological Year (TMY) data**: Typical year so accounts for any year-on-year variation. Does not
include solar generation calculations.

We use #1 here because the solar calculation functionality is more useful than the averaging functionality.
A quick analysis of year-on-year variation (documented in *documentation/solar_year_on_year_variation*) shows the
standard deviation is about 3% of the total annual generation. That does mean you could be
quite significantly off if you chose the wrong year, but we will go with it for a minute. 
Later we could pull multiple years and average.

