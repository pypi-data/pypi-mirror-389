from setuptools import setup, find_packages

setup(
    name="caki",  # must be unique on PyPI
    version="0.8.0",
    packages=find_packages(),
    install_requires=[],
    entry_points={
        "console_scripts": [
            "caki=auto.cli:main",  # creates 'auto' CLI
        ],
    },
    python_requires='>=3.6',
    description="Auto-installer CLI wrapper for pip packages",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Mufaddal Jawadwala",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)