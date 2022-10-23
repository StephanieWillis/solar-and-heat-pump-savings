import streamlit as st

import usage_questions
import solar_questions
import savings_outputs

from streamlit_wizard import Wizard, Page


class WelcomePage(Page):
    def render(self) -> dict:
        st.write(
            "This tool helps you get a rough idea of how much money and carbon you might save by installing a "
            "heat pump and/or solar panels. The real costs and performance will depend on the specifics of your home."
            "  \n  \n"
            " Throughout the tool we will make estimates of various values based on your inputs."
            " You can overwrite those assumptions in the sidebar of the results page if you have better info."
        )


class UsagePage(Page):
    def render(self) -> dict:
        return dict(house=usage_questions.render())


class SolarPage(Page):
    def render(self) -> dict:
        return dict(solar=solar_questions.render())


class ResultsPage(Page):
    def render(self):
        house = st.session_state["page_state"]["house"]["house"]
        solar = st.session_state["page_state"]["solar"]["solar"]
        savings_outputs.render(house=house, solar=solar)


wizard = Wizard(pages=[UsagePage("house"),
                       SolarPage("solar"),
                       ResultsPage("results")])

st.markdown("<p class='title'>Cut your bills with solar + heat pump </p>"
            "<p class='description'> How much money and carbon can you save by installing a heat pump "
         "or solar panels? Get an estimate in 5 minutes!</p>", unsafe_allow_html=True)

wizard.render()
