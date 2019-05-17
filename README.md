# Mercator: Dense Wireless Connectivity Datasets for the IoT

<img src="https://raw.githubusercontent.com/wiki/openwsn-berkeley/mercator/figures/mercator.jpg" align="left">

**Mercator** is a collection of tools to gather connectivity traces, which are:
* **dense in time**, meaning the connectivity is continuously assessed over a long period of time; it allows one to see variation of connectivity over time.
* **dense in space**, meaning the connectivity is assessed over hundreds of measurements points; it allows one to see how connectivity is affected by the location of transmitter and receivers.
* **dense in frequency**, meaning the connectivity is assessed for each of the 16 IEEE802.15.4 frequencies; it allows one to see how connectivity is affected by the communication frequency.

## Get Mercator
1. Make sure you have Python 3 installed (Python 2 is not supported)
1. Clone or download Mercator repository
1. Move into your local Mercator repository
1. Install required Python packages: `$ pip install -r requirements.txt`

## How to Run Mercator
1. Edit mercator.yml as you like
1. Run `mercator.py`
