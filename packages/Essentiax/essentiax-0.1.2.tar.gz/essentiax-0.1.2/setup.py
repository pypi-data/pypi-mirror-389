from setuptools import setup, find_packages

setup(
    name="EssentiaX",
    version="0.1.2",
    author="Shubham Wagh",
    author_email="your_email@example.com",
    description="A next-generation Python library for smart EDA, cleaning, visualization, and ML interpretability.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://pypi.org/project/EssentiaX/",
    packages=find_packages(include=["essentiax", "essentiax.*"]),
    install_requires=[
        "pandas",
        "numpy",
        "matplotlib",
        "seaborn",
        "scikit-learn",
    ],
    python_requires=">=3.7",
)
