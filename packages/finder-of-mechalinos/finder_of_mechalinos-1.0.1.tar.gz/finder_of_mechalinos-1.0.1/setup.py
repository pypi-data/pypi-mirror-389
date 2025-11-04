from setuptools import setup, find_packages

setup(
    name="finder-of-mechalinos",
    version="1.0.1",
    description="Tool to discover Mechalino robots on a local network",
    author="Khalil Youssefi",
    author_email="kh4lil@outlook.com",
    license="MIT",
    packages=find_packages(),
    install_requires=["netifaces", "scapy"],
    entry_points={
        "console_scripts": [
            "finder-of-mechalinos=finder_of_mechalinos.main:cli",
        ],
    },
)