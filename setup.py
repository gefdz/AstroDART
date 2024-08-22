from setuptools import setup, find_packages


VERSION = '0.1'
DESCRIPTION = 'Astronomical image reduction.'
LONG_DESCRIPTION = 'A package to reduce astronomical images, intended for photometry and astrophotography uses.'

# Setting up
setup(
    name="AstroDART",
    version=VERSION,
    author="Gareb Enoc Fernández Rodríguez",
    author_email="gareb.fernandez@gmai.com",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=['astropy', 'ccdproc', 'astroquery','photutils','matplotlib','tqdm'],
    keywords=['python', 'reduction', 'photometry', 'astrophotography', 'astronomy'],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Education",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
    ]
)
