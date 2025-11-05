from setuptools import setup, find_packages

setup(
    name="EssentiaX",  # ✅ Updated name
    version="0.1.0",
    author="Shubham Wagh",
    author_email="your_email@example.com",  # optional but nice to include
    description="A next-generation Python library for smart EDA, cleaning, and interpretability in ML.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://pypi.org/project/EssentiaX/",  # optional
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy",
        "matplotlib",
        "seaborn",
        "scikit-learn"
    ],
    python_requires=">=3.8",
)
 