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

    def start_analysis(self, pdf_bytes: bytes) -> str:
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
                raise RuntimeError(f'Unexpected analysis status: {response.status_code}')

            operation_url = response.headers.get('Operation-Location')

            if not operation_url:
                raise RuntimeError('Operation-Location header is missing.')

            return operation_url

    def get_analysis_result(
        self,
        operation_url: str,
        max_attempts: int = 60,
    ) -> dict[str, Any]:
        if max_attempts < 1:
            raise ValueError('max_attempts must be greater than zero.')

        expected_prefix = f'{self.endpoint}/contentunderstanding/analyzerResults/'

        if not operation_url.startswith(expected_prefix):
            raise ValueError('Invalid Content Understanding operation URL.')

        with httpx.Client(timeout=60.0) as client:
            for attempt in range(max_attempts):
                response = client.get(
                    operation_url,
                    headers=self.headers,
                )
                response.raise_for_status()

                result = response.json()
                status = str(result.get('status', '')).lower()

                if status == 'succeeded':
                    if not result.get('result'):
                        raise RuntimeError('Analysis succeeded without a result.')

                    return result

                if status in ('failed', 'canceled', 'cancelled'):
                    raise RuntimeError(f'Content Understanding analysis: {status}')

                if status not in ('running', 'notstarted'):
                    raise RuntimeError(f'Unexpected analysis status: {status}')

                if attempt < max_attempts - 1:
                    sleep(3)

        raise TimeoutError(
            'Content Understanding analysis is still pending. '
            'The operation can be queried again.'
        )

    def analyze_pdf(self, pdf_bytes: bytes) -> dict[str, Any]:
        operation_url = self.start_analysis(pdf_bytes)
        return self.get_analysis_result(operation_url)
