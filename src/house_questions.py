""" Using session state solution described here for assumptions:
https://discuss.streamlit.io/t/make-a-widget-remember-its-value-after-it-is-hidden-and-shown-again-in-later-script-runs/29702/2"""

from typing import Dict

import streamlit as st

import constants
from building_model import House, BuildingEnvelope, HeatingSystem, Tariff
from fuels import Fuel


def get_house_from_session_state_if_exists_or_create_default():
    if "house" not in st.session_state:
        house = set_up_default_house()
        st.session_state.house = house
    else:
        house = st.session_state.house
    return house


def render(house: House) -> House:

    st.header("Start by telling us about your home")
    st.markdown(
        f"<p class='more-info'> If you know lots more about your home and tariff, you can"
        f"  <a  href='javascript:document.getElementsByClassName({constants.CLASS_NAME_OF_SIDEBAR_DIV}"
        f")[1].click();' target='_self'> enter more details here!</a></p>",
        unsafe_allow_html=True,
    )

    # Both functions below take whole house so can reset consumption
    house = render_building_envelope_questions(house=house)
    house = render_heating_system_questions(house=house)
    if st.session_state.heating_fuel_changed:
        house.tariffs = update_tariffs_for_new_heating_fuel(heating_fuel=house.heating_system.fuel,
                                                            tariffs=house.tariffs)
    house = render_house_assumptions_sidebar(house=house)

    render_results(house)
    return house


def set_up_default_house() -> "House":
    print("Setting up default house")
    envelope = BuildingEnvelope.from_building_type_constants(constants.BUILDING_TYPE_OPTIONS["Terrace"])
    heating_system_name = list(constants.DEFAULT_HEATING_CONSTANTS.keys())[0]
    house = House.set_up_from_heating_name(envelope=envelope, heating_name=heating_system_name)
    st.session_state.heating_fuel_changed = False
    return house


def render_building_envelope_questions(house: House) -> House:
    envelope = house.envelope
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.write("I live in a")
        with col2:
            if "house_type" not in st.session_state:
                st.session_state.house_type = envelope.house_type
                write_house_type_variables_to_session_state(envelope=envelope)
                write_heating_consumption_to_session_state(house)
                st.session_state.upgrade_heating_system_cost_needs_resetting = False

            house_type = st.selectbox("", options=constants.BUILDING_TYPE_OPTIONS.keys(), key="house_type",
                                      on_change=flag_change_in_house_type)

            if st.session_state.house_type_changed:  # only overwrite if house type changed by user
                print("Behaves as if house changed")
                envelope = BuildingEnvelope.from_building_type_constants(constants.BUILDING_TYPE_OPTIONS[house_type])
                write_house_type_variables_to_session_state(envelope=envelope)
                house.envelope = envelope
                write_heating_consumption_to_session_state(house)  # so change of house type changes consumption
                st.session_state.upgrade_heating_system_cost_needs_resetting = True
                st.session_state.baseline_heating_system_cost_needs_resetting = True

    return house


def write_house_type_variables_to_session_state(envelope: BuildingEnvelope):
    st.session_state.house_type_changed = False

    st.session_state.annual_heating_demand = int(envelope.annual_heating_demand)
    st.session_state.heating_demand_changed = False

    st.session_state.annual_base_demand = int(envelope.base_demand.sum())
    st.session_state.base_demand_changed = False


def write_heating_consumption_to_session_state(house: House):
    st.session_state.annual_heating_consumption = int(house.heating_consumption.overall.annual_sum_fuel_units)


def flag_change_in_house_type():
    st.session_state.house_type_changed = True


def render_heating_system_questions(house: House) -> House:
    heating_system = house.heating_system
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.write("My home is heated with a")
        with col2:
            if "heating_system_name" not in st.session_state:
                st.session_state.heating_system_name = heating_system.name
                st.session_state.heating_fuel_name = heating_system.fuel.name
                write_baseline_heating_system_to_session_state(heating_system=heating_system)
                st.session_state.baseline_heating_system_cost_needs_resetting = False

            name = st.selectbox(
                "", options=list(constants.DEFAULT_HEATING_CONSTANTS.keys()), key="heating_system_name",
                on_change=flag_change_in_heating_system)

            if st.session_state.heating_system_changed:  # only overwrite heating system if changed by user
                print("Behaves as if heating system changed")
                heating_system = HeatingSystem.from_constants(name=name,
                                                              parameters=constants.DEFAULT_HEATING_CONSTANTS[name])
                write_baseline_heating_system_to_session_state(heating_system=heating_system)
                house.heating_system = heating_system
                write_heating_consumption_to_session_state(house=house)
                st.session_state.baseline_heating_system_cost_needs_resetting = True

    return house


def write_baseline_heating_system_to_session_state(heating_system: HeatingSystem):
    if heating_system.fuel.name != st.session_state.heating_fuel_name:
        print(f"Behaves as if heating fuel changed")
        st.session_state.heating_fuel_changed = True  # flag change so tariff changes
        st.session_state.heating_fuel_name = heating_system.fuel.name

    st.session_state.baseline_heating_efficiency = heating_system.efficiency
    st.session_state.heating_system_changed = False
    st.session_state.baseline_heating_efficiency_changed = False


def flag_change_in_heating_system():
    st.session_state.heating_system_changed = True


def update_tariffs_for_new_heating_fuel(heating_fuel: Fuel, tariffs: Dict[str, Tariff]):
    st.session_state.heating_fuel_changed = False
    if heating_fuel.name != 'electricity':  # if heating fuel is electric then use elec tariff already defined
        heating_tariff = Tariff.set_up_heating_tariff(heating_system_fuel=heating_fuel)
        tariffs[heating_fuel.name] = heating_tariff
        write_heating_tariffs_to_sessions_state(tariff=heating_tariff)
    return tariffs


def render_house_assumptions_sidebar(house: House) -> House:
    with st.sidebar:
        st.header("Assumptions")
        st.markdown(
            "<p>If you know details of your current usage or tariff, enter below for greater accuracy</p>",
            unsafe_allow_html=True,
        )
        st.subheader("Current Performance")
        house = render_house_overwrite_options(house)
    return house


def render_house_overwrite_options(house: House):
    """ Split out because used on savings page and front page"""
    with st.expander("Baseline heating system"):
        house.heating_system = render_baseline_heating_system_overwrite_options(house=house)
    with st.expander("Energy use"):
        house.envelope = render_consumption_overwrite_options(house=house)
    with st.expander("Tariff"):
        house.tariffs = render_tariff_overwrite_options(tariffs=house.tariffs, fuel_name=house.heating_system.fuel.name)
    st.text("")  # to add some space
    return house


def render_baseline_heating_system_overwrite_options(house: "House") -> "HeatingSystem":
    st.number_input(
        label="Efficiency: ",
        min_value=0.1,
        max_value=8.0,
        value=st.session_state.baseline_heating_efficiency,
        key="baseline_heating_efficiency_overwrite",
        on_change=overwrite_baseline_heating_efficiency_in_session_state)

    if st.session_state.baseline_heating_efficiency_changed:
        house.heating_system.efficiency = st.session_state.baseline_heating_efficiency
        write_heating_consumption_to_session_state(house)  # so change of heating efficiency changes consumption
        st.session_state.baseline_heating_efficiency_changed = False

    if house.heating_system.fuel.name == "gas":
        st.caption(
            "Many boilers have a low efficiency because they run at a high a flow temperature. "
            "Your boiler may be able to run at 90% or better but in most cases the flow temperature will be too high to"
            " achieve the boiler's advertised efficiency. "
            "You can learn how to turn down your flow temperature "
            "[here](https://www.nesta.org.uk/project/lowering-boiler-flow-temperature-reduce-emissions)."
        )
    return house.heating_system


def overwrite_baseline_heating_efficiency_in_session_state():
    st.session_state.baseline_heating_efficiency = st.session_state.baseline_heating_efficiency_overwrite
    st.session_state.baseline_heating_efficiency_changed = True


def render_consumption_overwrite_options(house: 'House') -> BuildingEnvelope:

    heat_label = f"{house.heating_system.fuel.name.capitalize()} use for heat/hot water" \
                 f" ({house.heating_system.fuel.units})"
    st.number_input(
        label=heat_label,
        min_value=0,
        max_value=100000,
        value=st.session_state.annual_heating_consumption,
        key="annual_heating_consumption_overwrite",
        on_change=overwrite_heating_consumption_in_session_state)

    envelope = house.envelope
    if st.session_state.heating_demand_changed:  # scale profile  by correction factor
        print("Behaves as if heating demand changed")
        mult = st.session_state.annual_heating_consumption/int(house.heating_consumption.overall.annual_sum_fuel_units)
        envelope.annual_heating_demand = envelope.annual_heating_demand * mult
        st.session_state.annual_heating_demand = int(envelope.annual_heating_demand)
        st.session_state.heating_demand_changed = False

    st.number_input(
        label="Electricity use for lighting, appliances, etc. (kwh): ",
        min_value=0,
        max_value=100000,
        value=st.session_state.annual_base_demand,
        key="annual_base_demand_overwrite",
        on_change=overwrite_base_demand_in_session_state
    )
    if st.session_state.base_demand_changed:  # scale profile  by correction factor
        print("Behaves as if base demand changed")
        multiplier = st.session_state.annual_base_demand / int(envelope.base_demand.sum())
        envelope.base_demand = house.envelope.base_demand * multiplier
        st.session_state.base_demand_changed = False

    typical_heat_demand = constants.BUILDING_TYPE_OPTIONS[house.envelope.house_type].annual_heat_demand_kWh
    typical_heat_consumption = house.heating_system.calculate_consumption(typical_heat_demand)
    if house.envelope.house_type == "Flat":
        house_name = house.envelope.house_type.lower()
    else:
        house_name = f"{house.envelope.house_type.lower()} house"
    st.caption(
        f"A typical {house_name} heated with this {house.heating_system.name.lower()} needs"
        f" {int(typical_heat_consumption.overall.annual_sum_fuel_units):,} {house.heating_system.fuel.units} of "
        f"{house.heating_system.fuel.name} for heating and hot water, and "
        f"{constants.BUILDING_TYPE_OPTIONS[house.envelope.house_type].annual_base_electricity_demand_kWh:,} kWh of "
        f"electricity for lighting, appliances, etc.  \n\n"
        f"The better insulated your home, the less energy it will need for heating. "
    )
    return envelope


def overwrite_heating_consumption_in_session_state():
    st.session_state.annual_heating_consumption = st.session_state.annual_heating_consumption_overwrite
    st.session_state.heating_demand_changed = True


def overwrite_base_demand_in_session_state():
    st.session_state.annual_base_demand = st.session_state.annual_base_demand_overwrite
    st.session_state.base_demand_changed = True


def render_tariff_overwrite_options(tariffs: Tariff, fuel_name: "str") -> Tariff:
    st.subheader("Electricity")

    if "p_per_unit_elec_import" not in st.session_state:
        write_elec_tariff_to_session_state(tariff=tariffs["electricity"])

    st.number_input(label="Unit rate (p/kwh), electricity import", min_value=0.0, max_value=100.0,
                    value=st.session_state.p_per_unit_elec_import, key="p_per_unit_elec_import_overwrite",
                    on_change=overwrite_elec_p_per_unit_import_in_session_state)

    st.number_input(label="Unit rate (p/kwh), electricity export", min_value=0.0, max_value=100.0,
                    value=st.session_state.p_per_unit_elec_export, key="p_per_unit_elec_export_overwrite",
                    on_change=overwrite_elec_p_per_unit_export_in_session_state)

    st.number_input(label="Standing charge (p/day), electricity", min_value=0.0, max_value=100.0,
                    value=st.session_state.p_per_day_elec, key="p_per_day_elec_overwrite",
                    on_change=overwrite_elec_p_per_day_in_session_state)

    tariffs["electricity"].p_per_unit_import = st.session_state.p_per_unit_elec_import
    tariffs["electricity"].p_per_unit_export = st.session_state.p_per_unit_elec_export
    tariffs["electricity"].p_per_day = st.session_state.p_per_day_elec

    if 'p_per_unit_heating_fuel_import' not in st.session_state:
        write_heating_tariffs_to_sessions_state(tariff=tariffs[fuel_name])

    match fuel_name:  # only need to define other tariff if heating fuel is gas or oil as elec already defined
        case "gas":
            st.subheader("Gas")
            st.number_input(label="Unit rate (p/kwh), gas", min_value=0.0, max_value=100.0,
                            value=st.session_state.p_per_unit_heating_fuel_import,
                            key="p_per_unit_heating_fuel_import_overwrite",
                            on_change=overwrite_p_per_unit_heating_fuel_import)
            st.number_input(label="Standing charge (p/day), gas", min_value=0.0, max_value=100.0,
                            value=st.session_state.p_per_day_heating_fuel,
                            key="p_per_day_heating_fuel_overwrite",
                            on_change=overwrite_p_per_unit_heating_fuel_import)

            tariffs["gas"].p_per_unit_import = st.session_state.p_per_unit_heating_fuel_import
            tariffs["gas"].p_per_day = st.session_state.p_per_day_heating_fuel

        case "oil":
            st.subheader("Oil")
            st.number_input(label="Oil price, (p/litre)", min_value=0.0, max_value=200.0,
                            value=st.session_state.p_per_unit_heating_fuel_import,
                            key="p_per_unit_heating_fuel_import_overwrite",
                            on_change=overwrite_p_per_unit_heating_fuel_import)

            tariffs["oil"].p_per_unit_import = st.session_state.p_per_unit_heating_fuel_import

    st.caption(
        "Our default tariffs reflect the current [Energy Price Guarantee]("
        "https://www.gov.uk/government/publications/energy-bills-support/energy-bills-support-factsheet-8-september-2022)"
        " which is in place until April, but you can change them if you have fixed at a different rate."
    )

    return tariffs


def write_elec_tariff_to_session_state(tariff: Tariff):
    st.session_state.p_per_unit_elec_import = tariff.p_per_unit_import
    st.session_state.p_per_unit_elec_export = tariff.p_per_unit_export
    st.session_state.p_per_day_elec = tariff.p_per_day


def write_heating_tariffs_to_sessions_state(tariff: Tariff):
    st.session_state.p_per_unit_heating_fuel_import = tariff.p_per_unit_import
    st.session_state.p_per_day_heating_fuel = tariff.p_per_day


def overwrite_elec_p_per_unit_import_in_session_state():
    st.session_state.p_per_unit_elec_import = st.session_state.p_per_unit_elec_import_overwrite


def overwrite_elec_p_per_unit_export_in_session_state():
    st.session_state.p_per_unit_elec_export = st.session_state.p_per_unit_elec_export_overwrite


def overwrite_elec_p_per_day_in_session_state():
    st.session_state.p_per_day_elec = st.session_state.p_per_day_elec_overwrite


def overwrite_p_per_unit_heating_fuel_import():
    st.session_state.p_per_unit_heating_fuel_import = st.session_state.p_per_unit_heating_fuel_import_overwrite


def overwrite_p_per_day_heating_fuel():
    st.session_state.p_per_day_heating_fuel = st.session_state.p_per_day_heating_fuel_overwrite


def render_results(house: House):
    st.markdown(
        f"<div class='results-container'>"
        f"<p class='bill-label'>Your bill next year will be around <p>"
        f"<p class='bill-estimate'>£{int(house.total_annual_bill):,d}"
        f"</p>"
        f"<p class='bill-details'>Based on estimated usage of "
        f"<a class='bill-consumption-kwh' href='javascript:document.getElementsByClassName("
        f"{constants.CLASS_NAME_OF_SIDEBAR_DIV})[1].click();' target='_self'>"
        f"{int(house.total_annual_consumption_kwh):,d} kwh</a> </p>"
        f"</div>",
        unsafe_allow_html=True,
    )
