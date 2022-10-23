
# -*- coding: utf-8 -*-

# copied from https://github.com/navdeep-G/samplemod/blob/master/setup.py

from setuptools import setup


with open('README.md') as f:
    readme = f.read()

setup(
    name='heat_pump_and_solar_savings',
    version='0.1.0',
    description='Calculate savings from installing solar and a heat pump',
    long_description=readme,
    author='Steph Willis',
    author_email='stephaniewillis808@gmail.com',
    url='https://github.com/StephanieWillis/solar-and-heat-pump-savings'
)