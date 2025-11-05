import abc
from abc import ABC

from NEMO.models import Tool
from django.utils.timezone import now

from NEMO_fabublox_integration.models import FabubloxIntegrationConfiguration, ToolField


class Serializer(ABC):

    def __init__(self, instance_id: str, type_name: str):
        self.entity_type = type_name
        self.instance_id = instance_id
        self.instance_type = "NEMO"

    def get_obj_id(self, obj):
        return str(obj.id)

    def serialize(self, obj, fields=None):
        return {
            "source_type": self.instance_type,
            "source_id": self.instance_id,
            "entity_type": self.entity_type,
            "source_entity_id": self.get_obj_id(obj),
            "file_date_created": now().isoformat(),
            "data": self.serialize_entity(obj, fields),
        }

    def get_object_path(self, obj):
        timestamp = str(int(now().timestamp() * 1000))
        return f"{self.instance_type}/{self.instance_id}/{self.entity_type}/{self.get_obj_id(obj)}/{timestamp}.json"

    @abc.abstractmethod
    def serialize_entity(self, obj, fields: list[str] = None):
        return {}


class ToolSerializer(Serializer):
    def __init__(self, instance_id: str):
        super().__init__(instance_id, "tool")

    def serialize_entity(self, obj: Tool, fields: list[str] = None):
        # Name is always required
        data: dict = {"name": obj.name}
        if fields is None:
            fields = []

        if ToolField.DESCRIPTION.value in fields and obj.description:
            data["description"] = obj.description
        if ToolField.CATEGORY.value in fields and obj.category:
            data["category"] = obj.category
        if ToolField.LOCATION.value in fields and obj.location:
            data["location"] = obj.location

        if ToolField.PRIMARY_OWNER.value in fields and obj.primary_owner:
            primary_owner = {}
            if ToolField.PRIMARY_OWNER_FIRST_NAME.value in fields and obj.primary_owner.first_name:
                primary_owner["first_name"] = obj.primary_owner.first_name
            if ToolField.PRIMARY_OWNER_LAST_NAME.value in fields and obj.primary_owner.last_name:
                primary_owner["last_name"] = obj.primary_owner.last_name
            if ToolField.PRIMARY_OWNER_EMAIL.value in fields and obj.primary_owner.email:
                primary_owner["email"] = obj.primary_owner.email
            if len(primary_owner) > 0:
                data["primary_owner"] = primary_owner

        if ToolField.BACKUP_OWNERS.value in fields and obj.backup_owners.exists():
            backup_owners = []
            for backup_owner in obj.backup_owners.all():
                backup_owner_data = {}
                if ToolField.BACKUP_OWNERS_FIRST_NAME.value in fields and backup_owner.first_name:
                    backup_owner_data["first_name"] = backup_owner.first_name
                if ToolField.BACKUP_OWNERS_LAST_NAME.value in fields and backup_owner.last_name:
                    backup_owner_data["last_name"] = backup_owner.last_name
                if ToolField.BACKUP_OWNERS_EMAIL.value in fields and backup_owner.email:
                    backup_owner_data["email"] = backup_owner.email
                if len(backup_owner_data) > 0:
                    backup_owners.append(backup_owner_data)
            if len(backup_owners) > 0:
                data["backup_owners"] = backup_owners

        return data


def get_tool_serializer():
    lms_fabublox_instance_id = FabubloxIntegrationConfiguration.get_instance().instance_id
    if not lms_fabublox_instance_id:
        raise ValueError("Instance id for this LMS in FabuBlox is not set.")

    return ToolSerializer(lms_fabublox_instance_id)
