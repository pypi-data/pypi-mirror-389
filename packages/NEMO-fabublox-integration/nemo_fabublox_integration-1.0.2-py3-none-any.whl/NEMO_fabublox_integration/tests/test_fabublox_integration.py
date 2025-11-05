from django.apps import apps
from django.test import TestCase


class FabubloxIntegrationTest(TestCase):

    def test_plugin_is_installed(self):
        assert apps.is_installed("NEMO_fabublox_integration")
