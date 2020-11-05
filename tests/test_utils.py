import unittest
from datetime import datetime

from photomatools.utils import auto_datetime


class TestUtils(unittest.TestCase):
    def test_datetime(self):

        self.assertEqual(
            auto_datetime("2020-02-24 17:05:01"),
            datetime(2020, 2, 24, 17, 5, 1),
        )
        self.assertEqual(
            auto_datetime("2020-02-24 17:05:01.123"),
            datetime(2020, 2, 24, 17, 5, 1, 123000),
        )
        self.assertEqual(
            auto_datetime("2020:02:24 17:05:01"),
            datetime(2020, 2, 24, 17, 5, 1),
        )
        self.assertEqual(
            auto_datetime("2020:02:24 17:05:01.123"),
            datetime(2020, 2, 24, 17, 5, 1, 123000),
        )