import os
from time import sleep
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()


class AzureContentUnderstanding:
    def __init__(self):
        self.endpoint = os.getenv('AZURE_CONTENT_UNDERSTANDING_ENDPOINT', '').rstrip('/')
        self.api_key = os.getenv('AZURE_CONTENT_UNDERSTANDING_KEY') or ''
        self.analyzer_id = os.getenv('AZURE_CONTENT_UNDERSTANDING_ANALYZER_ID') or ''
        if not all([self.endpoint, self.api_key, self.analyzer_id]):
            raise ValueError(
                'AZURE_CONTENT_UNDERSTANDING_ENDPOINT, AZURE_CONTENT_UNDERSTANDING_KEY,'
                ' or AZURE_CONTENT_UNDERSTANDING_ANALYZER_ID is not set in the environment variables.'
            )
        self.headers: dict[str, str] = {
            'Ocp-Apim-Subscription-Key': self.api_key,
        }

    def analyze_pdf(self, pdf_bytes: bytes) -> dict[str, Any]:
        if not pdf_bytes:
            raise ValueError('PDF bytes cannot be empty.')

        url = (
            f'{self.endpoint}/contentunderstanding/analyzers/'
            f'{self.analyzer_id}:analyzeBinary'
        )

        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                url,
                params={'api-version': '2025-11-01'},
                headers={
                    **self.headers,
                    'Content-Type': 'application/pdf',
                },
                content=pdf_bytes,
            )
            response.raise_for_status()

            if response.status_code != 202:
                raise RuntimeError(
                    f'Unexpected status code: {response.status_code}. '
                    f'Response: {response.text}'
                )
            opration_url = response.headers.get('Operation-Location')

            if not opration_url:
                raise RuntimeError(
                    'Operation-Location header is missing in the response.'
                )

            for _ in range(40):
                result_response = client.get(
                    opration_url,
                    params={'api-version': '2025-11-01'},
                    headers=self.headers,
                )
                result_response.raise_for_status()

                result = result_response.json()
                status = str(result.get('status', '')).lower()

                if status == 'succeeded':
                    if not result.get('result'):
                        raise RuntimeError('Analysis succeeded without a result')
                    return result

                if status in ('failed', 'canceled'):
                    raise RuntimeError(f'Content Understanding analysis: {status}')

                sleep(3)

        raise TimeoutError('Content Understanding analysis did not finish in time.')
