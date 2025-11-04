from django.apps import AppConfig


class HydraConfig(AppConfig):
    name = "NEMO_hydra"
    verbose_name = "hydra"

    def ready(self):
        """
        This code will be run when Django starts.
        """
        from NEMO_hydra import customizations  # needed

        pass
