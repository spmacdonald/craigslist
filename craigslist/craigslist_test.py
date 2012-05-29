import craigslist
import fixtures
import unittest

from BeautifulSoup import BeautifulSoup


class TestCraigslist(unittest.TestCase):
    
    def test_register_extractor(self):
        """ Verify that we can register and retreive an extractor function. """

        @craigslist.register_extractor('test_category')
        def test_fn():
            """ A mock extractor. """
            return "Testing"

        fn = craigslist.get_extractor('test_category')

        self.assertEqual(fn(), test_fn())

    def test_get_default_extractor(self):
        """
        Verify that requesting an extractor for a category for which we don't
        have an extractor yields the default extractor.
        """

        @craigslist.register_extractor('default')
        def test_fn():
            """ A mock extractor. """
            return "Testing"

        fn = craigslist.get_extractor('nonexistent_category')

        self.assertEqual(fn(), test_fn())

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
        result = craigslist.get_items_for_category('sss', fixtures.for_sale[0])
        self.assertEqual(
            result[0]['link'],
            'http://portland.craigslist.org/mlt/bks/3032571105.html')

        self.assertEqual(
            result[0]['desc'], 'Ball Python Book')

        self.assertEqual(
            result[0]['location'], '(SE Portland)')

        self.assertFalse('price' in result[0])

    def test_extract_item_for_sale_with_price(self):
        """
        Verify that `craigslist.extract_item_for_sale` works with a mock
        Craigslist post title that has a price.
        """
        result = craigslist.get_items_for_category('sss', fixtures.for_sale[1])

        self.assertEqual(
            result[0]['link'],
            "http://portland.craigslist.org/mlt/for/3038377527.html")

        self.assertEqual(
            result[0]['desc'], 'Python Aquarium Cleaner With Extension')

        self.assertEqual(
            result[0]['location'], '(SE Portland)')

        self.assertEqual(
            result[0]['price'], 20.00)



if __name__ == '__main__':
    unittest.main()
