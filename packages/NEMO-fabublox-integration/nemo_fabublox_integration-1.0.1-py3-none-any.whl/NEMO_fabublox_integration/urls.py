from NEMO_fabublox_integration.views import fabublox_integration
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path(
        "fabublox/",
        include(
            [
                path("", RedirectView.as_view(url="/fabublox/tools", permanent=False), name="fabublox_index"),
                path("configuration/", fabublox_integration.configuration, name="fabublox_configuration"),
                path(
                    "shared_tool_fields/",
                    fabublox_integration.update_shared_tool_fields,
                    name="fabublox_shared_tool_fields",
                ),
                path("tools/", fabublox_integration.tools, name="fabublox_tools"),
                path("synchronization/", fabublox_integration.synchronizations, name="fabublox_synchronization"),
                path(
                    "synchronize/tools/",
                    fabublox_integration.synchronize_tools,
                    name="fabublox_synchronize_tools",
                ),
                path(
                    "synchronize/jobs-in-progress/",
                    fabublox_integration.in_progress_synchronizations,
                    name="fabublox_in_progress_synchronization",
                ),
            ]
        ),
    )
]
