import sugartrail.utils as utils


# --- normalise_address ---

def test_normalise_address_all_keys():
    addr = {
        'premises': '1',
        'address_line_1': 'High Street',
        'locality': 'London',
        'postal_code': 'EC1A 1BB',
        'country': 'England',
    }
    assert utils.normalise_address(addr) == "1 High Street London EC1A 1BB England"

def test_normalise_address_partial_keys():
    addr = {'address_line_1': 'High Street', 'postal_code': 'EC1A 1BB'}
    assert utils.normalise_address(addr) == "High Street EC1A 1BB"

def test_normalise_address_empty():
    assert utils.normalise_address({}) == ""

def test_normalise_address_ignores_unknown_keys():
    addr = {'address_line_1': 'High Street', 'fax': '0800 000 000'}
    assert utils.normalise_address(addr) == "High Street"


# --- normalise_name ---

def test_normalise_name_moves_first_word_to_end():
    # "SMITH JOHN" → pop SMITH → ['JOHN', 'SMITH'] → "JOHN SMITH"
    assert utils.normalise_name("SMITH JOHN") == "JOHN SMITH"

def test_normalise_name_single_word():
    # Only one word: pop it and re-append → same result
    assert utils.normalise_name("SMITH") == "SMITH"

def test_normalise_name_removes_commas():
    # Commas are stripped before splitting
    result = utils.normalise_name("SMITH,JOHN")
    assert "SMITH" in result
    assert "JOHN" in result


# --- infer_postcode ---

def test_infer_postcode_standard_format():
    assert utils.infer_postcode("1 High Street EC1A 1BB London") == "EC1A 1BB"

def test_infer_postcode_short_format():
    assert utils.infer_postcode("Some Road W1A 0AX") == "W1A 0AX"

def test_infer_postcode_no_match():
    assert utils.infer_postcode("1 High Street London") is None

def test_infer_postcode_empty_string():
    assert utils.infer_postcode("") is None


# --- ensure_json_extension ---

def test_ensure_json_extension_adds_extension():
    assert utils.ensure_json_extension("myfile") == "myfile.json"

def test_ensure_json_extension_keeps_existing():
    assert utils.ensure_json_extension("myfile.json") == "myfile.json"

def test_ensure_json_extension_replaces_other():
    # os.path.splitext strips the extension, then .json is appended
    assert utils.ensure_json_extension("myfile.txt") == "myfile.json"


# --- flatten ---

def test_flatten_nested_dict():
    d = {"a": {"b": 1, "c": 2}, "d": 3}
    assert utils.flatten(d) == {"a.b": 1, "a.c": 2, "d": 3}

def test_flatten_already_flat():
    d = {"a": 1, "b": 2}
    assert utils.flatten(d) == {"a": 1, "b": 2}

def test_flatten_deeply_nested():
    d = {"a": {"b": {"c": 42}}}
    assert utils.flatten(d) == {"a.b.c": 42}

def test_flatten_empty():
    assert utils.flatten({}) == {}
