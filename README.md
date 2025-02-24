# QDU QCoDeS drivers
This repository host QCoDeS drivers for QDU Lab instruments. The repository includes custom versions of QCoDeS instrument drivers and QCoDeS contrib drivers as well as original drivers for instruments used in QDU Lab.
# Quickstart

## Prerequisites
The drivers in this repository work in conjuntction wuth  QCoDeS. Start by installing QCoDeS https://github.com/QCoDeS/Qcodes.

## Installation
You can install drivers with pip directly from GitHub repository:
```
pip install git+https://github.com/QDU-lab/qdu_qcodes_drivers.git@main
```

If you want an editable install first clone curent repository locally:
```
git clone https://github.com/QDU-lab/qdu_qcodes_drivers.git
```

And then install with pip
```
cd pyplotter
pip install -e .
```
