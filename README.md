# Heat pump and solar savings

Web app to calculate bill and carbon savings from installing solar, a heat pump, or both. Calculations account for proportion
of solar generation that is used within the home vs. exported. 

Calculations are hourly rather than half-hourly because the Solar generation API we are using gives hourly results.

## Data sources

### Electricity demand excluding space and water heating

#### Annual totals
Table 2 of [this report](https://www.energysavingtrust.org.uk/sites/default/files/reports/PoweringthenationreportCO332.pdf)
has overall values

2900 for elec typical apparently

#### Hourly profiles
Using Elexon's user demand profile data for Domestic Unrestricted (single rate) customers (Class 1). 
This data gives an averaged demand profile for this user class, as explained [here
](https://bscdocs.elexon.co.uk/guidance-notes/load-profiles-and-their-use-in-electricity-settlement).
The fact that this data is averaged isn't ideal because it is likely smoother than a real demand profile and so may give
estimates of solar self-use that are too high. The data also likely includes some households that use some electric resistance heating
which may mean that we are double counting a small amount of heating consumption. If you know of better data that gets around 
these problems please get in touch!

Demand profiles in other sources such as [this paper](https://www.researchgate.net/publication/324141791_The_potential_for_peak_shaving_on_low_voltage_distribution_networks_using_electricity_storage)
and [this report](https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/208097/10043_R66141HouseholdElectricitySurveyFinalReportissue4.pdf)
are largely consistent with the elexon profiles, but they do show slightly lower winter peak demand. 

Thanks to the [cutmyenergybill project](https://github.com/cutmyenergybill/domestic-energy-bill-reduction-app/)
for alerting me to this dataset. 

Still to do: Assign days to seasons. Note half hourly
so needs splitting. Credit cutmyenergybill project if use 
this. That app uses a heating degree day approach to gas use. Not ideal.


### Heat demand
We took annual heating demand values and half-hourly heating demand profiles from the UKERC dataset
["Spatio-temporal heat demand for LSOAs in England and Wales"](https://ukerc.rl.ac.uk/DC/cgi-bin/edc_search.pl?WantComp=165).
The methodology use to produce this data can be found in [this paper](https://www.nature.com/articles/s41597-022-01356-9),
and the code itself can be found [here](https://github.com/AlexandreLab/UKERC-data).

#### Annual totals

To get indicative values of annual heating demand by building type we used the 'Annual_heating_demand_LSOA' data and 
took the weighted average for each system/built form combination. We used the values for homes with gas boilers and 
without energy efficiency upgrades on the basis they are likely to be most representative of the typical stock. The
resulting values are hard coded in constants.HEATING_DEMAND_BY_BUILT_FORM
Could at a later use values specific ot the local area using [this sort of data
](https://www.data.gov.uk/dataset/9b090605-9861-4bb4-9fa4-6845daa2de9b/postcode-to-output-area-to-lower-layer-super-output-area-to-middle-layer-super-output-area-to-local-authority-district-february-2018-lookup-in-the-uk)

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

# TODO: check SAP elec carbon, apparently its 0.136

### Tariffs

The default tariffs for gas and electricity are based on the average rate under the
[Energy Price Guarantee](https://www.gov.uk/government/publications/energy-bills-support/energy-bills-support-factsheet-8-september-2022),
which is active until April 2023.
Without further government support, bills will increase after that date, at least in the short term. 
The oil tariff is a rough average based on [Boiler Juice](https://www.boilerjuice.com/heating-oil-prices/) 
data since prices stabilised in April 2022.


### Possible cost data
Heat pump cost tool, doesn't work all that well: [here](http://asf-hp-cost-demo-l-b-1046547218.eu-west-1.elb.amazonaws.com)


