"""
craigslist: A module for searching Craigslist.

Copyright (c) 2012 Andrew Brookins. All Rights Reserved.
"""

import re
import requests
from BeautifulSoup import BeautifulSoup


class ExtractorRegistry(object):
    """
    A wrapper around a dictionary of functions that each extract data from
    Craigslist posts made in a specific category, like housing or jobs.
    """
    extractors = {}

    def register(self, *args):
        """
        Register the decorated function as an extractor for any Craigslist
        category passed in *args Arguments should be Craigslist search
        categories like 'sss' or 'jjj'.

        e.g.,

            @extractors.register('jjj', 'hhh')
            def my_extractor(text):
                ...
        """
        def decorator(fn):
            for category in args:
                if category in self.extractors:
                    raise ValueError('Category is already registered: %s' % category)
                self.extractors[category] = fn

            def inner_function(*args, **kwargs):
                return fn(*args, **kwargs)
            return inner_function
        return decorator

    def get(self, category):
        """
        Get the extractor function for `category`.
        If no function is registered for `category`, return the default extractor.
        """
        fn = self.extractors.get(category, None)

        if fn is None:
            fn = self.extractors.get('default', None)

        return fn

    def deregister(self, category):
        """ Deregister the extractor function for `category`. """
        if category in self.extractors:
            del(self.extractors[category])


extractors = ExtractorRegistry()


def get_price(text):
    """
    Try to extract a price from `text`.

    # See: http://stackoverflow.com/questions/2150205/can-somebody-explain-a-money-regex-that-just-checks-if-the-value-matches-some-pa
    """
    money = re.compile('|'.join([
        # $.50, .50, $1.50, $.5, .5
        r'\$?(\d*\.\d{1,2})$',

        # $500, $5, 500, 5
        r'\$?(\d+)$',

        # $5.
        r'\$(\d+\.?)',
    ]))
    matches = money.search(text)
    price = matches and matches.group(0) or None

    if price:
        return float(price[1:])


@extractors.register('default', 'sss')
def extract_item_for_sale(item):
    """ Extract a Craigslist item for sale. """
    result = {
        'date': item.contents[1].text.replace('-', '').strip(),
        'link': item.contents[2].get('href'),
        'desc': item.contents[2].text.strip(),
        'location': item.contents[5].text.strip(),
        'image': item.contents[6].text != '',
    }

    # TODO: Category markup is occasionally bad. We should probably wrap
    # all references to `item.contents` indexes in a wrapper that tests for
    # `IndexError`.
    try:
        result['category'] = item.contents[7].text
    except IndexError:
        result['category'] = ''

    # If this tag has text in it, the item has an image.
    # This value is provided by Craigslist and need not be strip

    price = get_price(item.contents[4].text)

    if price:
        result['price'] = price

    return result


@extractors.register('jjj', 'ggg', 'bbb')
def extract_job(item):
    """ Extra a Craigslist job posting. """
    result = {
        'date': item.contents[0].text.replace('-', '').strip(),
        'link': item.contents[1].get('href'),
        'desc': item.contents[1].text, 'location': item.contents[2].text,
        'image': item.contents[3].text != '',
        'category': item.contents[4].text
    }

    category = item.find('small')

    if category:
        result['category'] = category.text

    return result


@extractors.register('hhh')
def extract_housing(item):
    """ Extract a Craigslist housing unit for sale or rental. """
    result = {'desc': item.contents[1].text.strip()}
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


def get_posts_for_category(category, location, html):
    """
    Get Craigslist all posts for the category `category`.

    Extract data from each post using the registered extractor and return a
    list of dictionaries containing the extracted data.

    If there are additional pages, recursively call `get_posts_for_category` to
    find items in the next page of the search.
    """
    items = []
    content = get_soup(html).findAll('blockquote')[1]
    extractor = extractors.get(category)

    for el in content.findAll('p'):
        # Filter out newlines and item separator spans.
        el.contents = filter(lambda x: x != u'\n' and x.text != u'-', el.contents)
        items.append(extractor(el))

    next_page_text = content.find('b', text='Next >>')

    if next_page_text:
        url = next_page_text.parent.parent.get('href')
        items += get_posts_for_category(category, location, requests.get(url).text)

    return items


# Perform an all-text search.
SEARCH_ALL = 'A'

# Search only titles.
SEARCH_TITLES = 'T'


def search(location, category, query, search_type=SEARCH_ALL):
    """
    Search Craigslist location `location` (a Craigslist URL like
    http://portland.craigslist.org) for posts in `category` matching `query`.

    `search_type` indicates whether this is an all-text search ('A') or a title
    search ('T').
    """
    valid_search_types = [SEARCH_ALL, SEARCH_TITLES]

    if not search_type in valid_search_types:
        raise ValueError(
            'Search type must be one of: %s.' % ', '.join(valid_search_types))

    search_url = '%ssearch/%s?query=%s&srchType=%s' % (
        location, category, query, search_type)

    return get_posts_for_category(category, location,
                                  requests.get(search_url).text)
