from django.apps import apps
from django.test import TestCase


class HydraTest(TestCase):

    def test_plugin_is_installed(self):
        assert apps.is_installed("NEMO_hydra")
