from setuptools import setup, find_packages

setup(
    name="nardlpy",
    version="1.0.0",
    author="Dr. Taha Zaghdoudi",
    author_email="zedtaha@gmail.com",
    description="NARDL and Fourier NARDL estimation and diagnostic toolkit in Python.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    #url="https://github.com/YourUsername/nardlpy",  # Optional: update if you host it
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pandas",
        "scipy",
        "statsmodels",
        "matplotlib"
    ],
    python_requires=">=3.8",
    license="MIT",
)
