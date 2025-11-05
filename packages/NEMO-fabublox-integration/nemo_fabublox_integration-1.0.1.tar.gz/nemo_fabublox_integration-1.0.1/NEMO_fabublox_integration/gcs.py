import json
from logging import getLogger

from google.cloud import storage
from google.oauth2 import service_account

gcs_logger = getLogger(__name__)


def get_gcs_bucket(sa_key, bucket_name):
    try:
        credentials = service_account.Credentials.from_service_account_info(sa_key)
        client = storage.Client(credentials=credentials, project=credentials.project_id)
        return client.bucket(bucket_name)
    except Exception as e:
        gcs_logger.error(f"Failed to initialize GCS bucket '{bucket_name}': {e}")
        raise ValueError(f"Failed to initialize GCS bucket")


def upload_json_to_gcs(data: dict, destination_blob_name: str, bucket: storage.Bucket):
    blob = bucket.blob(destination_blob_name)
    json_data = json.dumps(data)
    blob.upload_from_string(json_data, content_type="application/json")
