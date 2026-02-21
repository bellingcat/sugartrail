"""Integration tests for the Companies House API.

These tests make real network requests and require a valid API key in .env.
Run them with:

    uv run pytest test/test_api_integration.py -v

They are excluded from the default test run (which uses no markers).
"""
import pytest
import sugartrail.api as api

# ---------------------------------------------------------------------------
# Stable test fixtures from the example notebooks
# ---------------------------------------------------------------------------
COMPANY_ID = "11951034"       # DOMAIN FOUNDATION (quickstart example)
COMPANY_ID_2 = "11004735"     # KINGDOM OF SWEETS LTD (getting_started example)
OFFICER_ID = "W806gf93kuLBqHdMWnoaBuG08m8"  # Alexis MARCO


@pytest.fixture(autouse=True)
def require_api_key():
    """Skip every test in this file if no API key is configured."""
    if not api.basic_auth.username:
        pytest.skip("No API key found — set COMPANIES_HOUSE_API_KEY in .env")


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_api_auth_succeeds():
    assert api.test() is True


# ---------------------------------------------------------------------------
# Company endpoints
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_get_company_returns_expected_name():
    result = api.get_company(COMPANY_ID)
    assert result is not None
    assert result["company_number"] == COMPANY_ID
    assert "company_name" in result

@pytest.mark.integration
def test_get_company_officers_returns_list():
    result = api.get_company_officers(COMPANY_ID)
    assert result is not None
    assert "items" in result
    assert isinstance(result["items"], list)
    assert len(result["items"]) > 0

@pytest.mark.integration
def test_get_psc_returns_result():
    result = api.get_psc(COMPANY_ID)
    assert result is not None
    assert "items" in result

@pytest.mark.integration
def test_get_address_changes_returns_result():
    result = api.get_address_changes(COMPANY_ID)
    assert result is not None
    assert "items" in result

@pytest.mark.integration
def test_get_company_unknown_id_returns_none():
    result = api.get_company("00000000")
    assert result is None


# ---------------------------------------------------------------------------
# Officer endpoints
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_get_appointments_returns_list():
    result = api.get_appointments(OFFICER_ID)
    assert result is not None
    assert "items" in result
    assert isinstance(result["items"], list)
    assert len(result["items"]) > 0

@pytest.mark.integration
def test_get_correspondance_address_returns_result():
    result = api.get_correspondance_address(OFFICER_ID)
    assert result is not None
    assert "items" in result

@pytest.mark.integration
def test_get_duplicate_officers_returns_list_or_none():
    result = api.get_duplicate_officers(OFFICER_ID)
    # May return None or a list depending on whether duplicates exist
    assert result is None or isinstance(result, list)


# ---------------------------------------------------------------------------
# Address endpoints
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_get_companies_at_address_returns_result():
    # Use a postcode known to have registered companies
    result = api.get_companies_at_address("EC1A 1BB")
    assert result is not None
    assert "items" in result

@pytest.mark.integration
def test_get_officers_at_address_returns_list():
    result = api.get_officers_at_address("EC1A 1BB")
    # Returns a filtered list (may be empty for some addresses)
    assert result is None or isinstance(result, list)
