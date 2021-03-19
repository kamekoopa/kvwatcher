from setuptools import setup, find_packages

version = "0.0.1.a1"

requires = [
    "PyYAML==3.11",
    "python-etcd==0.3.2",
    "Jinja2==2.11.3",
]

with open("README.rst") as f:
    readme = f.read()

setup(
    name="kvwatcher",
    version=version,
    description="watching kvs and execute some command with trigger of modification",
    long_description=readme,
    author="kamekoopa",
    author_email="hogehugo@gmail.com",
    url="",
    packages=find_packages(),
    scripts=["kvwatcher"],
    license="",
    install_requires=requires,
)
