"""
craigslist: A module for searching Craigslist.

Copyright (c) 2012 Andrew Brookins. All Rights Reserved.
"""

import re
import requests
import urllib
from BeautifulSoup import BeautifulSoup


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


def get_item_dict(item):
    """
    Get generic Craigslist values for an item.

    Many features of an item, like the date, use the same span classes across
    categories of the site.
    """
    date = item.find('span', 'itemdate')
    link = item.find('a')
    pix = item.find('span', 'p')

    result = {
        'date': date.text.strip(),
        'link': link.get('href'),
        'desc': link.text.strip(),
        'location': item.find('span', 'itempn').text.strip(),
        'image': True if pix and pix.text else False
    }

    cat = item.find('span', 'itemcg')
    if cat:
        result['category'] = cat.text

    return result


def extract_item_for_sale(item, filters=None):
    """ Extract a Craigslist item for sale. """
    result = get_item_dict(item)
    price = item.find('span', 'itempp')
    price = get_price(price.text) if price else None

    if price:
        result['price'] = price

    return result


def extract_job(item, filters=None):
    """ Extra a Craigslist job posting. """
    results = get_item_dict(item)

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


def extract_housing(item, filters=None):
    """ Extract a Craigslist housing unit for sale or rental. """
    result = get_item_dict(item)
    details = item.find('span', 'itemph')
    details = details.text if details else item.find('a').text

    price = get_price(details)
    if price:
        result['price'] = price

    # Isolate the price and details (bedrooms, square feet) from a title like:
    # '$1425 / 3br - 1492ft - Beautiful Sherwood Home Could Be Yours, Move in March 1st'
    if '/' in details:
        parts = details.split('/')
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

    # Apply any filters. TODO: Make this elegant.
    min_price = filters.get('min_price', None)
    max_price = filters.get('max_price', None)
    min_rooms = filters.get('min_rooms', None)
    max_rooms = filters.get('max_rooms', None)
    bedrooms = result.get('bedrooms', None)

    if min_price and price and price <= min_price:
        return
    if max_price and price and price >= max_price:
        return
    if min_rooms and bedrooms and bedrooms <= min_rooms:
        return
    if max_rooms and bedrooms and bedrooms >= max_rooms:
        return

    return result


def get_soup(text):
    return BeautifulSoup(text, convertEntities=BeautifulSoup.HTML_ENTITIES)


extractors = {
    ('default', 'sss'): extract_item_for_sale,
    ('jjj', 'ggg', 'bbb'): extract_job,
    ('hhh',): extract_housing
}


def get_extractor(category):
    for categories, fn in extractors.items():
        if category in categories:
            return fn


def get_posts_for_category(category, location, html, filters=None):
    """
    Get Craigslist all posts for the category `category`.

    Extract data from each post using the registered extractor and return a
    list of dictionaries containing the extracted data.

    If there are additional pages, recursively call `get_posts_for_category` to
    find items in the next page of the search.
    """
    items = []
    content = get_soup(html).findAll('blockquote')[1]
    extractor = get_extractor(category)

    for el in content.findAll('p'):
        # Filter out newlines and item separator spans.
        el.contents = filter(lambda x: x != u'\n' and x.text != u'-', el.contents)
        item = extractor(el, filters)
        if item:
            items.append(item)

    next_page_text = content.find('b', text='Next >>')

    if next_page_text:
        url = next_page_text.parent.parent.get('href')
        items += get_posts_for_category(category, location,
                                        requests.get(url).text, filters)

    return items


# Perform an all-text search.
SEARCH_ALL = 'A'

# Search only titles.
SEARCH_TITLES = 'T'


def search(location, category, query, search_type=SEARCH_ALL, filters=None):
    """
    Search Craigslist location `location` (a Craigslist URL like
    http://portland.craigslist.org) for posts in `category` matching `query`.

    `search_type` indicates whether this is an all-text search ('A') or a title
    search ('T').
    """
    valid_search_types = [SEARCH_ALL, SEARCH_TITLES]
    query = urllib.quote(query)

    if not search_type in valid_search_types:
        raise ValueError(
            'Search type must be one of: %s.' % ', '.join(valid_search_types))

    search_url = '%ssearch/%s?query=%s&srchType=%s' % (
        location, category, query, search_type)

    html = requests.get(search_url).text

    return get_posts_for_category(category, location, html, filters)
