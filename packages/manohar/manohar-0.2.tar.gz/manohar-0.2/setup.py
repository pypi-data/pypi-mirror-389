from setuptools import setup, find_packages

setup(
    name="manohar",
    version="0.2",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "manohar = manohar.main:run"
        ]
    },
)
