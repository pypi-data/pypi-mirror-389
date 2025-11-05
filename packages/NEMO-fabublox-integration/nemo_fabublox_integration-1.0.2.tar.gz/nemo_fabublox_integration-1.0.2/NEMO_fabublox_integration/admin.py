from django.contrib import admin

from NEMO_fabublox_integration.models import FabubloxIntegrationConfiguration


@admin.register(FabubloxIntegrationConfiguration)
class FabubloxIntegrationConfigurationAdmin(admin.ModelAdmin):
    list_display = ("instance_id", "data_sync_bucket_name")
    search_fields = ("instance_id", "data_sync_bucket_name")
    exclude = ("shared_tool_fields",)
    readonly_fields = ("data_sync_bucket_name",)

    def has_add_permission(self, request):
        return FabubloxIntegrationConfiguration.objects.count() == 0

    def has_delete_permission(self, request, obj=None):
        return False
