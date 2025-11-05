from setuptools import setup, find_packages

setup(
    name="animalsay",
    version="0.1.3",
    packages=find_packages(where="src"),  # <-- look in src/
    package_dir={"": "src"},               # <-- maps packages from src/
    install_requires=[
        "pytest",
    ],
)
