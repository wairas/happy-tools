from wai.logging import init_logging
from happy.data import configure_envi_settings
from happy.base.core import ENV_HAPPY_LOGLEVEL


def init_app():
    """
    Initializes an application.
    """
    configure_envi_settings()
    init_logging(env_var=ENV_HAPPY_LOGLEVEL)
