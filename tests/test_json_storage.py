import json

from elis_procurement_v2.adapters.json_storage import save_json


def test_save_json(tmp_path) -> None:
    data = {
        'supplier_name': 'Example Supplier Ltd',
        'invoice_total': '150.00',
        'reconciliation_status': 'matched',
    }

    file_path = tmp_path / 'processed' / 'invoice.json'

    save_json(data, file_path)

    assert file_path.exists()

    saved_data = json.loads(file_path.read_text(encoding='utf-8'))

    assert saved_data == data
