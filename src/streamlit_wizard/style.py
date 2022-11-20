from pathlib import Path

import streamlit as st

this_file = Path(__name__)

primary_hue = 158

primary_dark = f"hsl({primary_hue},50%,50%)"
primary_light = f"hsl({primary_hue},50%,90%)"
primary_desat = f"hsl({primary_hue},5%,95%)"

style = """

/* Remove the labels on selectboxes on the first page*/
#root > div:nth-child(1) > div.withScreencast > div > div > div > section.main.css-1v3fvcr.egzxvld3 > div > div:nth-child(1) > div > div:nth-child(2) > div > div:nth-child(6) > div > div > div:nth-child(2) > div:nth-child(1) > div > div > div > label,
#root > div:nth-child(1) > div.withScreencast > div > div > div > section.main.css-1v3fvcr.egzxvld3 > div > div:nth-child(1) > div > div:nth-child(2) > div > div:nth-child(8) > div > div > div:nth-child(2) > div:nth-child(1) > div > div > div > label,
#root > div:nth-child(1) > div.withScreencast > div > div > div > section.main.css-1v3fvcr.egzxvld3 > div > div:nth-child(1) > div > div:nth-child(2) > div > div:nth-child(7) > div > div > div:nth-child(2) > div:nth-child(1) > div > div > div > label
 {
    display: none;
}


.results-container {
    text-align: center;
}

p {
    font-size: 1.1em;
    vertical-align: middle; 
    color: hsl(220, 10%, 10%);       
}

p.more-info {
    margin-top: -2em;
    margin-bottom: 2em;
}


p.bill-estimate {
    font-size: 2.8em;
    font-weight: bold;
    line-height: 1.1em;
    color: hsl(220, 60%, 30%);   
}

p.next-steps {
    font-size: 16px;
}

p.bill-label{
    font-size: 1.5em;
    color: hsl(220, 60%, 30%);
    
}

p.bill-details, div.install-disclaimer{
    font-size: 1em;
    color: hsl(220, 30%, 70%);   
}

p.green {
    color: hsl(140, 60%, 25%);
}

p.snug {
    margin-top: 0;
    line-height: .2em;
}
.bill-consumption-kwh {
    text-decoration-line: underline;
    text-decoration-style: dotted;
    cursor: pointer;
    color: hsl(220, 30%, 70%);  
}

.css-znku1x a {
   color: hsl(220, 30%, 70%); 
}

#postcode {
    
}


a:hover {
    color: hsl(220, 60%, 10%);
}

.results-container {
    margin-top: 40px;
}

.title {
    font-size: 2.8em;
    font-weight: bold;
    line-height: 1.1em;
}

.description {
 font-size: 1.4em;
 color: hsl(220, 10%, 40%);
 margin-bottom: 50px;

}

.css-1n76uvr.e1tzin5v0{
    margin-bottom: 10px;
}

h2 {
    font-size: 1.6em;
    font-weight: bold;
    line-height: 1.4em;
    margin-bottom: 1em;
    color: hsl(220, 10%, 30%);
}

h3 {
    margin-top: -1em;
    font-size: 1.2em;
    font-weight: bold;
    line-height: 1.4em;
    margin-bottom: .1em;
    color: hsl(220, 10%, 30%);
    scroll-margin-top: 50px;
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

button.css-sc7x0u.edgvbvh9 {
    background-color: hsl(220, 60%, 30%);
    color: hsl(0,0%,100%);    
}

.leaflet-draw-draw-polyline {
    display: None;
    color: blue;
}

/* Hiding the excess map drawing controls. Doesn't seem to work right now */
#map_div > div.leaflet-control-container > div.leaflet-top.leaflet-left > div.leaflet-draw.leaflet-control > div:nth-child(1) > div > a.leaflet-draw-draw-polyline {
    display: None
}

.leaflet-draw-draw-circlemarker {
    color: rgb(200,10,10);
}
                  

#root > div:nth-child(1) > div.withScreencast > div > div > div > section > div > div:nth-child(1) > div > div:nth-child(2) > div > div.css-434r0z.e1tzin5v4 > div:nth-child(2) > div:nth-child(1) > div > div > div > button{
    background-color: hsl(0,0%,100%);
    color: hsl(0,0%,0%); 
}

div.toc, p.toc, div.saving-maths {
    border-radius: 10px;
    background-color: hsl(220, 60%, 95%);
    color: hsl(220, 10%, 40%);
    padding: 15px;
    line-height: 15px;
    font-size: 18px;
    margin-bottom: 20px;
    font-weight: 600;
}

div.saving-maths {
 text-align: center;
 font-size: 14px;
 color: hsl(0, 0%, 31%, 1);
 padding: 30px;
 display: flex;
 flex-direction: column;
 justify-content: space-between;
 
}

p.install-disclaimer {
    text-weight:400;
    color: hsl(220, 30%, 70%);
    font-size: 10px;
    margin: 0;
}

p.saving-maths,p.saving-maths-headline {
    color: hsl(0, 0%, 31%);
    line-height:12px;
}

p.saving-maths-headline {
 font-size: 20px;
 font-weight: 700;
 space-after: 80px;
 display: block;
 margin: 10px;
}

a.toc {
font-weight: 600;
    text-decoration-line: underline;
    text-decoration-style: dotted;
    color: hsl(220, 10%, 40%);
}

p.toc, ul.toc, li.toc{
    list-style-type: none;
    margin: 0;
    padding: 5px 8px;
    line-height: 12px;
       
}

 ul.toc, li.toc {
 font-size: 15px;
 }

@media only screen and (max-width: 650px) {
  button.css-1q8dd3e {
    text-align: center;
    width: 100%;
  }
  
  #root > div:nth-child(1) > div.withScreencast > div > div > div > section > div > div:nth-child(1) > div > div:nth-child(2) > div {
  padding: 5px;
  box-shadow: None;
  }
  
   .title {
        font-size: 2em;
        text-decoration: underline;
        text-decoration-color: hsl(220, 90%, 30%);
   }
  .description{
     display: none;
  }
}


"""

style = style.replace("primary_desat", primary_desat)


def inject_style():
    """Reads a local stylesheet and injects it"""
    st.markdown("<style>" + style + "</style>", unsafe_allow_html=True)
