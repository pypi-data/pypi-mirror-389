from setuptools import setup, find_packages

REQUIRED_PACKAGES = [
    'viggocorev2>=1.0.0,<2.0.0',
    'viggolocalv2>=1.0.0',
    'flask-cors'
]

setup(
    name="viggoparceirov2",
    version="1.0.5",
    summary='ViggoParceiroV2 Module Framework',
    description="ViggoParceiroV2 Backend Flask REST service",
    packages=find_packages(exclude=["tests"]),
    install_requires=REQUIRED_PACKAGES
)
