"""
India Housing Datasets Library
------------------------------
A collection of open housing datasets for Indian cities.

Usage Example:
---------------
from india_housing_datasets import fetch_ahmedabad_housing

df = fetch_ahmedabad_housing()
print(df.head())
"""

from .ahmedabad import fetch_ahmedabad_housing
from .gurugram import fetch_gurugram_housing  
from .mumbai import fetch_mumbai_housing
# add later when we create it

__all__ = [
    "fetch_ahmedabad_housing",
    "fetch_gurugram_housing",
    "fetch_mumbai_housing"
]
