# setup.py

from setuptools import setup, find_packages

setup(
    name="ucbl_logger",
    version="0.14.0",
    description="A User-Centric Behaviour Log Markup Language Logger",
    author="Evan Erwee",
    author_email="evan@erwee.com",
    packages=find_packages(),
    install_requires=[
        'pytz',  # Add other dependencies here if needed
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",  # Updated for CC BY-NC-ND 4.0
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Topic :: Software Development :: Libraries",
    ],
    license="Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License",  # Updated license
    python_requires='>=3.6',
)
