import setuptools
from setuptools import setup, find_packages

setup(
    name="codehackscalculator",              # Required: Name of the package
    version="0.0.1",                  # Required: Version of the package
    author="Bogoljub Stankovic",             # Optional: Author's name
    author_email="bob.stankovic@gov.ab.ca",  # Optional: Author's email
    description="A basic calculations",  # Optional: Brief description
    long_description=open("README.md").read(),  # Optional: Long description from README
    long_description_content_type="text/markdown",  # Optional: Content type of long description
    url="https://bogoljubstankovic.com",  # Optional: Project URL
    packages=setuptools.find_packages(),        # Required: Automatically find packages
    install_requires=[               # Optional: List of dependencies
        "numpy",
        "requests",
    ],
    classifiers=[                    # Optional: Additional metadata
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',         # Optional: Python version compatibility
    project_urls={                   # Optional: Information about the source code of the package. If you want to open-source your package. You can create a public repository and add its link here.
        "Documentation": "project documentation",
       
    },
)
