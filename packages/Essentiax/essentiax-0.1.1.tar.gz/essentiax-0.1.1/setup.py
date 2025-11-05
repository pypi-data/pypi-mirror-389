from setuptools import setup, find_packages

setup(
    name="EssentiaX",  # PyPI project name
    version="0.1.1",
    packages=find_packages(include=["EssentiaX", "EssentiaX.*"]),
    install_requires=[
        "pandas",
        "numpy",
        "matplotlib",
        "seaborn",
        "scikit-learn"
    ],
    author="Shubham Wagh",
    author_email="your_email@example.com",
    description="A next-generation Python library for smart EDA, cleaning, and interpretability in ML.",
    url="https://pypi.org/project/EssentiaX/",
)
