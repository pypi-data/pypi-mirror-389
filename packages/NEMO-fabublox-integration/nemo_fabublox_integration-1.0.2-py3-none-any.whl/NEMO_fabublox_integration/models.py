from datetime import timedelta

from NEMO.fields import MultiRoleGroupPermissionChoiceField
from NEMO.models import User
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import ForeignKey
from django.utils.timezone import now
import json
from pathlib import Path


# Global variable to track last cleanup time
# Note: In multi-process environments (e.g., gunicorn with multiple workers),
# each worker will maintain its own timestamp. This is acceptable for this use case.
_last_cleanup_time = None
INVALID_AUTHENTICATION_KEY = "FabuBlox Authentication key is not valid."
NOTFOUND_AUTHENTICATION_KEY = "FabuBlox Authentication key is not configured."


class FabubloxAuthenticationKey:
    def __init__(self, path):
        self.file_path = path
        path = Path(path)
        if not path.exists() or not path.is_file():
            raise ValueError(NOTFOUND_AUTHENTICATION_KEY)

        with path.open("r", encoding="utf-8") as file:
            file_content = file.read()
            if file_content:
                try:
                    data = json.loads(file_content)
                    content = self.read_file_metadata(data)
                    self.key = data
                    self.client_email = content["client_email"]
                    self.key_instance_id = content["key_instance_id"]

                    configuration = FabubloxIntegrationConfiguration.get_instance()
                    if configuration.instance_id and self.key_instance_id != configuration.instance_id:
                        raise ValueError(INVALID_AUTHENTICATION_KEY)

                except json.JSONDecodeError:
                    raise ValueError(INVALID_AUTHENTICATION_KEY)
            else:
                raise ValueError(NOTFOUND_AUTHENTICATION_KEY)

    @classmethod
    def read_file_metadata(cls, data):
        if (
            "type" not in data
            or "universe_domain" not in data
            or data["type"] != "service_account"
            or data["universe_domain"] != "googleapis.com"
        ):
            raise ValueError(INVALID_AUTHENTICATION_KEY)

        if (
            not data.get("client_email")
            or not data["client_email"].startswith(settings.FABUBLOX_SA_EMAIL_PREFIX)
            or "@" not in data["client_email"]
        ):
            raise ValueError(INVALID_AUTHENTICATION_KEY)

        return {
            "client_email": data["client_email"],
            "key_instance_id": data["client_email"].split("@")[0].replace(settings.FABUBLOX_SA_EMAIL_PREFIX, ""),
        }

    def set_configuration_instance_id(self):
        configuration = FabubloxIntegrationConfiguration.get_instance()
        if not configuration.instance_id and self.key_instance_id:
            # set the instance_id if not already set
            configuration.instance_id = self.key_instance_id
            configuration.save()


class SingletonModel(models.Model):
    """
    Abstract base class for singleton models.
    """

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def get_instance(cls):
        instance, _ = cls.objects.get_or_create(pk=1)
        return instance


class ToolField(models.TextChoices):
    NAME = "name", "Name"
    DESCRIPTION = "description", "Description"
    CATEGORY = "category", "Category"
    LOCATION = "location", "Location"
    PRIMARY_OWNER = "primary_owner", "Primary Owner"
    PRIMARY_OWNER_FIRST_NAME = "primary_owner_first_name", "Primary Owner First Name"
    PRIMARY_OWNER_LAST_NAME = "primary_owner_last_name", "Primary Owner Last Name"
    PRIMARY_OWNER_EMAIL = "primary_owner_email", "Primary Owner Email"
    BACKUP_OWNERS = "backup_owners", "Backup Owners"
    BACKUP_OWNERS_FIRST_NAME = "backup_owners_first_name", "Backup Owners First Name"
    BACKUP_OWNERS_LAST_NAME = "backup_owners_last_name", "Backup Owners Last Name"
    BACKUP_OWNERS_EMAIL = "backup_owners_email", "Backup Owners Email"

    @classmethod
    def get_all_fields(cls):
        return list(cls.values)


class FabubloxIntegrationConfiguration(SingletonModel):
    instance_id = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        null=True,
        help_text="Unique identifier for this NEMO instance in Fabublox (Do not change this unless instructed by Fabublox support).",
    )
    data_sync_bucket_name = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        null=True,
        help_text="Name of the bucket used for data synchronization with Fabublox (Do not change this unless instructed by Fabublox support).",
    )
    admin_permission = MultiRoleGroupPermissionChoiceField(
        null=False,
        blank=False,
        groups=True,
        default="is_superuser",
        help_text="The roles/groups required for users to access the Fabublox integration features.",
    )
    shared_tool_fields = models.JSONField(
        default=ToolField.get_all_fields,
        blank=True,
        null=True,
        help_text="List of fields to be shared with Fabublox for tool synchronization.",
    )

    def __str__(self):
        return f"Fabublox Integration Configuration"

    @classmethod
    def get_fabublox_authentication_key(cls):
        key_location = getattr(settings, "FABUBLOX_AUTHENTICATION_KEY_LOCATION", None)
        if key_location:
            return FabubloxAuthenticationKey(key_location)
        return None

    def key_health_check(self):
        try:
            authentication_key = self.get_fabublox_authentication_key()
            if not authentication_key:
                return False, NOTFOUND_AUTHENTICATION_KEY
            return True, "Authentication key is valid."
        except ValueError as e:
            return False, e

    def check_readiness(self):
        key_health_pass, message = self.key_health_check()
        if not key_health_pass:
            raise ValueError(message)

        if not self.instance_id or not self.instance_id.strip():
            raise ValueError("Instance ID is not set or is invalid.")

        if not self.data_sync_bucket_name or not self.data_sync_bucket_name.strip():
            raise ValueError("Data synchronization bucket name is not set or is invalid.")

    @classmethod
    def get_admin_permission_field(cls) -> MultiRoleGroupPermissionChoiceField:
        return cls._meta.get_field("admin_permission")

    def has_access(self, user):
        return self.get_admin_permission_field().has_user_roles(self.admin_permission, user)

    def clean(self):
        errors = {}

        if self.shared_tool_fields:
            if not isinstance(self.shared_tool_fields, list):
                errors["share_tool_fields"] = "Shared tool fields must be a list."
            else:
                fields = self.shared_tool_fields or []
                for field in fields:
                    if field not in ToolField.values:
                        errors["share_tool_fields"] = f"Invalid shared tool field: {field}"

                primary_owner_fields = {
                    ToolField.PRIMARY_OWNER_FIRST_NAME,
                    ToolField.PRIMARY_OWNER_LAST_NAME,
                    ToolField.PRIMARY_OWNER_EMAIL,
                }
                backup_owners_fields = {
                    ToolField.BACKUP_OWNERS_FIRST_NAME,
                    ToolField.BACKUP_OWNERS_LAST_NAME,
                    ToolField.BACKUP_OWNERS_EMAIL,
                }
                intersect_primary_owner = primary_owner_fields & set(fields)
                if intersect_primary_owner and ToolField.PRIMARY_OWNER not in fields:
                    fields.append(ToolField.PRIMARY_OWNER)
                elif not intersect_primary_owner and ToolField.PRIMARY_OWNER in fields:
                    fields.remove(ToolField.PRIMARY_OWNER)
                intersect_backup_owners = backup_owners_fields & set(fields)
                if intersect_backup_owners and ToolField.BACKUP_OWNERS not in fields:
                    fields.append(ToolField.BACKUP_OWNERS)
                elif not intersect_backup_owners and ToolField.BACKUP_OWNERS in fields:
                    fields.remove(ToolField.BACKUP_OWNERS)

                self.shared_tool_fields = fields

        if len(errors) > 0:
            raise ValidationError(errors)


class FabubloxDataSyncStatus(models.Model):
    class Meta:
        unique_together = ("content_type", "object_id")
        indexes = [
            models.Index(fields=["content_type", "object_id", "-last_synced"]),
            models.Index(fields=["-last_synced"]),
        ]

    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, help_text="Content type of the model being synced"
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    last_synced = models.DateTimeField(auto_now=True, help_text="Timestamp of the last sync attempt with FabuBlox")
    last_synced_by = ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fabublox_sync_status",
        help_text="User who last synced this entity",
    )


class JobStatus(object):
    PENDING = 0
    IN_PROGRESS = 1
    COMPLETED = 2
    PARTIALLY_COMPLETED = 3
    FAILED = 4
    Choices = (
        (PENDING, "Pending"),
        (IN_PROGRESS, "In Progress"),
        (COMPLETED, "Completed"),
        (PARTIALLY_COMPLETED, "Partially Completed"),
        (FAILED, "Failed"),
    )


class FabubloxSyncFailure(models.Model):
    job = models.ForeignKey(
        "FabubloxSynchronizationJob", on_delete=models.CASCADE, related_name="failures", help_text="Synchronization job"
    )
    item_id = models.PositiveIntegerField(help_text="ID of the item that failed to sync")
    item_name = models.CharField(max_length=255, help_text="Name of the item that failed")
    error_message = models.TextField(help_text="Error message from the failed sync attempt")
    failed_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the sync failed")

    class Meta:
        indexes = [
            models.Index(fields=["job", "-failed_at"]),
        ]


class FabubloxSynchronizationJob(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["-created_at"]),
        ]

    status = models.IntegerField(
        choices=JobStatus.Choices, default=JobStatus.PENDING, help_text="Current status of the synchronization job"
    )
    total_items = models.PositiveIntegerField(default=0, help_text="Total number of items to be synchronized")
    succeeded_items = models.PositiveIntegerField(default=0, help_text="Number of items successfully synchronized")
    failed_items = models.PositiveIntegerField(default=0, help_text="Number of items that failed to synchronize")
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, help_text="Content type of the model being synced"
    )
    started_by = ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fabublox_sync_jobs",
        help_text="User who started this synchronization job",
    )
    item_ids = models.JSONField(help_text="List of item IDs being synchronized")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the job was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the job was last updated")

    @property
    def processed_items(self):
        return self.succeeded_items + self.failed_items

    @property
    def progress_percent(self):
        if self.total_items == 0:
            return 0
        return round((self.processed_items / self.total_items) * 100)

    @property
    def failed_items_details(self):
        return [{"item": failure.item_name, "error": failure.error_message} for failure in self.failures.all()]

    @property
    def is_stale(self):
        """Check if job appears to be abandoned (thread died/server restarted)."""
        from datetime import timedelta

        if self.status not in [JobStatus.IN_PROGRESS, JobStatus.PENDING]:
            return False
        timeout_minutes = getattr(settings, "FABUBLOX_JOB_TIMEOUT_MINUTES", 5)
        return self.updated_at < now() - timedelta(minutes=timeout_minutes)

    def handle_interrupted(self):
        """Update job status if it was likely interrupted (thread died, server restart, etc)."""
        with transaction.atomic():
            job = type(self).objects.select_for_update().get(pk=self.pk)

            if job.succeeded_items == job.total_items:
                job.status = JobStatus.COMPLETED
            elif job.failed_items == job.total_items:
                job.status = JobStatus.FAILED
            elif job.succeeded_items + job.failed_items == job.total_items:
                job.status = JobStatus.PARTIALLY_COMPLETED
            else:
                # likely interrupted, mark as failed
                job.status = JobStatus.FAILED

            job.save(update_fields=["status"])

    @classmethod
    def create_job(cls, content_type, item_ids, started_by):
        return cls.objects.create(
            content_type=content_type,
            started_by=started_by,
            item_ids=list(item_ids),
            total_items=len(item_ids),
            status=JobStatus.PENDING,
        )

    @classmethod
    def get_in_progress_jobs(cls):
        return cls.objects.filter(status__in=[JobStatus.IN_PROGRESS, JobStatus.PENDING]).order_by("-created_at")

    @classmethod
    def get_history(cls):
        return cls.objects.filter(
            status__in=[JobStatus.COMPLETED, JobStatus.PARTIALLY_COMPLETED, JobStatus.FAILED]
        ).order_by("-created_at")

    @classmethod
    def cleanup_stale_jobs(cls):
        """
        Find and mark stale jobs as failed.

        This method is throttled to run at most once per configured interval
        to avoid overwhelming the database during frequent polling.
        """
        global _last_cleanup_time

        cleanup_interval_minutes = getattr(settings, "FABUBLOX_JOB_CLEANUP_INTERVAL_MINUTES", 2)
        cleanup_interval = timedelta(minutes=cleanup_interval_minutes)

        current_time = now()

        if _last_cleanup_time is None or (current_time - _last_cleanup_time) >= cleanup_interval:
            _last_cleanup_time = current_time

            in_progress_jobs = cls.get_in_progress_jobs()
            cleaned = 0
            for job in in_progress_jobs:
                if job.is_stale:
                    job.handle_interrupted()
                    cleaned += 1
            return cleaned

        return 0
