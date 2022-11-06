import streamlit.components.v1 as components
from pathlib import Path

THIS_FILE = Path(__file__)

place_search = components.declare_component(
    "place_search",
    path=Path(THIS_FILE.parent)
)