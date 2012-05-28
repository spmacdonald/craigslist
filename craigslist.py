"""
craigslist: A module for searching Craigslist.

Copyright (c) 2012 Andrew Brookins. All Rights Reserved.
"""

import re
import requests
from BeautifulSoup import BeautifulSoup


# a dictionary of extractor functions, each mapped to a Craigslist search
# category key like 'jjj' or 'hhh'
_extractor_registry = {}


def register_extractor(*args):
    """
    Register `fn` as an extractor for any Craigslist category passed in *args
    Arguments should be Craiglist search categories like 'sss' or 'jjj'.

    e.g., 

        @register_extracotr('jjj', 'hhh')
        def my_extractor(text):
            ...
    """
    def decorator(fn):
        for category in args:
            _extractor_registry[category] = fn
        def inner_function(*args, **kwargs):
            fn(*args, **kwargs)
        return inner_function
    return decorator


def get_extractor(category):
    """ 
    Get the extractor function for `category`.
    If no function is registered for `category`, return the default extractor.    
    """
    fn = _extractor_registry.get(category, None)

    if fn == None:
        fn = _extractor_registry.get('default', None)

    return fn


def get_price(text):
    """
    Try to extract a price from `text`.
    """
    money = re.compile('^\$(\d{1,3}(\,\d{3})*|(\d+))(\.\d{2})?$')
    matches = money.match(text.strip())
    price = matches and matches.group(0) or None
    
    if price:
        return float(price[1:])


@register_extractor('default', 'sss')
def extract_item_for_sale(item):
    """ Extract a Craigslist item for sale. """
    result = {}
    result['image'] = item.contents[1].get('id')
    result['date'] = item.contents[2].strip().rstrip('- ')
    result['link'] = item.contents[3].get('href')
    result['desc'] = item.contents[3].text
    result['location'] = item.contents[5].string

    price = get_price(item.contents[4])

    if price:
        result['price'] = price

    return result


@register_extractor('jjj', 'ggg', 'bbb')
def extract_job(item):
    """ Extra a Craigslist job posting. """
    result = {}
    result['date'] = item.contents[0].strip().rstrip('- ')
    result['link'] = item.contents[1].get('href')
    result['desc'] = item.contents[1].text
    result['location'] = item.contents[3].text

    category = item.find('small')

    if category:
        result['category'] = category.text

    return result 


@register_extractor('hhh')
def extract_housing(item):
    """ Extract a Craigslist housing unit for sale or rental. """
    result = {}

    # Isolate the price and details (bedrooms, square feet) from a title like:
    # '$1425 / 3br - 1492ft - Beautiful Sherwood Home Could Be Yours, Move in March 1st'
    if '/' in item.contents[1].text:
        parts = item.contents[1].text.split('/')
        price = get_price(parts[0])

        if price:
            result['price'] = price

        rental_details = parts[1].split('-')

        for detail in rental_details:
            detail = detail.strip()

            if 'ft' in detail:
                result['sqft'] = detail
            elif 'br' in detail:
                # Split the number portion of strings like '1br'
                bedrooms = detail.lower().split('br')[0]

                try:
                    bedrooms = int(bedrooms)
                except ValueError:
                    bedrooms = 0

                result['bedrooms'] = bedrooms
            else:
                result['desc'] = detail
    else:
        result['desc'] = item.contents[1].text.strip()

    result['link'] = item.contents[1].get('href')
    result['date'] = item.contents[0].strip().rstrip('- ')
    result['location'] = item.contents[3].text

    small = item.find('small')
    if small:
        result['type'] = small.text

    return result


def extract_results(raw_results, category):
    """
    Extract data about a single Craiglist search result from HTML into a dict,
    using BeautifulSoup.
    """
    results = []

    for el in raw_results.nextGenerator():
        if not hasattr(el, 'name') or el.name == 'h4':
            continue

        if el.name == 'p':
            extractor = get_extractor(category)
            results.append(extractor(el))

    return results


# Craigslist search types. These values indicate whether to seach all text in
# posts or just titles. The query arg for this value is 'srchType'.
SEARCH_ALL = 'A'
SEARCH_TITLES = 'T'


def search(location, category, query, search_type=SEARCH_ALL):
    """
    Search each Craigslist location `location` (iterable) for passing
    `category` to Craigslist as the search category and `query` as the user's
    search. 

    `search_type` indicates whether this is an all-text search ('A') or just a
    title search ('T').
    """
    results = []
    valid_search_types = [SEARCH_ALL, SEARCH_TITLES]

    if not search_type in valid_search_types:
        raise ValueError(
            'Search type must be one of: %s.' % ', '.join(valid_search_types))

    # 'srchType=A': Default to an "all-text" search rather than just titles.
    search_url = '%ssearch/%s?query=%s&srchType=A' % (
        location, category, query)

    content = BeautifulSoup(
        requests.get(search_url).text,
        convertEntities=BeautifulSoup.HTML_ENTITIES)

    for raw_results in content.findAll('h4'):
        results = results + extract_results(raw_results, category)

    return results

