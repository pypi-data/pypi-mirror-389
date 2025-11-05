from NEMO.decorators import customization
from NEMO.views.customization import CustomizationBase


@customization(key="fabublox_integration", title="FabuBlox Integration")
class FabubloxCustomization(CustomizationBase):
    variables = {}
    files = []
