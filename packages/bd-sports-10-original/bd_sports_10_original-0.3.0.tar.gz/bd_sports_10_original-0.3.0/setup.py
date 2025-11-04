from setuptools import setup, find_packages
import os

# Read the README.md for long_description
with open(os.path.join(os.path.dirname(__file__), "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="bd_sports_10_original",
    version="0.3.0",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,  # Recommended when including non-Python files
    install_requires=[
        "requests",
        "tqdm"
    ],
    description="Original version of BD Sports 10 dataset with downloader and progress bar",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Wazih Ullah Tanzim <wazihullahtanzim@gmail.com>, Khondaker A. Mamun <mamun@cse.uiu.ac.bd>",
    license="CC BY 4.0",
    url="https://doi.org/10.57760/sciencedb.24216",
    python_requires=">=3.11",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Topic :: Utilities",
        "Intended Audience :: Science/Research"
    ],
)
