# Heat pump and solar savings


Web app to estimate bill and carbon savings from installing solar, a heat pump, or both in a home. 
Calculations account for proportion of solar generation that is used within the home vs. exported. 

Calculations are hourly rather than half-hourly because the Solar generation API we are using gives hourly results.

## Running

```
docker compose up

or 

pip install requirements.txt
cd src
streamlit run main.py 
```

## Solar output calculation

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

## Data sources

### Electricity demand excluding space and water heating

#### Annual totals
Annual electricity demand excluding space and water hetaing is from Table 2 of 
[this energy savings trust report](https://www.energysavingtrust.org.uk/sites/default/files/reports/PoweringthenationreportCO332.pdf)
The numbers are a good match for other sources such as the [ECUK 2022:Consumption data tables
](https://www.gov.uk/government/statistics/energy-consumption-in-the-uk-2022).

#### Hourly profiles
Using Elexon's user demand profile data for Domestic Unrestricted (single rate) customers (Class 1). 
This data gives an averaged demand profile for this user class, as explained [here
](https://bscdocs.elexon.co.uk/guidance-notes/load-profiles-and-their-use-in-electricity-settlement). 
Thanks to the [cutmyenergybill project](https://github.com/cutmyenergybill/domestic-energy-bill-reduction-app/)
for alerting me to this dataset. The fact that this data is averaged isn't ideal because it is likely smoother than a real demand profile and so may give
estimates of solar self-use that are too high. The data also likely includes some households that use some electric resistance heating
which may mean that we are double counting a small amount of heating consumption. If you know of better data that gets around 
these problems please let me know. 

Demand profiles in other sources such as [this paper](https://www.researchgate.net/publication/324141791_The_potential_for_peak_shaving_on_low_voltage_distribution_networks_using_electricity_storage)
and [this report](https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/208097/10043_R66141HouseholdElectricitySurveyFinalReportissue4.pdf)
are largely consistent with the elexon profiles, but they do show slightly lower winter peak demand. 


### Heat demand
We took annual heating demand values and half-hourly heating demand profiles from the UKERC dataset
["Spatio-temporal heat demand for LSOAs in England and Wales"](https://ukerc.rl.ac.uk/DC/cgi-bin/edc_search.pl?WantComp=165).
The methodology use to produce this data can be found in [this paper](https://www.nature.com/articles/s41597-022-01356-9),
and the code itself can be found [here](https://github.com/AlexandreLab/UKERC-data).

#### Annual totals

To get indicative values of annual heating demand by building type we used the 'Annual_heating_demand_LSOA' data and 
took the weighted average for each system/built form combination. We used the values for homes with gas boilers and 
without energy efficiency upgrades on the basis they are likely to be most representative of the typical stock. The
resulting values are hard coded in the constants module.

To corroborate the above, this [nesta analysis
](https://www.nesta.org.uk/report/reduce-the-cost-of-heat-pumps/))
uses small, medium and large heat demand at 9500kWh, 14,500kWh, and 22,000 kWh respectively. This agrees well with the 
averages produced using the process described above.

#### Hourly profiles
Half-hourly heating demand profiles for each heating system are taken from the UKERC dataset
["Spatio-temporal heat demand for LSOAs in England and Wales"](https://ukerc.rl.ac.uk/DC/cgi-bin/edc_search.pl?WantComp=165).

From their Readme: "The normalised profiles have been temperature corrected based on the number of degree days difference between a typical 
year and year 2013. Hence, the sum of the values of a normalised heat production profile is equal to 0.961203 instead of 1.""
In the step where we pickle the demand profile we normalize it so the profiles sum to 1.

### Heating system efficiencies

**Heat pumps** - using rounded values from 5 kW 
[Vaillant arotherm SCOP data](https://www.vaillant.co.uk/downloads/aproducts/renewables-1/arotherm-plus/arotherm-plus-1/quick-guides/new-5/installers-quick-guide-arotherm-plus-1949445.pdf),
 with flow temperature of 55C. These efficiencies are above
recorded averages (2.76 according to this [nesta analysis](https://www.nesta.org.uk/report/reduce-the-cost-of-heat-pumps/))
but lower than reported values for high quality installs.

**Gas boiler** - using 84%, as used in this 
[Delta EE report](https://www.climatexchange.org.uk/media/1897/electrification_of_heat_and_impact_on_scottish_electricity_system_-_final_report1.pdf)). Using 80% for water heating due to lower
efficiencies in the summer when the boiler only heats hot water.

**Oil boiler** - using the same values as for a gas boiler because [SAP](https://www.bre.co.uk/filelibrary/SAP/2012/SAP-2012_9-92.pdf)
assumptions for a condensing oil boiler are very similar to those for modern condensing gas combi. 


### Emissions factors

Gas and oil numbers from [BEIS UK Government GHG Conversion Factors for Company Reporting](https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2022)
, kWh (Net CV) for Natural gas and Burning oil.
Electricity emissions factors are UK average from the start of 2022 to 2022-10-26. Data from 
[National Grid ESO](https://data.nationalgrideso.com/carbon-intensity1/historic-generation-mix/r/historic_gb_generation_mix).


### Tariffs

The default tariffs for gas and electricity are based on the average rate under the
[Energy Price Guarantee](https://www.gov.uk/government/publications/energy-bills-support/energy-bills-support-factsheet-8-september-2022),
which is active until April 2023.
Without further government support, bills will increase after that date, at least in the short term. Some clues
as where rates might go in [this Cornwall Insights analysis](https://www.cornwall-insight.com/predicted-fall-in-the-april-2023-price-cap-but-prices-remain-significantly-above-the-epg/)
and [this nesta analysis](https://www.nesta.org.uk/report/how-the-energy-crisis-affects-the-case-for-heat-pumps/how-the-costs-of-heat-pumps-compare-to-gas-boilers-since-the-energy-crisis-1/#content)
The oil tariff is a rough average based on [Boiler Juice](https://www.boilerjuice.com/heating-oil-prices/) 
data since prices stabilised in April 2022.


### Cost data
Solar costs are from [BEIS data](https://www.data.gov.uk/dataset/738a7bdb-a533-443d-bd02-69a8dd7fe68d/solar-pv-cost-data)
for 2021/22 installs accredited under MCS. 
We used the upper confidence interval given prices have likely risen since 2021/2022

Heat pump and gas boiler costs from Nesta's [How to reduce the cost of heat pupms report](
https://media.nesta.org.uk/documents/How_to_reduce_the_cost_of_heat_pumps_v4_1.pdf)
- Used tables 1 (for semi only) and 2 (for terrace, flat, detached) from
- Corrected gas boiler cost for semi-detached by same amount as heat pump shifts to keep equivalent
- Assumed oil and direct electric baseline costs are the same as gas boiler costs. This is probably a poor assumption in the direct electric case

The Nesta prices were in £2021 so we inflated the figures by ratio of retail price index from [Oct 2021](
https://www.crosslandsolicitors.com/site/hr-hub/October-2021-inflation-data-CPI-CPIH-RPI) to [Oct 2022](
https://www.crosslandsolicitors.com/site/media/October-2022-inflation-data-CPI-CPIH-RPI). That amounts
to a 14% cost increase.

Other relevant cost resources [here](
https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/656866/BEIS_Update_of_Domestic_Cost_Assumptions_031017.pdf)
and [here](
https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/1104051/CODE-Final-Report-WHOLE-FINAL-v20.pdf)

Grant: [Boiler Upgrade Scheme](https://www.gov.uk/apply-boiler-upgrade-scheme/what-you-can-get)



