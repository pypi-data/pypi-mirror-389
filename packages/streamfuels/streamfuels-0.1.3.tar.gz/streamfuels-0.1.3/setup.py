from setuptools import setup, find_packages

setup(
    name="streamfuels",
    version="0.1.3",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.2.0",
        "requests>=2.25.0",
        "beautifulsoup4>=4.9.0",
        "unidecode>=1.1.1",
        "numpy>=1.19.0",
        "editdistance>=0.5.3",
        "setuptools",
        "tqdm==4.65.0",
    ],
    author="StreamFuels",
    author_email="lucascstxv@gmail.com",
    description="Data processing and analysis tools for fuel market research",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/streamfuels/streamfuels",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    license="MIT",
    license_files="LICENSE",
)
