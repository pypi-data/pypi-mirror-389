from setuptools import setup, find_packages

setup(
    name="rodmena",
    version="0.0.1",
    author="Farshid Ashouri",
    author_email="farsheed.ashouri@gmail.com",
    description="A basic 'Hello World' package.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/rodmena-limited/rodmena",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
