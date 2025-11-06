from setuptools import setup, find_packages

setup(
    name="thermohi_hikari",
    version='0.1.2',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'matplotlib'
    ],
    python_requires='>=3.9',
    author='Hikari Quicklime',
    description='Thermal analysis toolkit for non-isothermal kinetic analysis (FWO, KAS, Starink, etc.)',
    url='https://github.com/QuicklimeHikari/thermohi'
)