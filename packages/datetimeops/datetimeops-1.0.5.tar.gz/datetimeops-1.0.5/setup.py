from setuptools import setup, find_packages

setup(
    name="datetimeops",
    version="1.0.5",
    description="A lightweight Python library for date and time operations.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Kanad Rishiraj (RoamingSaint)",
    author_email="roamingsaint27@gmail.com",
    url="https://github.com/roamingsaint/datetimeops",  # Update with your actual repo
    packages=find_packages(),
    install_requires=[
        "pytz",
        "python-dateutil",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
