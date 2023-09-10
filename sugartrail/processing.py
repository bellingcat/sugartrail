from sugartrail import api
import requests
import urllib
import regex as re
import collections
import IPython
from string import ascii_letters as alc

def flatten(d, parent_key='', sep='.'):
    """Flatten nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.abc.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def infer_postcode(address_string):
    """Extracts UK postcode from input address string with regex."""
    postcode = re.findall(r'\b[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][ABD-HJLNP-UW-Z]{2}\b', address_string)
    if postcode:
        return postcode[0]
    else:
        return

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

def get_nearby_postcode(postcode_string):
    """Find closest nearby postcode to input postcode (postcode_string)."""
    url = "http://api.postcodes.io/postcodes/" + postcode_string[:-1] + "/autocomplete"
    response = requests.get(url).json()
    if response['result'] != None:
        closest_address = {}
        for postcode in response["result"]:
            distance = abs(ord(postcode[-1]) - ord(postcode_string[-1]))
            if closest_address:
                if distance < closest_address["distance"]:
                    closest_address = {"postcode": postcode, "distance": distance}
            else:
                closest_address = {"postcode": postcode, "distance": distance}
        return closest_address["postcode"]

def get_coords_from_address(address_string):
    """Attempt retrieval of coords for input address string."""
    params = {'q': address_string, 'format': 'json'}
    url = 'https://nominatim.openstreetmap.org/search?' + urllib.parse.urlencode(params)
    response = requests.get(url).json()
    if response:
        return {'lat': response[0]['lat'], 'lon': response[0]['lon'], 'address': address_string}
    else:
        postcode_string = infer_postcode(address_string)
        if postcode_string:
            url = "http://api.postcodes.io/postcodes/" + urllib.parse.quote(postcode_string)
            response = requests.get(url).json()
            if str(response['status']) == '200':
                return {'lat': response['result']['latitude'], 'lon': response['result']['longitude'], 'postcode': postcode_string}
            else:
                # try nearby postcode:
                nearby_postcode = get_nearby_postcode(postcode_string)
                if nearby_postcode:
                    url = "http://api.postcodes.io/postcodes/" + urllib.parse.quote(nearby_postcode)
                    response = requests.get(url).json()
                    if str(response['status']) == "200":
                        return {'lat': response['result']['latitude'], 'lon': response['result']['longitude'], 'postcode': nearby_postcode}
                else:
                    print("failed")
        else:
            # print("No postcode found for: " + address_string)
            pass

def normalise_name(name):
    """Move first word (often surname) from the beginning to the end of string."""
    name_list = name.replace(',','').split(" ")
    name_list.append(name_list.pop(0))
    return ' '.join(name_list)

def process_address_changes(address_changes):
    """Attempt retrieval of 'new_address' value if Companies House record is
    incomplete."""
    for i in reversed(range(1,len(address_changes['items']))):
        if 'new_address' not in address_changes['items'][i]['description_values'].keys():
            if 'old_address' in address_changes['items'][i-1]['description_values'].keys():
                address_changes['items'][i]['description_values']['new_address'] = address_changes['items'][i-1]['description_values']['old_address']
    return address_changes

def find_network_connections(first_network, second_network, max_depth=5, print_progress=False):
    """Returns a list of nodes connecting ."""
    hops = 0
    while hops < max_depth:
        first_network.progress.pre_print = str(hops) + "/" + str(max_depth) + " hops completed."
        second_network.progress.pre_print = str(hops) + "/" + str(max_depth) + " hops completed."
        first_network.perform_hop(1, print_progress=print_progress)
        second_network.perform_hop(1, print_progress=print_progress)
        hops += 1
        IPython.display.clear_output(wait=True)
        print(str(hops) + "/" + str(max_depth) + " hops completed.")
        connectors = [x for x in list(filter(first_network.graph.__contains__, second_network.graph.keys())) if x]
        if connectors:
            print("Found connection(s)!")
            return connectors
    print("No connections found.")
    return

def build_address_history(company_id):
    """Returns a list of dicts containing historic addresses for input company
    (company_id)."""
    company_info = api.get_company(company_id)
    if company_info:
        company_info_subset = {k:company_info[k] for k in ("date_of_creation","date_of_cessation","registered_office_address") if k in company_info}
        address_changes = api.get_address_changes(company_id)
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
                    entry["address"] = str(normalise_address(company_info_subset['registered_office_address']))
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
                        if 'old_address' in change['description_values']:
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
                    entry['address'] = normalise_address(entry['address'])
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
            entry['address'] = normalise_address(entry['address'])
            entry["lat"] = ""
            entry["lon"] = ""
            return [entry]
    else:
        return []

def normalise_address(address_dict):
    """Joins address key values into a single str."""
    address_list = []
    for key in ['premises','address_line_1', 'locality','postal_code', 'country']:
                if key in address_dict:
                    address_list.append(address_dict[key])
    address_string = ' '.join(address_list)
    return address_string
