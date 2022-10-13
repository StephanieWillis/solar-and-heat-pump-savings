from pathlib import Path

import streamlit as st

this_file = Path(__name__)

style = """

p {
font-size: 1.2em;
}
div.css-1n76uvr.e1tzin5v0{
    border-radius: 10px;
    padding: 10px;
    border: 1px solid darkgray;
}

div.custom_centred {
    text-align: center;
}

@media only screen and (max-width: 650px) {
  button.css-1q8dd3e {
    text-align: center;
    width: 100%;
  }
}
"""


def inject_style():
    """Reads a local stylesheet and injects it"""
    st.markdown(
        "<style>" + style + "</style>", unsafe_allow_html=True
    )
