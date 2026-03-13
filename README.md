# QDU QCoDeS drivers
This repository host QCoDeS drivers for QDU Lab instruments. The repository includes custom versions of QCoDeS instrument drivers and QCoDeS contrib drivers as well as original drivers for instruments used in QDU Lab.
# Quickstart

## Prerequisites
The drivers in this repository work in conjuntction wuth  QCoDeS. Start by installing QCoDeS https://github.com/QCoDeS/Qcodes.

## Installation
You can install drivers with pip directly from GitHub repository:
```
pip install git+https://github.com/QDU-lab/qdu_qcodes_drivers.git
```
In this case you can find drivers in python folder envs/%your environment name%/Lib/site-packages/qdu_qcodes_drivers

If you plannig to make changes in drivers, you need editable installation.
First clone the repository to your git folder:
```
git clone https://github.com/QDU-lab/qdu_qcodes_drivers.git
```

And then go to repository folder and make editable install with pip
```
cd qdu_qcodes_drivers
pip install -e .
```
In this case drivers files will be in your git folder. You can edit them and push them back to origin repository. 

## Modification
In case of editable installation you can easily commit changes back to GitHub repository.

First, you can check what files was modified
```
git status
```
Second, stage files with changes:
```
git add qdu_qcodes_drivers/file1.py
...
git add qdu_qcodes_drivers/fileN.py
```
Or add all files that have been modified:
```
git add -A
```
Commit changes with a short message:
```
git commit -m "changes I made to screw everything"
```
Finally, upload changes to GitHub:
```
git push origin
```
