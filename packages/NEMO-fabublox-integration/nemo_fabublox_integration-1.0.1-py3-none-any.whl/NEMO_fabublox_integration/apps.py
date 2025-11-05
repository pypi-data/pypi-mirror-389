import logging

from django.apps import AppConfig
from django.conf import settings
from . import app_settings as defaults

logger = logging.getLogger(__name__)

for name in dir(defaults):
    if name.isupper() and not hasattr(settings, name):
        setattr(settings, name, getattr(defaults, name))


class FabubloxIntegrationConfig(AppConfig):
    name = "NEMO_fabublox_integration"
    verbose_name = "FabuBlox Integration"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        """
        This code will be run when Django starts.
        """
        from NEMO_fabublox_integration.customization import FabubloxCustomization
        from NEMO.plugins.utils import check_extra_dependencies

        check_extra_dependencies(self.name, ["NEMO", "NEMO-CE"])

        # Load the configuration model to ensure it exists
        try:
            from .models import FabubloxIntegrationConfiguration

            configuration = FabubloxIntegrationConfiguration.get_instance()
        except Exception:
            # The models may not be loaded yet (e.g., during migrations)
            return

        # check authentication key is set and is valid
        key_location = getattr(settings, "FABUBLOX_AUTHENTICATION_KEY_LOCATION", None)
        if not key_location:
            logger.warning("FABUBLOX_AUTHENTICATION_KEY_LOCATION is not set. Please set it in your settings.py file.")

        try:
            from .models import FabubloxAuthenticationKey

            if key_location:
                authentication_key = FabubloxAuthenticationKey(key_location)
                authentication_key.set_configuration_instance_id()
        except Exception as e:
            logger.error(e)

        # if the bucket name is not set, use the one from settings
        if configuration and not configuration.data_sync_bucket_name:
            if hasattr(settings, "FABUBLOX_DATA_SYNC_BUCKET_NAME"):
                configuration.data_sync_bucket_name = settings.FABUBLOX_DATA_SYNC_BUCKET_NAME
                configuration.save()
