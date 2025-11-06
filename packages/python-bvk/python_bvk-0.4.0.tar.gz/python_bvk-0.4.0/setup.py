import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

install_requires = ["scrapy<=2.13.0", "python-dateutil"]

setuptools.setup(
    name="python-bvk",
    version="0.4.0",
    author="Dan Keder",
    author_email="dan.keder@protonmail.com",
    description="Python library for tracking water consumption from BVK (Brnenske vodarny a kanalizace, bvk.cz)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dankeder/python-bvk",
    packages=setuptools.find_packages(),
    install_requires=install_requires,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
