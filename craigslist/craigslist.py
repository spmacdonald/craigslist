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
    Arguments should be Craigslist search categories like 'sss' or 'jjj'.

    e.g., 

        @register_extractor('jjj', 'hhh')
        def my_extractor(text):
            ...
    """
    def decorator(fn):
        for category in args:
            _extractor_registry[category] = fn
        def inner_function(*args, **kwargs):
            return fn(*args, **kwargs)
        return inner_function
    return decorator


def get_extractor(category):
    """ 
    Get the extractor function for `category`.
    If no function is registered for `category`, return the default extractor.    
    """
    fn = _extractor_registry.get(category, None)

    if fn is None:
        fn = _extractor_registry.get('default', None)

    return fn


def get_price(text):
    """
    Try to extract a price from `text`.

    # See: http://stackoverflow.com/questions/2150205/can-somebody-explain-a-money-regex-that-just-checks-if-the-value-matches-some-pa
    """
    money = re.compile('|'.join([
      r'\$?(\d*\.\d{1,2})$',  # e.g., $.50, .50, $1.50, $.5, .5
      r'\$?(\d+)$',           # e.g., $500, $5, 500, 5
      r'\$(\d+\.?)',         # e.g., $5.
    ]))
    matches = money.search(text)
    price = matches and matches.group(0) or None
    
    if price:
        return float(price[1:])


@register_extractor('default', 'sss')
def extract_item_for_sale(item):
    """ Extract a Craigslist item for sale. """
    result = {}
    result['date'] = item.contents[1].text.replace('-', '').strip()
    result['link'] = item.contents[2].get('href')
    result['desc'] = item.contents[2].text.strip()
    result['location'] = item.contents[5].text.strip()
    # If this tag has text in it, the item has an image.
    result['image'] = item.contents[6].text != ''
    # This value is provided by Craigslist and need not be stripped.
    result['category'] = item.contents[7].text

    price = get_price(item.contents[4].text)

    if price:
        result['price'] = price

    return result


@register_extractor('jjj', 'ggg', 'bbb')
def extract_job(item):
    """ Extra a Craigslist job posting. """
    result = {}
    result['date'] = item.contents[0].text.replace('-', '').strip()
    result['link'] = item.contents[1].get('href')
    result['desc'] = item.contents[1].text
    result['location'] = item.contents[2].text
    result['image'] = item.contents[3].text != ''
    result['category'] = item.contents[4].text

    category = item.find('small')

    if category:
        result['category'] = category.text

    return result 


@register_extractor('hhh')
def extract_housing(item):
    """ Extract a Craigslist housing unit for sale or rental. """
    result = {}

    result['desc'] = item.contents[1].text.strip()
    result['price'] = get_price(result['desc'])

    # Isolate the price and details (bedrooms, square feet) from a title like:
    # '$1425 / 3br - 1492ft - Beautiful Sherwood Home Could Be Yours, Move in March 1st'
    if '/' in item.contents[1].text:
        parts = item.contents[1].text.split('/')
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

    result['link'] = item.contents[1].get('href')
    result['date'] = item.contents[0].text.replace('-', '').strip()
    result['location'] = item.contents[2].text.strip()
    result['image'] = item.contents[3].text != ''

    small = item.find('small')
    if small:
        result['category'] = small.text

    return result


def get_soup(text):
    return BeautifulSoup(text, convertEntities=BeautifulSoup.HTML_ENTITIES)


def get_items_for_category(category, text):
    items = []
    content = get_soup(text).findAll('blockquote')[1]
    extractor = get_extractor(category)

    for el in content.findAll('p'):
        # Filter out newlines and item separator spans.
        el.contents = filter(lambda x: x != u'\n' and x.text != u'-', el.contents)
        items.append(extractor(el))

    return items


# Craigslist search types. These values indicate whether to search all text in
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
    valid_search_types = [SEARCH_ALL, SEARCH_TITLES]

    if not search_type in valid_search_types:
        raise ValueError(
            'Search type must be one of: %s.' % ', '.join(valid_search_types))

    # 'srchType=A': Default to an "all-text" search rather than just titles.
    search_url = '%ssearch/%s?query=%s&srchType=A' % (
        location, category, query)

    return get_items_for_category(category, requests.get(search_url).text)
