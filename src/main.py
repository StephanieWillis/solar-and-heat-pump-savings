import streamlit as st

import house_questions
import solar_questions
import savings_outputs

from streamlit_wizard import Wizard, Page

st.set_page_config(page_title="Solar or a heat pump?",
                   page_icon=" 🔥 ",
                   initial_sidebar_state="collapsed")


class YourHousePage(Page):
    def render(self) -> dict:
        return dict(house=house_questions.render())


class SolarPage(Page):
    def render(self) -> dict:
        return dict(solar=solar_questions.render())


class ResultsPage(Page):
    def render(self):
        # produce default version of house and solar for cases where user doesn't click through all the pages
        house = house_questions.get_house_from_session_state_if_exists_or_create_default()
        solar_install = solar_questions.get_solar_install_from_session_state_if_exists_or_create_default()

        savings_outputs.render(house=house, solar_install=solar_install)


wizard = Wizard(pages=[YourHousePage("house"), SolarPage("solar"), ResultsPage("results")])

st.markdown(
    "<p class='title'>Cut your bills with solar + heat pump </p>"
    "<p class='description'> How much money and carbon can you save by installing a heat pump "
    "or solar panels? Get an estimate in 5 minutes!</p>",
    unsafe_allow_html=True,
)

wizard.render()

st.write("Made by [Stephanie Willis](https://twitter.com/stephwillis808)"
         " and [Archy de Berker](https://twitter.com/ArchydeB). Please get in touch with any feedback!")
