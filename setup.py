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
    name="happy-tools",
    description="Tools for dealing with hyper-spectral images.",
    long_description=(
        _read('DESCRIPTION.rst') + b'\n' +
        _read('CHANGES.rst')).decode('utf-8'),
    url="https://github.com/wairas/happy-tools",
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Topic :: Scientific/Engineering',
        'Programming Language :: Python :: 3',
    ],
    license='MIT License',
    install_requires=[
        "numpy<1.22",
        "pandas<1.4",
        "scipy",
        "spectral==0.23.1",
        "pillow<10.0",
        "pygubu==0.31",
        "redis",
        "ttkSimpleDialog==1.2.1",
        "opex",
        "shapely",
        "scikit-learn",
        "matplotlib",
    ],
    package_dir={
        '': 'src'
    },
    package_data={
        "happy": ["*.png"],
        "happy.envi_viewer": ["*.ui"],
    },
    packages=find_namespace_packages(where='src'),
    entry_points={
        "console_scripts": [
            "envi-viewer=happy.envi_viewer.viewer:sys_main",  # deprecated
            "happy-envi-viewer=happy.envi_viewer.viewer:sys_main",
            "happy-generate-image-regions-objects=happy.generate_image_regions_objects:sys_main",
            "happy-hdr-info=happy.hdr_info:sys_main",
            "happy-hsi2csv=happy.hsi_to_csv.generate:sys_main",
            "happy-hsi2rgb=happy.hsi_to_rgb.generate:sys_main",
            "happy-mat-info=happy.mat_info:sys_main",
            "happy-opex2happy=happy.opex_to_happy.generate:sys_main",
            "happy-plot-preproc=happy.plot_preproc:sys_main",
            "happy-scikit-regression-build=happy.scikit_regression_build:sys_main",
            "happy-scikit-unsupervised-build=happy.scikit_unsupervised_build:sys_main",
        ]
    },
    version="0.0.1",
    author='Dale Fletcher',
    author_email='dale@waikato.ac.nz',
)
