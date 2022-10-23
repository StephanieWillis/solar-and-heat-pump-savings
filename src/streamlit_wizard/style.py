from pathlib import Path

import streamlit as st

this_file = Path(__name__)

primary_hue = 158

primary_dark = f'hsl({primary_hue},50%,50%)'
primary_light = f'hsl({primary_hue},50%,90%)'
primary_desat = f'hsl({primary_hue},5%,95%)'

style = """
p {
font-size: 1.2em;
color: hsl(0, 0%, 5%);
}




.title {
    font-size: 2.2em;
    font-weight: bold;
    line-height: 1.4em;
}

h2 {
    font-size: 1.2em;
    font-weight: bold;
    line-height: 1.4em;
}

/* This is the main container */

div.css-1n76uvr.e1tzin5v0{
    border-radius: 10px;
    padding: 40px;
    box-shadow: 0 1px 5px hsla(0, 0%, 0%, .3);
    background-color: white;
    overflow: wrap;
}

div.custom_centred {
    text-align: center;
}

button {
    box-shadow: 0 1px 1px hsla(0, 0%, 0%, .3);
}

@media only screen and (max-width: 650px) {
  button.css-1q8dd3e {
    text-align: center;
    width: 100%;
  }
}
"""

style = style.replace('primary_desat', primary_desat)


def inject_style():
    """Reads a local stylesheet and injects it"""
    st.markdown(
        "<style>" + style + "</style>", unsafe_allow_html=True
    )
