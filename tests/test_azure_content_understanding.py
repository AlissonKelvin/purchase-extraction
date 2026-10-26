from unittest.mock import MagicMock, patch

from elis_procurement_v2.adapters.azure_content_understanding import (
    AzureContentUnderstanding,
)


@patch('elis_procurement_v2.adapters.azure_content_understanding.httpx.Client')
def test_analyze_pdf(mock_client_class, monkeypatch):
    monkeypatch.setenv(
        'AZURE_CONTENT_UNDERSTANDING_ENDPOINT',
        'https://example.cognitiveservices.azure.com',
    )
    monkeypatch.setenv(
        'AZURE_CONTENT_UNDERSTANDING_KEY',
        'fictitious-key',
    )
    monkeypatch.setenv(
        'AZURE_CONTENT_UNDERSTANDING_ANALYZER_ID',
        'invoice-analyzer',
    )

    mock_client = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_client

    mock_post_response = MagicMock()
    mock_post_response.status_code = 202
    mock_post_response.headers = {
        'Operation-Location': (
            'https://example.cognitiveservices.azure.com/'
            'contentunderstanding/analyzerResults/test-operation'
        )
    }

    mock_get_response = MagicMock()
    mock_get_response.json.return_value = {
        'status': 'succeeded',
        'result': {
            'contents': [
                {
                    'fields': {
                        'SupplierName': {
                            'type': 'string',
                            'valueString': 'Example Supplier',
                        }
                    }
                }
            ]
        },
    }

    mock_client.post.return_value = mock_post_response
    mock_client.get.return_value = mock_get_response

    adapter = AzureContentUnderstanding()
    result = adapter.analyze_pdf(b'%PDF-1.4 fictitious content')

    assert result['status'] == 'succeeded'
    assert (
        result['result']['contents'][0]['fields']['SupplierName']['valueString']
        == 'Example Supplier'
    )

    mock_client.post.assert_called_once()
    mock_client.get.assert_called_once()
