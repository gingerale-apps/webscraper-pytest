from os import path
from zipfile import ZipFile
from pytest import fixture, mark, yield_fixture, raises
from mock import Mock, patch
from json import load

from errors import NoQuotes, UnsupportedQuery
import webscraper.scraper as scraper


@fixture
def query_dict():
    def _query_dict(**kwargs):
        base = {
            'from_place': 'KTM',
            'to_place': 'BIR',
            'flight_date': '2019-12-05',
            'return_date': 'null',
            'nationality': 'NP',
            'trip_type': 'O',
            'adults': 1,
            'children': 0,
            'infants': 0
            }
        base.update(kwargs)
        return base
    return _query_dict


@fixture
def test_params():
    return {
        'strTripType': 'O',
        'intChild': 0,
        'strFlightDate': '05-Dec-2019',
        'strReturnDate': 'null',
        'strNationality': 'NP',
        'intAdult': 1,
        'strSectorTo': 'BIR',
        'strSectorFrom': 'KTM'
    }


@fixture
def test_quote():
    return {
        'dep_time': u'2019-12-05 07:45',
        'marketing_carrier': u'U4',
        'from_place': u'KTM',
        'to_place': u'BIR',
        'arr_time': u'2019-12-05 08:25',
        'currency': u'NPR',
        'child_price': {'base': u'3404', 'tax': u'200', 'surcharge': u'2270'},
        'marketing_segment_code': u'703',
        'adult_price': {'base': u'5080', 'tax': u'200', 'surcharge': u'2270'}
    }


@yield_fixture(scope='module')
def transport_response():
    zip_file = path.join(path.dirname(__file__), 'data', 'transport.zip')
    with ZipFile(zip_file, 'r') as f:
        yield f


@mark.parametrize('adults,children,infants,return_date,trip_type,expected', [
        (1, 1, 0, 'null', 'O', True),
        (8, 0, 0, 'null', 'O', False),
        (7, 1, 0, 'null', 'O', False),
        (2, 1, 1, 'null', 'O', False),
        (1, 1, 0, '2019-12-03', 'O', False),
        (1, 1, 0, 'null', 'R', False),
        (7, 1, 1, '2019-12-03', 'R', False)
])
def test_is_valid(query_dict, adults, children, infants, return_date, trip_type, expected):
    query_test = query_dict(adults=adults, children=children, infants=infants, return_date=return_date, trip_type=trip_type)
    assert scraper.is_valid(query_test) == expected


def test_request_params(query_dict, test_params):
    params = scraper.request_params(query_dict())
    assert params == test_params


def test_extract_quotes(transport_response, query_dict, test_quote):
    json_response = load(transport_response.open('transport/ow_response.json'))
    quotes = scraper.extract_quotes(query_dict(), json_response)
    assert quotes[0] == test_quote


@patch('webscraper.scraper.is_valid', Mock(return_value=False))
def test_scraper_raise_wrong_search_parameters(query_dict):
    with raises(UnsupportedQuery, match='Search parameters validation failed'):
        scraper.scraper(query_dict())


@patch('webscraper.scraper.is_valid', Mock(return_value=True))
@patch('webscraper.scraper.requests', Mock(post=Mock(return_value=Mock(text=Mock(return_value=" ")))))
@patch('webscraper.scraper.extract_quotes', Mock(return_value=[]))
def test_scraper_raise_no_quotes(query_dict):
    with raises(NoQuotes, match='No fares for search parameters'):
        scraper.scraper(query_dict())
