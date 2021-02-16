"""
Webscraper for oneway flights on https://www.buddhaair.com.
Python 3.7
"""

from datetime import datetime
import requests
from errors import NoQuotes, UnsupportedQuery

# search parameters
query_oneway = {
    'from_place': 'KTM',
    'to_place': 'BIR',
    'flight_date': '2021-05-12',
    'return_date': 'null',
    'nationality': 'NP',
    'trip_type': 'O',
    'adults': 1,
    'children': 0,
    'infants': 0
}


def scraper(query):
    """Main function, send request, get fares and return list with quotes.

    :param query: search parameters
    :type query: dict

    :raises UnsupportedQuery: if search parameters are not valid
    :raises NoQuotes: if there are no fares for search parameters

    :rtype: list of dicts
    :return: fares, e.g. [{'adult_price': {'base': '5140', 'surcharge': '1560', 'tax': '255'},
                     'child_price': {'base': '3444', 'surcharge': '1560', 'tax': '255'},
                     'currency': 'NPR', 'marketing_carrier': 'U4', 'marketing_segment_code': '701',
                     'from_place': 'KTM', 'to_place': 'BIR', 'dep_time': '2020-11-01 08:30',
                     'arr_time': '2020-11-01 09:10'}, {...}, ...]
    """
    if not is_valid(query):
        raise UnsupportedQuery('Search parameters validation failed')

    response = requests.post('https://www.buddhaair.com/soap/FlightAvailability', data=request_params(query)).json()
    quotes = extract_quotes(query, response)

    if not quotes:
        raise NoQuotes('No fares for search parameters')

    return quotes


def is_valid(query):
    """Check search parameters.

    :param query: search parameters
    :type query: dict

    :rtype: bool
    :return: True|False
    """
    return all((query['adults'] + query['children'] < 8,
                query['infants'] == 0,
                query['return_date'] == 'null',
                query['trip_type'] == 'O'))


def request_params(query):
    """Set the values from search parameters into request parameters.

    :param query: search parameters
    :type query: dict

    :rtype: dict
    :return: request parameters
    """
    date_out = datetime.strptime(query['flight_date'], '%Y-%m-%d')
    return {'strSectorFrom': query['from_place'],
            'strSectorTo': query['to_place'],
            'strFlightDate': date_out.strftime('%d-%b-%Y'),
            'strReturnDate': query['return_date'],
            'strNationality': query['nationality'],
            'strTripType': query['trip_type'],
            'intAdult': query['adults'],
            'intChild': query['children']
            }


def extract_quotes(query, response):
    """Extract quotes from response.

    :param query: search parameters
    :type query: dict

    :param response: response data
    :type response: dict

    :rtype: list of dicts
    :return: fares
    """
    quotes = []
    if not response['data']['outbound']['flightsector']:
        return quotes

    out_flights = response['data']['outbound']['flightsector']['flightdetail']

    for flight in out_flights:
        prices = flight['airfare']['faredetail']
        quotes.append({
            'adult_price': {'base': prices['fare'], 'surcharge': prices['surcharge'],
                            'tax': prices['taxbreakup']['taxdetail']['taxamount']},
            'child_price': {'base': prices['childfare'], 'surcharge': prices['surcharge'],
                            'tax': prices['taxbreakup']['taxdetail']['taxamount']},
            'currency': prices['currency'],
            'marketing_carrier': flight['flightno'].split(' ')[0],
            'marketing_segment_code': flight['flightno'].split(' ')[1],
            'from_place': flight['sectorpair'].split('-')[0],
            'to_place': flight['sectorpair'].split('-')[1],
            'dep_time': f"{query['flight_date']} {flight['departuretime']}",
            'arr_time': f"{query['flight_date']} {flight['arrivaltime']}"
        })

    return quotes


if __name__ == "__main__":
    print(scraper(query_oneway))
