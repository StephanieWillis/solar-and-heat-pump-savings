""""""

import streamlit as st
heating_system = st.selectbox('Heating System', options=['Gas Boiler', 'Direct Electric', 'Heat Pump'])
st.write(f'Your heating system is a {heating_system}')