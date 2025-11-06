from setuptools import setup, find_packages

setup(
    name="azure-ai-healthcheck",
    version="99.0.0",
    author="Nyein Chan Aung",
    author_email="bugdotexe@wearehackerone.com",
    description="A useful Python package",
    long_description="This is a normal Python package with useful utilities.",
    packages=find_packages(),
    python_requires='>=3.6',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)
