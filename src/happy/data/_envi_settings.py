import spectral


def configure_envi_settings():
    """
    Adjusts some ENVI settings.
    """
    spectral.settings.envi_support_nonlowercase_params = False
