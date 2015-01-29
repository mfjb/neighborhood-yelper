import argparse
import urllib2
import oauth2
import json
import pandas as pd
import time
import sys

API_HOST = 'api.yelp.com'
DEFAULT_TERM = ''
DEFAULT_TERM_FILE = 'default.terms'
DEFAULT_LOCATION = 'Woodstock Portland OR'
DEFAULT_RADIUS_FILTER = 3000
DEFAULT_OFFSET = 0
DEFAULT_SORT = 0
SEARCH_LIMIT = 20
SEARCH_PATH = '/v2/search/'

CONSUMER_KEY = 'TG6NB-2hpPxToVaqWjqbWQ'
CONSUMER_SECRET = 'W1LscuZh4oBAaTmWdIECHx68hyg'
TOKEN = 'wIIlKrVdw8xP-lLQf9ziIgJ6ZP8vs_H7'
TOKEN_SECRET = 'GfNCLLHhtj9j9iKrvKvIEJpaKfI'


def request(host, path, url_params=None):
    """Prepares OAuth authentication and sends the request to the API.

    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        url_params (dict): An optional set of query parameters in the request.

    Returns:
        dict: The JSON response from the request.

    Raises:
        urllib2.HTTPError: An error occurs from the HTTP request.
    """
    url_params = url_params or {}
    url = 'http://{0}{1}?'.format(host, path)
    
    consumer = oauth2.Consumer(CONSUMER_KEY, CONSUMER_SECRET)
    oauth_request = oauth2.Request(method="GET", url=url, parameters=url_params)
 
    oauth_request.update(
        {
            'oauth_nonce': oauth2.generate_nonce(),
            'oauth_timestamp': oauth2.generate_timestamp(),
            'oauth_token': TOKEN,
            'oauth_consumer_key': CONSUMER_KEY
        }
    )
    token = oauth2.Token(TOKEN, TOKEN_SECRET)
    oauth_request.sign_request(oauth2.SignatureMethod_HMAC_SHA1(), consumer, token)
    signed_url = oauth_request.to_url()
    
    print 'Querying {0} ...'.format(url)

    conn = urllib2.urlopen(signed_url, None)
    try:
        response = json.loads(conn.read())
    finally:
        conn.close()

    return response

def search(term, location, radius_filter, offset, sort):
    """Query the Search API by a search term and location.

    Args:
        location (str): The search location passed to the API.
        radius_filter (int): The radius filter passed to the API.

    Returns:
        dict: The JSON response from the request.
    """
    
    url_params = {
        'term': term.replace(' ', '+'),
        'location': location.replace(' ', '+'),
        'radius_filter': radius_filter,
        'limit': SEARCH_LIMIT,
        'offset': offset,
        'sort': sort
    }
    return request(API_HOST, SEARCH_PATH, url_params=url_params)

def convert_response_to_dataframe(response):
    b_name_dict, b_address_dict, b_city_dict, b_state_dict, b_postal_code_dict, b_country_dict, b_phone_dict = {}, {}, {}, {}, {}, {}, {}
 
    for business in response['businesses']:
        if business['is_closed'] is False:
            b_id = business['id']
            b_name_dict[b_id] = business['name']

            if 'address' in business['location']:
                b_address_dict[b_id] = ', '.join(business['location']['address'])
            else:
                b_address_dict[b_id] = None

            if 'city' in business['location']:
                b_city_dict[b_id] = business['location']['city']
            else:
                b_city_dict[b_id] = None

            b_state_dict[b_id] = business['location']['state_code']

            if 'postal_code' in business['location']:
                b_postal_code_dict[b_id] = business['location']['postal_code']
            else:
                b_postal_code_dict[b_id] = None

            b_country_dict[b_id] = business['location']['country_code']

            if 'display_phone' in business:
                b_phone_dict[b_id] = business['display_phone']
            else:
                b_phone_dict[b_id] = None

    business_df = pd.DataFrame(
        {
            'Business Name': b_name_dict, 
            'Address': b_address_dict, 
            'City': b_city_dict,
            'State': b_state_dict,
            'Postal Code': b_postal_code_dict,
            'Country': b_country_dict,
            'Phone Number': b_phone_dict
        }
    )
    return business_df

def load_query_terms(term_file):
    with open(term_file, 'r') as f:
        query_terms = []
        for line in f:
            query_terms.append(line.strip('\n'))
    return query_terms

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-q', '--term', dest='term', default=DEFAULT_TERM, type=str, help='Search term (default: %(default)s)')
    parser.add_argument('-l', '--location', dest='location', default=DEFAULT_LOCATION, type=str, help='Search location (default: %(default)s)')
    parser.add_argument('-r', '--radius_filter', dest='radius_filter', default=DEFAULT_RADIUS_FILTER, type=int, help='Search radius filter (default: %(default)s)')
    parser.add_argument('-s', '--sort', dest='sort', default=DEFAULT_SORT, type=int, help='Sort value (default: %(default)s)')
    parser.add_argument('-o', '--offset', dest='offset', default=DEFAULT_OFFSET, type=int, help='Offset value (default: %(default)s)')
    parser.add_argument('-Q', '--term_file', dest='term_file', default=DEFAULT_TERM_FILE, type=str, help='Query term filename (default: %(default)s)')
    input_values = parser.parse_args()

    try:
        if input_values.term:
            all_responses = search(input_values.term, input_values.location, input_values.radius_filter, input_values.offset, input_values.sort)
            business_df = convert_response_to_dataframe(all_responses)
        else:
            terms = load_query_terms(input_values.term_file)
            all_responses = []
            business_df = pd.DataFrame()
            for term in terms:
                response = search(term, input_values.location, input_values.radius_filter, input_values.offset, input_values.sort)
                all_responses.append(response)
                business_df_increment = convert_response_to_dataframe(response)
                business_df = business_df.append(business_df_increment)

        timestamp = str(int(time.time()))        
        json_filename = 'json/{}_{}_sort{}_offset{}_{}.json'.format(input_values.location, input_values.term, input_values.sort, input_values.offset, timestamp)

        with open(json_filename, 'w') as f:
            f.write(json.dumps(all_responses, indent=4, separators=(',', ': ')))

        df_filename = 'processed_data/{}_{}_sort{}_offset{}_{}.csv'.format(input_values.location, input_values.term, input_values.sort, input_values.offset, timestamp)
        business_df.to_csv(df_filename, index_label='Yelp ID', encoding='utf-8')

    except urllib2.HTTPError as error:
        sys.exit('Encountered HTTP error {0}. Abort program.'.format(error.code))


if __name__=='__main__':
    main()
