# -*- coding: utf-8 -*-

import craigslist
import fixtures
import unittest

from BeautifulSoup import BeautifulSoup


class TestCraigslist(unittest.TestCase):

    def _expect_price(self, text, price):
        """
        Verify that `craigslist.get_price` can extract `price` from `text`.
        """
        parsed_price = craigslist.get_price(text)

        self.assertEqual(
            parsed_price, price,
            'Could not parse "%s". Expected %s - got "%s"' % (
                text, price, parsed_price))

    def _test_price_formatting(self, price):
        """
        Test `craigslist.get_price` by converting `price` into a variety of
        strings.
        """
        for v in (' $%s', ' $%s ', '$%s ', '$%s.00'):
            self._expect_price(v % price, float(price))

    def test_get_price(self):
        """
        Test that `get_price` can parse a variety of price strings.
        """
        self._test_price_formatting(50)
        self._test_price_formatting(20)
        self._test_price_formatting(100)
        self._test_price_formatting(1000)
        self._test_price_formatting(2000)
        self._test_price_formatting(100000)

    def test_extract_item_for_sale_no_price(self):
        """
        Verify that `craigslist.extract_item_for_sale` works with a mock
        Craigslist post title that lacks a price.
        """
        result = craigslist.get_posts_for_category('sss', fixtures.location,
                                                   fixtures.for_sale[0])

        self.assertEqual(result[0]['date'], 'Jun 7')
        self.assertEqual(result[0]['link'],
                         "http://portland.craigslist.org/clk/sys/3058025999.html")
        self.assertEqual(result[0]['desc'],
                         'i want to trade my laptop for a utility trailer')
        self.assertEqual(result[0]['location'], '(Kelso)')
        self.assertEqual(result[0]['category'], 'computers - by owner')
        self.assertFalse(result[0]['image'])
        self.assertFalse('price' in result[0])

    def test_extract_item_for_sale_with_price(self):
        """
        Verify that `craigslist.extract_item_for_sale` works with a mock
        Craigslist post title that has a price.
        """
        result = craigslist.get_posts_for_category('sss', fixtures.location,
                                                   fixtures.for_sale[1])

        self.assertEqual(result[0]['date'], 'Jun 7')
        self.assertEqual(result[0]['link'],
                         "http://portland.craigslist.org/mlt/sys/3058061021.html")
        self.assertEqual(result[0]['desc'],
                         'D525MWV Intel Atom 1.8Ghz MotherBoard')
        self.assertEqual(result[0]['location'], '(Ne Portland)')
        self.assertTrue(result[0]['image'])
        self.assertEqual(result[0]['category'], 'computers - by owner')
        self.assertEqual(result[0]['price'], 50.00)

    def test_extract_job(self):
        """
        Verify that `craigslist.extract_job` extracts a job from a mock
        Craigslist item.
        """
        result = craigslist.get_posts_for_category('jjj', fixtures.location,
                                                   fixtures.jobs[0])

        self.assertEqual(result[0]['date'], 'Jun  6')
        self.assertEqual(result[0]['link'],
                         "http://portland.craigslist.org/mlt/sof/3061734673.html")
        self.assertEqual(result[0]['desc'], 'Senior QA Engineer')
        self.assertEqual(result[0]['location'], '(Portland, OR)')
        self.assertFalse(result[0]['image'])
        self.assertEqual(result[0]['category'], 'software/QA/DBA/etc')

    def test_extract_housing_with_price_only(self):
        """
        Verify that `craigslist.extract_housing` extracts a housing item
        correctly when the item specifies only a price.
        """
        result = craigslist.get_posts_for_category('hhh', fixtures.location,
                                                   fixtures.housing[0])

        self.assertEqual(result[0]['date'], 'Jun  7')
        self.assertEqual(result[0]['link'],
                         "http://portland.craigslist.org/mlt/vac/3064470120.html")
        self.assertEqual(result[0]['location'], '(King)')
        self.assertEqual(result[0]['image'], True)
        self.assertEqual(result[0]['price'], 80)
        self.assertEqual(result[0]['desc'],
                         "$80 Stay at 'inner northeast charmer' by the night")
        self.assertEqual(result[0]['category'], 'vacation rentals')

    def test_extract_housing_with_rooms(self):
        """
        Verify that `craigslist.extract_housing` extracts a housing item
        correctly when the item specifies price and # of rooms.
        """
        result = craigslist.get_posts_for_category('hhh', fixtures.location,
                                                   fixtures.housing[1])

        self.assertEqual(result[0]['date'], 'Jun  7')
        self.assertEqual(result[0]['link'],
                         "http://portland.craigslist.org/mlt/apa/3064412526.html")
        self.assertEqual(result[0]['location'], '(1736 NE Killingsworth St.)')
        self.assertEqual(result[0]['image'], False)
        self.assertEqual(result[0]['price'], 800)
        self.assertEqual(result[0]['desc'],
                         "$800 / 1br - Great apartment near Alberta Arts")
        self.assertEqual(result[0]['bedrooms'], 1)
        self.assertEqual(result[0]['category'], 'apts/housing for rent')

    def test_extract_housing_with_rooms_and_sqft(self):
        """
        Verify that `craigslist.extract_housing` extracts a housing item
        correctly when the item specifies price, # of rooms and square feet.
        """
        result = craigslist.get_posts_for_category('hhh', fixtures.location,
                                                   fixtures.housing[2])

        self.assertEqual(result[0]['date'], 'Jun  7')
        self.assertEqual(result[0]['link'],
                         "http://portland.craigslist.org/wsc/reb/3063998127.html")
        self.assertEqual(result[0]['location'], '(Tigard)')
        self.assertEqual(result[0]['image'], True)
        self.assertEqual(result[0]['price'], 295000)
        self.assertEqual(result[0]['desc'],
                         u"$295000 / 4br - 2594ft\xb2 - Beautiful 4 "
                         "Bedroom With Hardwoods")
        self.assertEqual(result[0]['category'], 'real estate - by broker')

    def test_extract_housing_with_rooms_and_coords(self):
        """
        Verify that `craigslist.extract_housing` extracts a housing item
        correctly when the item specifies price, # of rooms and coordinates.
        """
        result = craigslist.get_posts_for_category('hhh', fixtures.location,
                                                   fixtures.housing[3])

        self.assertEqual(result[0]['date'], 'Dec 21')
        self.assertEqual(result[0]['link'],
                         "http://portland.craigslist.org/mlt/apa/3433985329.html")
        self.assertEqual(result[0]['location'], '(Dekum - Alberta)')
        self.assertEqual(result[0]['image'], True)
        self.assertEqual(result[0]['price'], 2300.0)
        self.assertEqual(result[0]['desc'],
                         u"Modern Furnished Home - Short term OK -Pets OK")
        self.assertEqual(result[0]['category'], 'apts/housing for rent')

    def test_bad_category_value(self):
        """
        Regression for badly-formed HTML in category field.
        """
        result = craigslist.get_posts_for_category('sss', fixtures.location,
                                                   fixtures.for_sale[2])
        self.assertEqual(result[0]['category'], '<<computers - by owner')


if __name__ == '__main__':
    unittest.main()
