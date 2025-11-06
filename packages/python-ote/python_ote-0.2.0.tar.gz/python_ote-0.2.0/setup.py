import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

install_requires = ["scrapy<=2.13.0", "python-dateutil"]

setuptools.setup(
    name="python-ote",
    version="0.2.0",
    author="Dan Keder",
    author_email="dan.keder@protonmail.com",
    description="Python library for scraping daily electricity prices from OTE (ote-cr.cz)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dankeder/python-ote",
    packages=setuptools.find_packages(),
    install_requires=install_requires,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
