from setuptools import setup, find_packages

setup(
    name="optimizelab",
    version="0.1.2",   # bumped
    description="A collection of classical and nature-inspired optimization algorithms implemented in Python.",
    author="code spaze",
    packages=find_packages(),
    include_package_data=True,
    package_data={                  # include .xlsx files inside the package
        "optimizelab": ["*.xlsx"],
    },
    install_requires=[
        "numpy",
        "matplotlib",
        "networkx",
        "pandas",
        "openpyxl"
    ],
    python_requires=">=3.8",
)
