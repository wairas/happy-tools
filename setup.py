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
    description="Tools for dealing with hyperspectral images.",
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
        "opex>=0.0.3",
        "shapely",
        "scikit-learn",
        "matplotlib",
        "seppl>=0.0.11",
        "wai.logging",
        "tabulate",
    ],
    package_dir={
        '': 'src'
    },
    package_data={
        "happy": ["*.png"],
        "happy.gui.envi_viewer": ["*.ui"],
        "happy.gui.data_viewer": ["*.ui"],
    },
    packages=find_namespace_packages(where='src'),
    entry_points={
        "console_scripts": [
            "envi-viewer=happy.gui.envi_viewer.viewer:sys_main",  # deprecated
            "happy-envi-viewer=happy.gui.envi_viewer.viewer:sys_main",
            "happy-data-viewer=happy.gui.data_viewer.viewer:sys_main",
            "happy-generate-image-regions-objects=happy.console.image_regions_objects.generate:sys_main",
            "happy-generic-regression-build=happy.console.builders.generic_regression_build:sys_main",
            "happy-generic-unsupervised-build=happy.console.builders.generic_unsupervised_build:sys_main",
            "happy-hdr-info=happy.console.hdr_info.output:sys_main",
            "happy-help=happy.console.help.generate:sys_main",
            "happy-hsi2rgb=happy.console.hsi_to_rgb.generate:sys_main",
            "happy-mat-info=happy.console.mat_info.output:sys_main",
            "happy-opex2happy=happy.console.opex_to_happy.generate:sys_main",
            "happy-opex-labels=happy.console.opex_labels.generate:sys_main",
            "happy-process-data=happy.console.process_data.process:sys_main",
            "happy-plot-preproc=happy.console.plot_preproc.output:sys_main",
            "happy-raw-check=happy.console.raw_check.process:sys_main",
            "happy-scikit-regression-build=happy.console.builders.regression_build:sys_main",
            "happy-scikit-segmentation-build=happy.console.builders.segmentation_build:sys_main",
            "happy-scikit-unsupervised-build=happy.console.builders.unsupervised_build:sys_main",
            "happy-splitter=happy.console.happy_splitter.split:sys_main",
        ],
        "happy.blackref_methods": [
            "happy_blackref_methods=happy.data:happy.data.black_ref.AbstractBlackReferenceMethod",
        ],
        "happy.whiteref_methods": [
            "happy_whiteref_methods=happy.data:happy.data.white_ref.AbstractWhiteReferenceMethod",
        ],
        "happy.ref_locator": [
            "happy_ref_locator=happy.data:happy.data.ref_locator.AbstractReferenceLocator",
        ],
        "happy.preprocessors": [
            "happy_preprocessors=happy.preprocessors:happy.preprocessors.Preprocessor",
        ],
        "happy.happydata_readers": [
            "happy_happydata_readers=happy.readers:happy.readers.HappyDataReader",
        ],
        "happy.happydata_writers": [
            "happy_happydata_writers=happy.writers:happy.writers.HappyDataWriter",
        ],
        "happy.pixel_selectors": [
            "happy_pixel_selectors=happy.pixel_selectors:happy.pixel_selectors.PixelSelector",
        ],
        "happy.region_extractors": [
            "happy_region_extractors=happy.region_extractors:happy.region_extractors.RegionExtractor",
        ],
    },
    version="0.0.1",
    author='Dale Fletcher',
    author_email='dale@waikato.ac.nz',
)
