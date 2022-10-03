import streamlit as st
import roof

polygons = roof.roof_mapper(800, 400)

if polygons:
    print([p.dimensions for p in polygons])