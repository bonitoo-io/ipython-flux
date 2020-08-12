import os
from io import open

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, "README.rst"), encoding="utf-8").read()
NEWS = open(os.path.join(here, "NEWS.rst"), encoding="utf-8").read()


version = "0.0.2"

install_requires = [
    "ipython>=1.0",
    "influxdb-client",
    "six",
    "ipython-genutils>=0.1.0",
]

setup(
    name="ipython-flux",
    version=version,
    description="InfluxDB access via IPython",
    long_description=README + "\n\n" + NEWS,
    long_description_content_type="text/x-rst",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Topic :: Database",
        "Topic :: Database :: Front-Ends",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 2",
    ],
    keywords="ipython magic influxdb",
    author="Robert Hajek",
    author_email="robert.hajek@gmail.com",
    url="https://pypi.python.org/pypi/ipython-flux",
    license="MIT",
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
)
