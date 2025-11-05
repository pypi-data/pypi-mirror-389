from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.contenttypes.models import ContentType
from django.db.models import OuterRef, Subquery
from django.http import HttpResponseNotFound
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from NEMO.models import Tool
from NEMO.views.pagination import SortedPaginator

from NEMO_fabublox_integration.forms import FabubloxIntegrationSharedToolFieldsForm
from NEMO_fabublox_integration.models import (
    FabubloxIntegrationConfiguration,
    FabubloxSynchronizationJob,
    FabubloxDataSyncStatus,
)
from NEMO_fabublox_integration.serializers import get_tool_serializer
from NEMO_fabublox_integration.synchronize import synchronize_job


def can_access_fabublox_integration(user):
    return FabubloxIntegrationConfiguration.get_instance().has_access(user)


@login_required
@user_passes_test(can_access_fabublox_integration)
@require_GET
def configuration(request):
    configuration_obj = FabubloxIntegrationConfiguration.get_instance()
    key_health_pass, key_health_message = configuration_obj.key_health_check()

    return render(
        request,
        "NEMO_fabublox_integration/configuration.html",
        {
            "key_health_message": key_health_message,
            "key_health_pass": key_health_pass,
            "shared_tool_fields": configuration_obj.shared_tool_fields,
        },
    )


@login_required
@user_passes_test(can_access_fabublox_integration)
@require_POST
def update_shared_tool_fields(request):
    configuration_obj = FabubloxIntegrationConfiguration.get_instance()
    fields = request.POST.getlist("shared_tool_fields", [])
    shared_tool_fields_form = FabubloxIntegrationSharedToolFieldsForm(
        {"shared_tool_fields": fields}, instance=configuration_obj
    )
    if shared_tool_fields_form.is_valid():
        shared_tool_fields_form.save()
        messages.success(request, "Shared tool fields updated successfully.")
        return redirect("fabublox_configuration")

    configuration_obj.refresh_from_db()
    key_health_pass, key_health_message = configuration_obj.key_health_check()

    return render(
        request,
        "NEMO_fabublox_integration/configuration.html",
        {
            "key_health_message": key_health_message,
            "key_health_pass": key_health_pass,
            "shared_tool_fields": configuration_obj.shared_tool_fields,
        },
    )


@login_required
@user_passes_test(can_access_fabublox_integration)
@require_GET
def tools(request):
    configuration_obj = FabubloxIntegrationConfiguration.get_instance()
    try:
        configuration_obj.check_readiness()
        search = request.GET.get("search", None)
        if search:
            tools_queryset = Tool.objects.filter(name__icontains=search)
        else:
            tools_queryset = Tool.objects.all()
        number_of_tools = Tool.objects.count()
        tool_content_type = ContentType.objects.get_for_model(Tool)
        sync_status_qs = FabubloxDataSyncStatus.objects.filter(
            content_type=tool_content_type, object_id=OuterRef("pk")
        ).order_by("-last_synced")
        tools_queryset = tools_queryset.annotate(
            last_synced=Subquery(sync_status_qs.values("last_synced")[:1]),
            last_synced_by=Subquery(sync_status_qs.values("last_synced_by__username")[:1]),
        )
        page = SortedPaginator(tools_queryset, request, order_by="name").get_current_page()
        return render(
            request,
            "NEMO_fabublox_integration/tools.html",
            {"page": page, "search_term": search, "number_of_tools": number_of_tools, "ready": True},
        )
    except ValueError as e:
        return render(request, "NEMO_fabublox_integration/tools.html", {"ready": False, "configuration_readiness": e})


@login_required
@user_passes_test(can_access_fabublox_integration)
@require_GET
def synchronizations(request):
    # Clean up any stale jobs (from server restarts, thread crashes, etc)
    FabubloxSynchronizationJob.cleanup_stale_jobs()

    in_progress = FabubloxSynchronizationJob.get_in_progress_jobs()
    others = FabubloxSynchronizationJob.get_history()
    page = SortedPaginator(others, request, order_by="-created_at").get_current_page()
    return render(
        request,
        "NEMO_fabublox_integration/synchronization.html",
        {"page": page, "in_progress": in_progress, "has_in_progress": in_progress.exists()},
    )


@login_required
@user_passes_test(can_access_fabublox_integration)
@require_http_methods(["GET"])
def in_progress_synchronizations(request):
    # Clean up any stale jobs (from server restarts, thread crashes, etc)
    FabubloxSynchronizationJob.cleanup_stale_jobs()

    in_progress = FabubloxSynchronizationJob.get_in_progress_jobs()
    if not in_progress.exists():
        return HttpResponseNotFound("No synchronization in progress.")

    return render(
        request,
        "NEMO_fabublox_integration/in_progress_synchronization.html",
        {"in_progress": in_progress},
    )


@login_required
@user_passes_test(can_access_fabublox_integration)
@require_POST
def synchronize_tools(request):
    configuration_obj = FabubloxIntegrationConfiguration.get_instance()
    user = request.user

    try:
        configuration_obj.check_readiness()
    except Exception as e:
        messages.error(
            request,
            f"Your FabuBlox integration configuration is incomplete or invalid: {e}",
            "data-speed=40000 data-trigger=manual",
        )
        return redirect("fabublox_tools")

    # Clean up any stale jobs before checking for in-progress jobs
    FabubloxSynchronizationJob.cleanup_stale_jobs()
    tool_content_type = ContentType.objects.get_for_model(Tool)

    in_progress = FabubloxSynchronizationJob.get_in_progress_jobs().filter(content_type=tool_content_type)

    # Only allow one synchronization job at a time
    if in_progress.exists():
        messages.error(
            request,
            "A synchronization job is already in progress. Please wait for it to complete.",
            "data-speed=40000 data-trigger=manual",
        )
        return redirect("fabublox_tools")

    sync_all = request.POST.get("sync_all", "false").lower() == "true"

    try:
        if sync_all:
            tool_ids = list(Tool.objects.values_list("id", flat=True))
        else:
            tool_id_strings = request.POST.getlist("tool_id")
            tool_ids = []
            for tool_id_str in tool_id_strings:
                try:
                    tool_ids.append(int(tool_id_str))
                except (ValueError, TypeError):
                    messages.error(request, f"Invalid tool ID: {tool_id_str}", "data-speed=40000 data-trigger=manual")
                    return redirect("fabublox_tools")

        if not tool_ids:
            messages.error(request, "No tools selected for synchronization.", "data-speed=40000 data-trigger=manual")
            return redirect("fabublox_tools")

        synchronize_job(get_tool_serializer(), tool_content_type, tool_ids, user)
        messages.success(request, f"Synchronization job started successfully for {len(tool_ids)} tool(s).")
        return redirect("fabublox_synchronization")

    except ValueError as e:
        messages.error(request, f"Failed to start synchronization job: {e}", "data-speed=40000 data-trigger=manual")
        return redirect("fabublox_tools")
    except Exception as e:
        messages.error(
            request, f"Unexpected error starting synchronization job: {e}", "data-speed=40000 data-trigger=manual"
        )
        return redirect("fabublox_tools")
