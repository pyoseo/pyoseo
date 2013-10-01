import os
import logging
import logging.config

module_dir = os.path.dirname(os.path.realpath(__file__))
settings_file = os.path.join(module_dir, 'settings.cfg')
logging.config.fileConfig(settings_file)
logger = logging.getLogger(__name__)
