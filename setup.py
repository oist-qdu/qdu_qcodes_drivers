from setuptools import setup, find_packages

exec(open('qdu_qcodes_drivers/_version.py').read())

setup(
    name='qdu_qcodes_drivers',
    version=__version__,
    packages=find_packages(), 
    install_requires=[]
)