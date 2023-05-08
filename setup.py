from setuptools import setup, find_namespace_packages


def _read(f):
    """
    Reads in the content of the file.
    :param f: the file to read
    :type f: str
    :return: the content
    :rtype: str
    """
    return open(f, 'rb').read()


setup(
    name="happy-hsi-to-csv",
    description="Library for the Happy project that turns hyper-spectral data into CSV.",
    long_description=(
        _read('DESCRIPTION.rst') + b'\n' +
        _read('CHANGES.rst')).decode('utf-8'),
    url="https://github.com/wairas/happy-hsi-to-csv",
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Topic :: Scientific/Engineering',
        'Programming Language :: Python :: 3',
    ],
    license='MIT License',
    install_requires=[
        "numpy==1.21.6",
        "pandas==1.3.5",
        "scipy==1.7.3",
    ],
    package_dir={
        '': 'src'
    },
    packages=find_namespace_packages(where='src'),
    entry_points={
        "console_scripts": [
            "h2c-generate-csv=happy_hsi2csv.generate_csv:sys_main",
        ]
    },
    version="0.0.1",
    author='Dale Fletcher',
    author_email='dale@waikato.ac.nz',
)
