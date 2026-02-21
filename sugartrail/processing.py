import sugartrail
import requests
import urllib
import regex as re
import collections
import os
import IPython
from string import ascii_letters as alc
import warnings
warnings.filterwarnings('ignore')

def condense_path(path):
    condensed_path = []
    for i, item in enumerate(path):
        item_subset = dict((k, item[k]) for k in ('title', 'depth', 'node_type', 'id', 'link_type'))
        matching_items = [item_whole for item_whole in path if item_subset.items() <= item_whole.items()]
        item_subset['link'] = []
        for item_whole in matching_items:
            item_subset['link'].append(item_whole['link'])
        if item_subset not in condensed_path:
            condensed_path.append(item_subset)
    return condensed_path

def asciiify_path(path):
    for i, item in enumerate(path):
        path[i]['node_index'] = int(1+i/51)*alc[i%51]
        path[i]['link'] = ", ".join([d['node_index'] for d in path if d['id'] in path[i]['link']])
    return path

def get_companies_from_address_database(address, company_data):
    """Searches input dataframe (company_data) for companies at input address
    (address) and returns list of dicts."""
    companies = company_data[company_data[' RegAddress.AddressLine2'].apply(lambda x: str(x).upper() in address.upper()) | company_data['RegAddress.AddressLine1'].apply(lambda x: str(x).upper() in address.upper()) & company_data['RegAddress.PostCode'].apply(lambda x: str(x).upper() in address.upper())]
    companies = companies.rename(columns={'CompanyName': 'company_name', ' CompanyNumber': 'company_number', 'CompanyStatus': 'company_status', 'CompanyCategory': 'company_type', 'RegAddress.AddressLine1': 'address_line_1', ' RegAddress.AddressLine2': 'address_line_2', 'RegAddress.PostCode': 'postal_code', 'RegAddress.PostTown': 'locality', 'RegAddress.Country': 'country', 'IncorporationDate':'date_of_creation', 'DissolutionDate': 'date_of_cessation'})
    companies['registered_office_address'] = [{'address_line_1': row['address_line_1'], 'address_line_2': row['address_line_2'], 'locality': row['locality'], 'postal_code': row['postal_code'], 'country': row['country']} for i,row in companies.iterrows()]
    return companies.to_dict('records')

def process_address_changes(address_changes):
    """Attempt retrieval of 'new_address' value if Companies House record is
    incomplete."""
    for i in reversed(range(1,len(address_changes['items']))):
        item = address_changes['items'][i]
        prev_item = address_changes['items'][i-1]
        if 'description_values' not in item:
            continue
        if 'new_address' not in item['description_values']:
            if 'description_values' in prev_item and 'old_address' in prev_item['description_values']:
                item['description_values']['new_address'] = prev_item['description_values']['old_address']
    return address_changes

def build_address_history(company_id):
    """Returns a list of dicts containing historic addresses for input company
    (company_id)."""
    company_info = sugartrail.api.get_company(company_id)
    if company_info:
        company_info_subset = {k:company_info[k] for k in ("date_of_creation","date_of_cessation","registered_office_address") if k in company_info}
        address_changes = sugartrail.api.get_address_changes(company_id)
        address_keys = ('start_date','end_date','address')
        if address_changes:
            if 'items' in address_changes:
                if address_changes['items']:
                    # attempt to retrieve any missing items within address changes
                    address_changes = process_address_changes(address_changes)
                    addresses = []
                    entry = {}
                    entry["company_number"] = str(company_id)
                    entry["lat"] = ""
                    entry["lon"] = ""
                    entry["address"] = str(sugartrail.utils.normalise_address(company_info_subset['registered_office_address']))
                    entry["start_date"] = str(address_changes['items'][0]['date'])
                    if 'date_of_cessation' in company_info_subset:
                        entry["end_date"] = str(company_info_subset['date_of_cessation'])
                    else:
                        entry["end_date"] = None
                    addresses.append(entry)
                    for i,change in enumerate(address_changes['items']):
                        entry = {}
                        entry["lat"] = ""
                        entry["lon"] = ""
                        entry["company_number"] = str(company_id)
                        if 'description_values' in change and 'old_address' in change['description_values']:
                            entry["address"] = change['description_values']['old_address']
                        else:
                            entry["address"] = ""
                        if i+1 < len(address_changes['items']):
                            entry["start_date"] = str(address_changes['items'][i+1]['date'])
                        else:
                            entry["start_date"] = company_info_subset['date_of_creation']
                        entry["end_date"] = str(change['date'])
                        addresses.append(entry)
                    return addresses
                else:
                    entry = {}
                    for k, key in enumerate(["date_of_creation","date_of_cessation","registered_office_address"]):
                        if key in company_info:
                            entry[address_keys[k]] = company_info[key]
                        else:
                            entry[address_keys[k]] = None
                    entry["company_number"] = str(company_id)
                    entry['address'] = sugartrail.utils.normalise_address(entry['address'])
                    entry["lat"] = ""
                    entry["lon"] = ""
                    return [entry]
        else:
            entry = {}
            for k, key in enumerate(["date_of_creation","date_of_cessation","registered_office_address"]):
                if key in company_info:
                    entry[address_keys[k]] = company_info[key]
                else:
                    entry[address_keys[k]] = None
            entry["company_number"] = str(company_id)
            entry['address'] = sugartrail.utils.normalise_address(entry['address'])
            entry["lat"] = ""
            entry["lon"] = ""
            return [entry]
    else:
        return []
