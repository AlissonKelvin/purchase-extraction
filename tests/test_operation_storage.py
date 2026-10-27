from elis_procurement_v2.adapters.operation_storage import (
    OperationStorage,
)


def test_operation_storage_persists_state(tmp_path):
    storage = OperationStorage(tmp_path / 'pending_operations.json')

    assert storage.load() == {}

    operations = {
        'example.pdf': {
            'operation_url': 'https://example.com/operation/123',
            'analyzer_id': 'test-analyzer',
        }
    }

    storage.save(operations)

    assert storage.load() == operations
