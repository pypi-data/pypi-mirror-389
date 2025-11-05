from logging import getLogger

from NEMO.decorators import postpone
from django.db import transaction
from django.db.models import F
from django.utils.timezone import now
from google.auth.exceptions import RefreshError
from google.cloud.exceptions import NotFound
from NEMO.utilities import get_model_instance

from NEMO_fabublox_integration.gcs import get_gcs_bucket, upload_json_to_gcs
from NEMO_fabublox_integration.models import (
    FabubloxSynchronizationJob,
    FabubloxSyncFailure,
    FabubloxDataSyncStatus,
    JobStatus,
    FabubloxIntegrationConfiguration,
)

synchronize_logger = getLogger(__name__)


def check_permissions(bucket):
    if not bucket:
        raise ValueError("FabuBlox access point is misconfigured.")
    try:
        # This will not check if we have access to the bucket, but it will check if the bucket exists and is accessible.
        bucket.test_iam_permissions(["storage.objects.create"])
    except NotFound:
        raise ValueError("FabuBlox access point not found or misconfigured")
    except RefreshError:
        raise ValueError("Your authentication key does not grant you permission to send data to FabuBlox.")


def synchronize_job(serializer, content_type, ids, user):
    configuration = FabubloxIntegrationConfiguration.get_instance()
    with transaction.atomic():
        if FabubloxSynchronizationJob.get_in_progress_jobs().filter(content_type=content_type).exists():
            raise ValueError("A synchronization job is already in progress. Please wait for it to complete.")
        bucket = get_gcs_bucket(
            configuration.get_fabublox_authentication_key().key, configuration.data_sync_bucket_name
        )
        check_permissions(bucket)
        job = FabubloxSynchronizationJob.create_job(content_type, ids, user)
        job.status = JobStatus.IN_PROGRESS
        job.save()
        start(bucket, serializer, content_type, ids, job.id, job.started_by, configuration.shared_tool_fields)


@postpone
def start(bucket, serializer, content_type, ids, job_id, started_by, fields=None):
    try:
        for item_id in ids:
            # Check if job is still IN_PROGRESS BEFORE doing any work
            is_in_progress = FabubloxSynchronizationJob.objects.filter(id=job_id, status=JobStatus.IN_PROGRESS).exists()
            if not is_in_progress:
                synchronize_logger.info(
                    f"Job {job_id} is no longer in progress (likely marked as interrupted), stopping synchronization thread"
                )
                return

            item_name = "Unknown"
            try:
                item = get_model_instance(content_type, item_id)
                item_name = str(item)
                data = serializer.serialize(item, fields)
                destination_blob_name = serializer.get_object_path(item)

                upload_json_to_gcs(data, destination_blob_name, bucket)

                try:
                    # Update counter
                    FabubloxSynchronizationJob.objects.filter(id=job_id).update(
                        succeeded_items=F("succeeded_items") + 1, updated_at=now()
                    )

                    # Update data sync status
                    FabubloxDataSyncStatus.objects.update_or_create(
                        content_type_id=content_type.id,
                        object_id=item_id,
                        defaults={"last_synced": now(), "last_synced_by": started_by},
                    )
                except Exception as e:
                    synchronize_logger.error(
                        f"Error updating synchronization status for item {item_id} ({item_name}) for job {job_id}: {e}"
                    )

            except Exception as e:
                # Record failure
                FabubloxSyncFailure.objects.create(
                    job_id=job_id, item_id=item_id, item_name=item_name, error_message=str(e)[:1000]
                )

                # Update counter
                FabubloxSynchronizationJob.objects.filter(id=job_id).update(
                    failed_items=F("failed_items") + 1, updated_at=now()
                )

        job = FabubloxSynchronizationJob.objects.get(id=job_id)

        # Check if job was already marked as completed/failed by cleanup
        if job.status != JobStatus.IN_PROGRESS:
            return

        if job.succeeded_items == job.total_items:
            status = JobStatus.COMPLETED
        elif job.failed_items == job.total_items:
            status = JobStatus.FAILED
        else:
            status = JobStatus.PARTIALLY_COMPLETED

        job.status = status
        job.save()

    except Exception as e:
        synchronize_logger.error(f"Unexpected error in synchronization job {job_id}: {e}", exc_info=True)
        FabubloxSynchronizationJob.objects.filter(id=job_id).update(status=JobStatus.FAILED, updated_at=now())
