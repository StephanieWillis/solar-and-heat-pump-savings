import streamlit as st

import house_questions
import solar_questions
import savings_outputs
import next_steps

from streamlit_wizard import Wizard, Page

st.set_page_config(page_title="Heat pump or Solar?",
                   page_icon="https://storage.googleapis.com/static_heatpump_and_solar/heat_pump_icon.png",
                   initial_sidebar_state="collapsed")


class YourHousePage(Page):
    def render(self):
        house = house_questions.get_house_from_session_state_if_exists_or_create_default()
        house = house_questions.render(house=house)
        st.session_state.house = house


class SolarPage(Page):
    def render(self):
        solar_install = solar_questions.get_solar_install_from_session_state_if_exists_or_create_default()
        solar_install = solar_questions.render(solar_install=solar_install)
        st.session_state.solar_install = solar_install


class ResultsPage(Page):
    def render(self):
        # produce default version of house and solar for cases where user doesn't click through all the pages
        house = house_questions.get_house_from_session_state_if_exists_or_create_default()
        solar_install = solar_questions.get_solar_install_from_session_state_if_exists_or_create_default()
        upgrade_heating = savings_outputs.get_upgrade_heating_from_session_state_if_exists_or_create_default()

        house, solar_install, upgrade_heating = savings_outputs.render(house=house,
                                                                       solar_install=solar_install,
                                                                       upgrade_heating=upgrade_heating)
        st.session_state.house = house
        st.session_state.solar_install = solar_install
        st.session_state.upgrade_heating = upgrade_heating


class NextStepsPage(Page):
    def render(self):
        solar_install = solar_questions.get_solar_install_from_session_state_if_exists_or_create_default()
        next_steps.render(solar_install)


wizard = Wizard(pages=[YourHousePage("house"), SolarPage("solar"), ResultsPage("results"), NextStepsPage("next_steps")])

st.markdown(
    "<p class='title'>Cut your bills with solar + heat pump </p>"
    "<p class='description'> How much money and carbon can you save by installing a heat pump "
    "or solar panels? Get an estimate in 5 minutes!</p>",
    unsafe_allow_html=True,
)

wizard.render()

st.markdown("<p style='text-align: center; margin-top: 20px; font-size:14px'>🛠 Made by <a href='https://twitter.com/stephwillis808'>Stephanie Willis </a>"
         " and <a href='https://twitter.com/ArchydeB'> Archy de Berker </a><br/>"
            "Code is on <a href='https://github.com/StephanieWillis/solar-and-heat-pump-savings'>Github</a>"
            "<br> <br>Please get in touch with any feedback!</p>",
            unsafe_allow_html=True)
