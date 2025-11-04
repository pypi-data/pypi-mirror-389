from setuptools import setup, find_packages

REQUIRED_PACKAGES = [
    'viggocorev2>=1.0.0,<2.0.0',
    'flask-cors'
]

setup(
    name="viggolocalv2",
    version="1.0.0",
    summary='ViggoLocalV2 Module Framework',
    description="ViggoLocalV2 backend Flask REST service",
    packages=find_packages(exclude=["tests"]),
    install_requires=REQUIRED_PACKAGES
)
