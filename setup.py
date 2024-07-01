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
        "fast-opex>=0.0.2",
        "orjson",
        "shapely",
        "scikit-learn",
        "matplotlib",
        "seppl>=0.2.6",
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
        "happy.gui.raw_checker": ["*.ui"],
    },
    packages=find_namespace_packages(where='src'),
    entry_points={
        "console_scripts": [
            "envi-viewer=happy.gui.envi_viewer.viewer:sys_main",  # deprecated
            "happy-envi-viewer=happy.gui.envi_viewer.viewer:sys_main",
            "happy-data-viewer=happy.gui.data_viewer.viewer:sys_main",
            "happy-raw-checker=happy.gui.raw_checker.checker:sys_main",
            "happy-generate-image-regions-objects=happy.console.image_regions_objects.generate:sys_main",
            "happy-generic-regression-build=happy.console.builders.generic_regression_build:sys_main",
            "happy-generic-unsupervised-build=happy.console.builders.generic_unsupervised_build:sys_main",
            "happy-hdr-info=happy.console.hdr_info.output:sys_main",
            "happy-help=happy.console.help.generate:sys_main",
            "happy-hsi2rgb=happy.console.hsi_to_rgb.generate:sys_main",
            "happy-mat-info=happy.console.mat_info.output:sys_main",
            "happy-opex2happy=happy.console.ann_to_happy.generate:sys_main",  # deprecated
            "happy-ann2happy=happy.console.ann_to_happy.generate:sys_main",
            "happy-opex-labels=happy.console.opex_labels.generate:sys_main",
            "happy-process-data=happy.console.process_data.process:sys_main",
            "happy-plot-preproc=happy.console.plot_preproc.output:sys_main",
            "happy-raw-check=happy.console.raw_check.process:sys_main",
            "happy-scikit-regression-build=happy.console.builders.regression_build:sys_main",
            "happy-scikit-segmentation-build=happy.console.builders.segmentation_build:sys_main",
            "happy-scikit-unsupervised-build=happy.console.builders.unsupervised_build:sys_main",
            "happy-splitter=happy.console.happy_splitter.split:sys_main",
        ],
        "class_lister": [
            "happy=happy.base.class_lister",
        ],
    },
    version="0.0.1",
    author='Dale Fletcher',
    author_email='dale@waikato.ac.nz',
)
