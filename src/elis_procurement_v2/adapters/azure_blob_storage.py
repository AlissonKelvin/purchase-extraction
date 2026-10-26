import json
import os
from typing import Any

from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv

load_dotenv()


class AzureBlobStorage:
    def __init__(self):
        self.connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        if not self.connection_string:
            raise ValueError(
                'AZURE_STORAGE_CONNECTION_STRING is not set in the environment variables.'
            )
        self.container_raw = os.getenv('AZURE_STORAGE_CONTAINER_RAW')
        self.container_processed = os.getenv('AZURE_STORAGE_CONTAINER_PROCESSED')
        if not self.container_raw or not self.container_processed:
            raise ValueError(
                'AZURE_STORAGE_CONTAINER_RAW or AZURE_STORAGE_CONTAINER_PROCESSED is not set in the environment variables.'
            )
        self.client = BlobServiceClient.from_connection_string(self.connection_string)

    def upload_json(
        self,
        container_name: str,
        blob_name: str,
        data: dict[str, Any],
    ) -> None:
        blob_client = self.client.get_blob_client(
            container=container_name,
            blob=blob_name,
        )

        content = json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )

        blob_client.upload_blob(
            content.encode('utf-8'),
            overwrite=False,
            content_settings=ContentSettings(
                content_type='application/json',
            ),
        )

    def download_pdf(self, blob_name: str) -> bytes:
        blob_client = self.client.get_blob_client(
            container=self.container_raw or '',
            blob=blob_name,
        )

        download_stream = blob_client.download_blob()
        return download_stream.readall()
