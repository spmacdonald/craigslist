import craigslist
import unittest


class TestCraigslist(unittest.TestCase):

    def test_register_extractor(self):
        """ Verify that we can register and retreive an extractor function. """

        @craigslist.register_extractor('test')
        def test_fn():
            """ A mock extractor. """
            return "Testing"

        fn = craigslist.get_extractor('test')

        self.assertEqual(fn(), test_fn())


if __name__ == '__main__':
    unittest.main()
