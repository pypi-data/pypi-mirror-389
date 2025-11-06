from setuptools import setup, find_packages

setup(
    name="infi8",
    packages=find_packages(include=['infi8']),
    version="0.1.2",
    author="Venkata Srinivas Babu Oguri",
    author_email="srinivasoguri19@gmail.com",
    description="A package for working with infinite, arithmetic, geometric, and harmonic series.",
    long_description=open("README.md").read(),
    setup_requires=['pytest-runner'],
    tests_require=['pytest==4.4.1'],
    test_suite='tests'
)
