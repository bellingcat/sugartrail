import sugartrail.processing as processing


# Minimal path entries used across tests
def make_entry(title, depth, node_type, id, link_type="", link=""):
    return {
        'title': title,
        'depth': depth,
        'node_type': node_type,
        'id': id,
        'link_type': link_type,
        'link': link,
    }


# --- condense_path ---

def test_condense_path_single_entry():
    path = [make_entry('Test Corp', 0, 'Company', 'CO001')]
    result = processing.condense_path(path)
    assert len(result) == 1
    assert result[0]['id'] == 'CO001'
    assert result[0]['link'] == ['']

def test_condense_path_two_distinct_entries():
    path = [
        make_entry('Test Corp', 0, 'Company', 'CO001'),
        make_entry('John Smith', 1, 'Person', 'OFF001', 'Officer', 'CO001'),
    ]
    result = processing.condense_path(path)
    assert len(result) == 2

def test_condense_path_deduplicates_identical_entries():
    entry = make_entry('Test Corp', 0, 'Company', 'CO001')
    path = [entry.copy(), entry.copy()]
    result = processing.condense_path(path)
    assert len(result) == 1


# --- asciiify_path ---

def test_asciiify_path_adds_node_index():
    path = [make_entry('Test Corp', 0, 'Company', 'CO001')]
    # condense_path must run first to set link as a list
    path = processing.condense_path(path)
    result = processing.asciiify_path(path)
    assert 'node_index' in result[0]
    assert result[0]['node_index'] == 'a'

def test_asciiify_path_link_becomes_string():
    path = [
        make_entry('Test Corp', 0, 'Company', 'CO001'),
        make_entry('John Smith', 1, 'Person', 'OFF001', 'Officer', 'CO001'),
    ]
    path = processing.condense_path(path)
    result = processing.asciiify_path(path)
    # link field should now be a comma-separated string, not a list
    for item in result:
        assert isinstance(item['link'], str)


# --- process_address_changes ---

def test_process_address_changes_fills_missing_new_address():
    data = {
        'items': [
            {
                'description_values': {'new_address': '2 New St', 'old_address': '1 Old St'},
                'date': '2020-01-01',
            },
            {
                # missing new_address — should be filled from item[0]'s old_address
                'description_values': {'old_address': '0 Older St'},
                'date': '2019-01-01',
            },
        ]
    }
    result = processing.process_address_changes(data)
    assert result['items'][1]['description_values']['new_address'] == '1 Old St'

def test_process_address_changes_leaves_existing_new_address_intact():
    data = {
        'items': [
            {
                'description_values': {'new_address': '2 New St', 'old_address': '1 Old St'},
                'date': '2020-01-01',
            },
            {
                'description_values': {'new_address': 'Already Set', 'old_address': '0 Older St'},
                'date': '2019-01-01',
            },
        ]
    }
    result = processing.process_address_changes(data)
    assert result['items'][1]['description_values']['new_address'] == 'Already Set'

def test_process_address_changes_single_item():
    data = {'items': [{'description_values': {'new_address': 'Only St'}, 'date': '2020-01-01'}]}
    result = processing.process_address_changes(data)
    assert result['items'][0]['description_values']['new_address'] == 'Only St'

def test_process_address_changes_missing_description_values():
    # Some Companies House responses omit 'description_values' entirely — should not raise KeyError
    data = {
        'items': [
            {'description_values': {'new_address': '2 New St', 'old_address': '1 Old St'}, 'date': '2020-01-01'},
            {'date': '2019-01-01'},  # no description_values at all
        ]
    }
    result = processing.process_address_changes(data)
    assert 'description_values' not in result['items'][1]


# --- build_address_history (mocked API) ---

from unittest.mock import patch

MOCK_COMPANY_INFO = {
    'date_of_creation': '2018-01-01',
    'registered_office_address': {'address_line_1': '1 High St', 'locality': 'London', 'postal_code': 'EC1A 1BB'},
}

def test_build_address_history_item_missing_description_values():
    """Filing history items without 'description_values' should not raise KeyError."""
    address_changes = {
        'items': [
            # normal item
            {'description_values': {'old_address': '0 Old St'}, 'date': '2019-06-01'},
            # item with no description_values at all
            {'date': '2018-01-01'},
        ]
    }
    with patch('sugartrail.api.get_company', return_value=MOCK_COMPANY_INFO), \
         patch('sugartrail.api.get_address_changes', return_value=address_changes):
        result = processing.build_address_history('CO001')

    assert result is not None
    addresses = [entry['address'] for entry in result]
    # The item missing description_values should produce an empty address, not crash
    assert '' in addresses
