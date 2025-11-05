from django import forms

from NEMO_fabublox_integration.models import FabubloxIntegrationConfiguration


class FabubloxIntegrationSharedToolFieldsForm(forms.ModelForm):
    class Meta:
        model = FabubloxIntegrationConfiguration
        fields = ["shared_tool_fields"]
