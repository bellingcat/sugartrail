import pytest
import json
from pathlib import Path
import sugartrail

# Use an absolute path so tests pass regardless of working directory.
# quickstart_a.json is a pre-generated file committed to the repo.
NETWORK_FILE = str(Path(__file__).parent.parent / 'assets/networks/quickstart_a.json')

NETWORK_FILE = str(Path(__file__).parent.parent / 'assets/networks/quickstart_a.json')


# ---------------------------------------------------------------------------
# Initialisation without arguments
# ---------------------------------------------------------------------------

def test_init_without_arguments(no_auth, capsys):
    sugartrail.base.Network()
    captured = capsys.readouterr()
    assert captured.out == 'No input provided. Please provide either officer_id, company_id, address or file as input.\n'


# ---------------------------------------------------------------------------
# Initialisation without auth prints requirement message
# ---------------------------------------------------------------------------

def test_init_officer_without_auth(no_auth, capsys):
    sugartrail.base.Network(officer_id='_')
    captured = capsys.readouterr()
    assert captured.out == 'Authentication required\n'

def test_init_company_without_auth(no_auth, capsys):
    sugartrail.base.Network(company_id='_')
    captured = capsys.readouterr()
    assert captured.out == 'Authentication required\n'

def test_init_address_without_auth(no_auth, capsys):
    sugartrail.base.Network(address='_')
    captured = capsys.readouterr()
    assert captured.out == 'Authentication required\n'


# ---------------------------------------------------------------------------
# State is unchanged when auth fails
# ---------------------------------------------------------------------------

def test_empty_officer_without_auth(no_auth, capsys):
    network = sugartrail.base.Network(officer_id='_')
    assert network._officer_id is None

def test_empty_company_without_auth(no_auth, capsys):
    network = sugartrail.base.Network(company_id='_')
    assert network._company_id is None

def test_empty_address_without_auth(no_auth, capsys):
    network = sugartrail.base.Network(address='_')
    assert network._address is None


# ---------------------------------------------------------------------------
# Loading a network from file (no auth required)
# ---------------------------------------------------------------------------

def test_file_init_without_auth():
    network = sugartrail.base.Network(file=NETWORK_FILE)
    with open(NETWORK_FILE) as f:
        network_json = json.load(f)
    for key in network.__dict__.keys():
        if key not in sugartrail.base.Network._unserialisable_attributes:
            assert network.__dict__[key] == network_json[key]

def test_file_load_without_auth(capsys):
    network = sugartrail.base.Network()
    capsys.readouterr()  # discard "No input provided" message
    network.load(NETWORK_FILE)
    with open(NETWORK_FILE) as f:
        network_json = json.load(f)
    for key in network.__dict__.keys():
        if key not in sugartrail.base.Network._unserialisable_attributes:
            assert network.__dict__[key] == network_json[key]


# ---------------------------------------------------------------------------
# find_path — pure graph traversal, no API calls needed
# ---------------------------------------------------------------------------

@pytest.fixture
def two_node_network(no_auth, capsys):
    """Network with a seed company connected to one officer."""
    network = sugartrail.base.Network()
    capsys.readouterr()
    network.graph = {
        'CO001': {
            'title': 'Test Corp',
            'depth': 0,
            'node_type': 'Company',
            'arcs': [],
        },
        'OFF001': {
            'title': 'John Smith',
            'depth': 1,
            'node_type': 'Person',
            'arcs': [{'arc_type': 'Officer', 'start_node': 'CO001'}],
        },
    }
    network.n = 1
    return network


def test_find_path_from_seed_returns_single_node(two_node_network):
    path = two_node_network.find_path('CO001')
    assert len(path) == 1
    assert path[0]['id'] == 'CO001'
    assert path[0]['node_type'] == 'Company'


def test_find_path_to_connected_node_includes_both(two_node_network):
    path = two_node_network.find_path('OFF001')
    ids = [item['id'] for item in path]
    assert 'CO001' in ids
    assert 'OFF001' in ids


def test_find_path_is_ordered_from_seed(two_node_network):
    path = two_node_network.find_path('OFF001')
    # Path should start at depth 0 (the seed)
    assert path[0]['depth'] == 0


# ---------------------------------------------------------------------------
# Graph property views
# ---------------------------------------------------------------------------

def test_company_ids_property(two_node_network):
    companies = two_node_network.company_ids
    assert len(companies) == 1
    assert companies[0]['company_id'] == 'CO001'

def test_officer_ids_property(two_node_network):
    officers = two_node_network.officer_ids
    assert len(officers) == 1
    assert officers[0]['officer_id'] == 'OFF001'
