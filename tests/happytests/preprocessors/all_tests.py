import unittest

import happytests.preprocessors.test_crop
import happytests.preprocessors.test_derivative
import happytests.preprocessors.test_downsample
import happytests.preprocessors.test_pad
import happytests.preprocessors.test_passthrough
import happytests.preprocessors.test_pca
import happytests.preprocessors.test_sni
import happytests.preprocessors.test_snv
import happytests.preprocessors.test_std_scaler
import happytests.preprocessors.test_wavelength_subset


def suite():
    """
    Returns the test suite.
    :return: the test suite
    :rtype: unittest.TestSuite
    """
    result = unittest.TestSuite()
    result.addTests(happytests.preprocessors.test_crop.suite())
    result.addTests(happytests.preprocessors.test_derivative.suite())
    result.addTests(happytests.preprocessors.test_downsample.suite())
    result.addTests(happytests.preprocessors.test_pad.suite())
    result.addTests(happytests.preprocessors.test_passthrough.suite())
    result.addTests(happytests.preprocessors.test_pca.suite())
    result.addTests(happytests.preprocessors.test_sni.suite())
    result.addTests(happytests.preprocessors.test_snv.suite())
    result.addTests(happytests.preprocessors.test_std_scaler.suite())
    result.addTests(happytests.preprocessors.test_wavelength_subset.suite())
    return result


if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
