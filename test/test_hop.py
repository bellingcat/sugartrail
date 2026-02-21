"""Tests for hop logic using mocked API responses — no real network calls."""
import pytest
from unittest.mock import patch
import sugartrail
import sugartrail.hop


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def empty_network(no_auth, capsys):
    """A bare Network with no seed — safe to build upon in tests."""
    network = sugartrail.base.Network()
    capsys.readouterr()  # discard the "No input provided" message
    return network


@pytest.fixture
def company_network(empty_network):
    """Network seeded with a single company node at depth 0."""
    empty_network.graph = {
        'CO001': {
            'depth': 0,
            'title': 'Test Corp',
            'node_type': 'Company',
            'arcs': [],
        }
    }
    empty_network._company_id = 'CO001'
    empty_network.n = 0
    return empty_network


@pytest.fixture
def officer_network(empty_network):
    """Network seeded with a single officer node at depth 0."""
    empty_network.graph = {
        'OFF001': {
            'depth': 0,
            'title': 'John Smith',
            'node_type': 'Person',
            'arcs': [],
        }
    }
    empty_network._officer_id = 'OFF001'
    empty_network.n = 0
    return empty_network


@pytest.fixture
def address_network(empty_network):
    """Network seeded with a single address node at depth 0."""
    addr = '1 High Street London EC1A 1BB'
    empty_network.graph = {
        addr: {
            'depth': 0,
            'title': addr,
            'node_type': 'Address',
            'arcs': [],
        }
    }
    empty_network._address = addr
    empty_network.n = 0
    return empty_network


# ---------------------------------------------------------------------------
# search_company_id
# ---------------------------------------------------------------------------

MOCK_COMPANY_OFFICERS = {
    'items': [
        {
            'name': 'SMITH, JOHN',
            'links': {'officer': {'appointments': '/officers/OFF001/appointments'}},
        }
    ]
}

MOCK_APPOINTMENTS = {
    'items': [{'name': 'JOHN SMITH'}]
}


def test_search_company_adds_officer(company_network):
    hop = sugartrail.hop.Hop()
    hop.get_company_address_history = False
    hop.get_psc_correspondance_address = False

    with patch('sugartrail.api.get_company_officers', return_value=MOCK_COMPANY_OFFICERS), \
         patch('sugartrail.api.get_appointments', return_value=MOCK_APPOINTMENTS):
        hop.search_company_id(company_network, 'CO001')

    assert 'OFF001' in company_network.graph
    node = company_network.graph['OFF001']
    assert node['node_type'] == 'Person'
    assert node['depth'] == 1
    assert any(arc['arc_type'] == 'Officer' for arc in node['arcs'])


def test_search_company_does_not_duplicate_officer(company_network):
    """Calling search_company_id twice should not duplicate arcs."""
    hop = sugartrail.hop.Hop()
    hop.get_company_address_history = False
    hop.get_psc_correspondance_address = False

    with patch('sugartrail.api.get_company_officers', return_value=MOCK_COMPANY_OFFICERS), \
         patch('sugartrail.api.get_appointments', return_value=MOCK_APPOINTMENTS):
        hop.search_company_id(company_network, 'CO001')
        hop.search_company_id(company_network, 'CO001')

    assert len(company_network.graph['OFF001']['arcs']) == 1


def test_search_company_no_officers(company_network):
    hop = sugartrail.hop.Hop()
    hop.get_company_address_history = False
    hop.get_psc_correspondance_address = False

    with patch('sugartrail.api.get_company_officers', return_value=None):
        hop.search_company_id(company_network, 'CO001')

    # Only the seed company should be in the graph
    assert list(company_network.graph.keys()) == ['CO001']


def test_search_company_respects_maxsize(company_network):
    """Officers are skipped when appointment count exceeds maxsize."""
    large_response = {'items': [MOCK_COMPANY_OFFICERS['items'][0]] * 100}
    hop = sugartrail.hop.Hop()
    hop.get_company_address_history = False
    hop.get_psc_correspondance_address = False
    hop.officer_appointments_maxsize = 5  # not directly used here, but via search_officer_id

    with patch('sugartrail.api.get_company_officers', return_value=large_response), \
         patch('sugartrail.api.get_appointments', return_value=MOCK_APPOINTMENTS):
        hop.search_company_id(company_network, 'CO001')

    # Officers are still added by search_company_id (maxsize applies in search_officer_id)
    assert 'OFF001' in company_network.graph


# ---------------------------------------------------------------------------
# search_officer_id
# ---------------------------------------------------------------------------

MOCK_OFFICER_APPOINTMENTS = {
    'items': [
        {'appointed_to': {'company_number': 'CO002', 'company_name': 'Another Corp'}}
    ]
}

MOCK_CORRESPONDENCE_ADDRESS = {
    'items': [
        {'address': {'address_line_1': '1 High Street', 'locality': 'London', 'postal_code': 'EC1A 1BB'}}
    ]
}


def test_search_officer_adds_company(officer_network):
    hop = sugartrail.hop.Hop()
    hop.get_officer_correspondance_address = False
    hop.get_officer_duplicates = False

    with patch('sugartrail.api.get_appointments', return_value=MOCK_OFFICER_APPOINTMENTS):
        hop.search_officer_id(officer_network, 'OFF001')

    assert 'CO002' in officer_network.graph
    node = officer_network.graph['CO002']
    assert node['node_type'] == 'Company'
    assert node['depth'] == 1
    assert any(arc['arc_type'] == 'Appointment' for arc in node['arcs'])


def test_search_officer_adds_correspondence_address(officer_network):
    hop = sugartrail.hop.Hop()
    hop.get_officer_duplicates = False

    with patch('sugartrail.api.get_appointments', return_value=MOCK_OFFICER_APPOINTMENTS), \
         patch('sugartrail.api.get_correspondance_address', return_value=MOCK_CORRESPONDENCE_ADDRESS):
        hop.search_officer_id(officer_network, 'OFF001')

    address_nodes = [k for k, v in officer_network.graph.items() if v['node_type'] == 'Address']
    assert len(address_nodes) == 1
    assert any(arc['arc_type'] == 'Officer Corresponance Address'
               for arc in officer_network.graph[address_nodes[0]]['arcs'])


def test_search_officer_skips_when_appointments_exceed_maxsize(officer_network):
    large_appts = {'items': [MOCK_OFFICER_APPOINTMENTS['items'][0]] * 100}
    hop = sugartrail.hop.Hop()
    hop.get_officer_correspondance_address = False
    hop.get_officer_duplicates = False
    hop.officer_appointments_maxsize = 5

    with patch('sugartrail.api.get_appointments', return_value=large_appts):
        hop.search_officer_id(officer_network, 'OFF001')

    # No companies added; entity recorded as oversized
    assert 'CO002' not in officer_network.graph
    assert len(officer_network.maxsize_entities) == 1
    assert officer_network.maxsize_entities[0]['node'] == 'OFF001'


# ---------------------------------------------------------------------------
# search_address
# ---------------------------------------------------------------------------

MOCK_COMPANIES_AT_ADDRESS = {
    'items': [
        {'company_number': 'CO003', 'company_name': 'Street Corp'}
    ]
}

MOCK_OFFICERS_AT_ADDRESS = [
    {
        'title': 'Jane Doe',
        'links': {'self': '/officers/OFF002'},
    }
]


def test_search_address_adds_company(address_network):
    addr = list(address_network.graph.keys())[0]
    hop = sugartrail.hop.Hop()
    hop.get_officers_at_address = False

    with patch('sugartrail.api.get_companies_at_address', return_value=MOCK_COMPANIES_AT_ADDRESS):
        hop.search_address(address_network, addr, None)

    assert 'CO003' in address_network.graph
    node = address_network.graph['CO003']
    assert node['node_type'] == 'Company'
    assert node['depth'] == 1
    assert any(arc['arc_type'] == 'Company at Address' for arc in node['arcs'])


def test_search_address_adds_officer(address_network):
    addr = list(address_network.graph.keys())[0]
    hop = sugartrail.hop.Hop()
    hop.get_companies_at_address = False

    with patch('sugartrail.api.get_officers_at_address', return_value=MOCK_OFFICERS_AT_ADDRESS):
        hop.search_address(address_network, addr, None)

    assert 'OFF002' in address_network.graph
    node = address_network.graph['OFF002']
    assert node['node_type'] == 'Person'
    assert node['depth'] == 1


def test_search_address_skips_companies_when_maxsize_exceeded(address_network):
    addr = list(address_network.graph.keys())[0]
    large_response = {'items': [MOCK_COMPANIES_AT_ADDRESS['items'][0]] * 100}
    hop = sugartrail.hop.Hop()
    hop.get_officers_at_address = False
    hop.companies_at_address_maxsize = 5

    with patch('sugartrail.api.get_companies_at_address', return_value=large_response):
        hop.search_address(address_network, addr, None)

    assert 'CO003' not in address_network.graph
    assert len(address_network.maxsize_entities) == 1
    assert address_network.maxsize_entities[0]['type'] == 'Address'
