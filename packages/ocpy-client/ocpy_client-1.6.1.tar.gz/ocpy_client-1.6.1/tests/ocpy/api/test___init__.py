import os
import unittest
import logging

from ocpy import setup_connection_config_from_yaml_file


class TestApiModuleClass(unittest.TestCase):
    def test_setup_connection_config_from_yaml_file(self):
        config = setup_connection_config_from_yaml_file(
            # os.path.abspath("tests/assets/example_connection_conf.yml")
            os.path.abspath("tests/.test.creds.yml")
        )
        logging.debug(config)
        self.assertIsNotNone(config)
        self.assertIsInstance(config, dict)
        self.assertIn("server_url", config)
