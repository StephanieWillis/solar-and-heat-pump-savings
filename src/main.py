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
            " Throughout the tool we have made estimates of various values, but you can overwrite them at the bottom "
            "of the Savings Potential page if you have better info."
        )


class UsagePage(Page):
    def render(self) -> dict:
        return dict(house=usage_questions.render())


class SolarPage(Page):
    def render(self) -> dict:
        return dict(solar=solar_questions.render())


class ResultsPage(Page):
    def render(self):
        house = st.session_state["page_state"]["usage"]["house"]
        solar = st.session_state["page_state"]["solar"]["solar"]
        savings_outputs.render(house=house, solar=solar)


wizard = Wizard(pages=[WelcomePage("welcome"), UsagePage("usage"), SolarPage("solar"), ResultsPage("results")])

st.title("Cut your bills with solar and a heat pump")
wizard.render()
