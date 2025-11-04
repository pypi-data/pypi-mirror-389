from setuptools import setup, find_packages

setup(
    name="hiba_simple_linear_regression",  
    version="0.1",
    packages=find_packages(),
    install_requires=[], 
    author="Zoubir hiba",
    author_email="h.zouir@esi-sba.dz",
    description="Un package Python pour la régression linéaire simple",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/hibyy/Simple_Linear_Regression",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License"
    ],
    python_requires=">=3.6",
)
