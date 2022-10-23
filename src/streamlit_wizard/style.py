from pathlib import Path

import streamlit as st

this_file = Path(__name__)

primary_hue = 158

primary_dark = f'hsl({primary_hue},50%,50%)'
primary_light = f'hsl({primary_hue},50%,90%)'
primary_desat = f'hsl({primary_hue},5%,95%)'

style = """

/* Remove the labels on selectboxes */
label.css-15tx938 {
    display: None;
}

p {
    font-size: 0.9em;
    color: hsl(0, 0%, 5%);
}


.title {
    font-size: 2.8em;
    font-weight: bold;
    line-height: 1.1em;
}

.description {
 font-size: 1.4em;
 color: hsl(158, 10%, 40%);

}

h2 {
    font-size: 1.6em;
    font-weight: bold;
    line-height: 1.4em;
    space-after: 1em;
}

/* This is the main container */
#root > div:nth-child(1) > div.withScreencast > div > div > div > section > div > div:nth-child(1) > div > div:nth-child(2) > div{
    
    border-radius: 10px;
    box-shadow: 0 1px 5px hsla(0, 0%, 0%, .3);
    background-color: white;
    box-sizing: content-box;
    
    margin: 0 auto;
    padding: 30px;
}


#text {
    padding: 10px;
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
