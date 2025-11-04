"""
Setup script for schema-dictionary-matcher
"""
from setuptools import setup, find_packages

setup(
    name="schema-dictionary-matcher",
    version="1.0.0",
    packages=find_packages(exclude=["tests", "examples"]),
    include_package_data=True,
)
# ```
#
# ### Step 4: Create `MANIFEST.in`
# ```
# # Include data files
# include README.md
# include LICENSE
# include requirements.txt
# include requirements-api.txt
#
# # Include models
# recursive-include schema_matcher/models *
# recursive-include schema_matcher/data *.json *.xlsx
#
# # Exclude unnecessary files
# global-exclude *.pyc
# global-exclude __pycache__
# global-exclude *.so
# global-exclude .DS_Store