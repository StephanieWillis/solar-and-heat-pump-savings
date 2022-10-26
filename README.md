# Heat pump and solar savings

Web app to calculate bill and carbon savings from installing solar, a heat pump, or both. Calculations account for proportion
of solar generation that is used within the home vs. exported. 

## Data sources


### Annual demand


### Heating system efficiencies

**Heat pumps** - using rounded values from 5 kW 
[Vaillant arotherm SCOP data](https://www.vaillant.co.uk/downloads/aproducts/renewables-1/arotherm-plus/arotherm-plus-1/quick-guides/new-5/installers-quick-guide-arotherm-plus-1949445.pdf),
 with flow temperature of 50C for space heating and 55C for water heating. These efficiencies are above
recorded averages (2.76 according to this [nesta analysis](https://www.nesta.org.uk/report/reduce-the-cost-of-heat-pumps/))
but lower than reported values for high quality installs. 

**Gas boiler** - using 85% for space heating, a widely used assumption including in this 
[nesta analysis](https://www.nesta.org.uk/report/reduce-the-cost-of-heat-pumps/)). Using 80% for water heating due to lower
efficiencies in the summer when the boiler only heats hot water. These are likely at the high end of real gas
boiler performance. 

**Oil boiler** - using the same values as for a gas boiler because [SAP](https://www.bre.co.uk/filelibrary/SAP/2012/SAP-2012_9-92.pdf)
assumptions for a condensing oil boiler are very similar to those for modern condensing gas combi. 


### Solar output calculation

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


### Emissions factors

Gas and oil numbers from BEIS UK Government GHG Conversion Factors for Company Reporting, kWh (Net CV) for Natural gas 
and Burning oil.
Electricity emissions factors are UK average from the start of 2022 to 2022-10-26. Data from 
[National Grid ESO](https://data.nationalgrideso.com/carbon-intensity1/historic-generation-mix/r/historic_gb_generation_mix).

### Tariffs

The default tariffs for gas and electricity are based on the average rate under the
[Energy Price Guarantee](https://www.gov.uk/government/publications/energy-bills-support/energy-bills-support-factsheet-8-september-2022),
which is active until April 2023.
Without further government support, bills will increase after that date, at least in the short term. 
The oil tariff is a rough average based on [Boiler Juice](https://www.boilerjuice.com/heating-oil-prices/) 
data since prices stabilised in April 2022.


