from setuptools import setup, find_packages

setup(
    name="cwmeda",
    version="0.0.2",
    author="Milind Chaudhari",
    author_email="codewithmilind@example.com",
    description="User-friendly customizable EDA plotting tools for data scientists.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "matplotlib",
        "seaborn"
    ],
    python_requires=">=3.7",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
