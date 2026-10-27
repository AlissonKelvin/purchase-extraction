import json
from typing import Any, cast
from unittest.mock import patch

from elis_procurement_v2.adapters.azure_blob_storage import (
    AzureBlobStorage,
)


@patch(
    'elis_procurement_v2.adapters.azure_blob_storage.'
    'BlobServiceClient.from_connection_string'
)
def test_upload_json(mock_from_connection_string, monkeypatch) -> None:
    monkeypatch.setenv(
        'AZURE_STORAGE_CONNECTION_STRING',
        'fictitious-connection-string',
    )
    monkeypatch.setenv(
        'AZURE_STORAGE_CONTAINER_RAW',
        'invoices-raw',
    )
    monkeypatch.setenv(
        'AZURE_STORAGE_CONTAINER_PROCESSED',
        'invoices-processed',
    )

    storage = AzureBlobStorage()

    storage.upload_json(
        container_name='invoices-processed',
        blob_name='test-invoice.json',
        data={'invoice_total': '150.00'},
    )

    blob_client = mock_from_connection_string.return_value.get_blob_client.return_value

    blob_client.upload_blob.assert_called_once()

    args, kwargs = blob_client.upload_blob.call_args

    assert json.loads(args[0]) == {'invoice_total': '150.00'}
    assert kwargs['overwrite'] is False


@patch(
    'elis_procurement_v2.adapters.azure_blob_storage.'
    'BlobServiceClient.from_connection_string'
)
def test_download_pdf(mock_from_connection_string, monkeypatch):
    monkeypatch.setenv(
        'AZURE_STORAGE_CONNECTION_STRING',
        'fictitious-connection-string',
    )
    monkeypatch.setenv(
        'AZURE_STORAGE_CONTAINER_RAW',
        'invoices-raw',
    )
    monkeypatch.setenv(
        'AZURE_STORAGE_CONTAINER_PROCESSED',
        'invoices-processed',
    )

    storage = AzureBlobStorage()

    expected_content = b'%PDF-1.4\nfictitious-pdf'

    blob_client = mock_from_connection_string.return_value.get_blob_client.return_value

    blob_client.download_blob.return_value.readall.return_value = expected_content

    result = storage.download_pdf('example-invoice.pdf')

    assert result == expected_content

    cast(Any, storage.client).get_blob_client.assert_called_once_with(
        container='invoices-raw',
        blob='example-invoice.pdf',
    )


@patch(
    'elis_procurement_v2.adapters.azure_blob_storage.'
    'BlobServiceClient.from_connection_string'
)
def test_list_pdfs(mock_from_connection_string, monkeypatch):
    monkeypatch.setenv(
        'AZURE_STORAGE_CONNECTION_STRING',
        'fictitious-connection-string',
    )
    monkeypatch.setenv(
        'AZURE_STORAGE_CONTAINER_RAW',
        'invoices-raw',
    )
    monkeypatch.setenv(
        'AZURE_STORAGE_CONTAINER_PROCESSED',
        'invoices-processed',
    )

    container_client = (
        mock_from_connection_string.return_value.get_container_client.return_value
    )

    container_client.list_blob_names.return_value = [
        'invoice-b.PDF',
        'notes.txt',
        'invoice-a.pdf',
        'folder/invoice-c.pdf',
    ]

    storage = AzureBlobStorage()

    result = storage.list_pdfs()

    assert result == [
        'folder/invoice-c.pdf',
        'invoice-a.pdf',
        'invoice-b.PDF',
    ]

    cast(Any, storage.client).get_container_client.assert_called_once_with(
        'invoices-raw'
    )

    container_client.list_blob_names.assert_called_once_with()


@patch(
    'elis_procurement_v2.adapters.azure_blob_storage.'
    'BlobServiceClient.from_connection_string'
)
def test_blob_exists(mock_from_connection_string, monkeypatch):
    monkeypatch.setenv(
        'AZURE_STORAGE_CONNECTION_STRING',
        'fictitious-connection-string',
    )

    storage = AzureBlobStorage()

    blob_client = mock_from_connection_string.return_value.get_blob_client.return_value

    blob_client.exists.return_value = True

    assert storage.blob_exists(
        'invoices-processed',
        'invoice-example.json',
    )

    cast(Any, storage.client).get_blob_client.assert_called_once_with(
        container='invoices-processed',
        blob='invoice-example.json',
    )
